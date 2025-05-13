# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _get_result(self):
        for aml in self:
            aml.result = aml.debit - aml.credit

    followup_line_id = fields.Many2one('payment.followup.line', 'Follow-up Level', ondelete='set null')
    # restrict deletion of the followup line
    followup_date = fields.Date('Latest Follow-up')
    result = fields.Float(compute='_get_result', string="Result")
    # 'balance' field is not the same


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    amount_payment = fields.Monetary(compute='_payment_total', string="Total payment")

    payment_responsible_id = fields.Many2one('res.users', ondelete='set null', string='Follow-up Responsible', track_visibility="onchange", copy=False)
    payment_note = fields.Text('Customer Payment Promise', help="Payment Note", track_visibility="onchange", copy=False)
    payment_next_action = fields.Text('Next Action', copy=False, track_visibility="onchange")
    payment_next_action_date = fields.Date('Next Action Date', copy=False,)
    unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id')

    latest_followup_date = fields.Date(compute='_get_latest', string="Latest Follow-up Date")
    latest_followup_level_id = fields.Many2one('payment.followup.line', compute='_get_latest', string="Latest Follow-up Level", help="The maximum follow-up level")
    latest_followup_level_id_without_lit = fields.Many2one('payment.followup.line', compute='_get_latest', store=True, string="Latest Follow-up Level without litigation")

    payment_amount_due = fields.Monetary(compute='_get_amounts_and_date', string="Amount Due", search='_payment_due_search')
    payment_amount_overdue = fields.Monetary(compute='_get_amounts_and_date', string="Amount Overdue", search='_payment_overdue_search')
    payment_earliest_due_date = fields.Date(compute='_get_amounts_and_date', string="Worst Due Date", search='_payment_earliest_date_search')

    bypass_auto_followup = fields.Boolean(string="ByPass Auto Payment Follow-up Email", default=False, help='tick to bypass the auto payment follow up email for this customer')
    last_payment_amount = fields.Monetary(string="Last Payment Amount", compute="get_last_payment")
    last_payment_date = fields.Date(string="Last Payment Date", compute="get_last_payment")
    last_sent_date = fields.Datetime(string="Last Sent Date", track_visibility='always')
    last_sent_by = fields.Many2one('res.users', string="Last Sent by", track_visibility='always')
    last_followup_level_id = fields.Many2one('payment.followup.line', string="Last Followup Level", track_visibility='always')
    last_action_type = fields.Selection([('manual', 'Manual'), ('automatic', ' Automatic')], string="Action Type", track_visibility='always')
    last_send_type = fields.Selection([('soa', "SOA"), ('overdue_invoices', 'Overdue Invoices'), ('soa_overdue', 'SOA + Overdue Invoices'), ('open_invoice', 'Open Invoices'), ('soa_open', 'SOA + Open Invoices')],
                                      string="Send Type", track_visibility='always')
    followup_histry_ids = fields.One2many('partner.payment.followup', 'partner_id', string="Payment FolloUp History")
    next_followup_date = fields.Date('Next Followup Date')
    default_payment_email = fields.Boolean(string="Default Payment Email", default=False,
                                           help='Is Default Recipient in the Payment Follow up Email?')
    followup_emails = fields.Char(string='Follow up Emails', track_visibility='always', compute='_get_followup_emails')
    # TS fix bug - remove state
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=_default_currency, track_visibility='always')
    reset_date = fields.Date(string="Followup Reset Date")
    outstanding_invoices_amount = fields.Monetary(string="Outstanding Invoices", compute="get_total_outstanding")

    @api.multi
    def get_total_outstanding(self):
        for res in self:
            qry = """select sum(residual) from account_invoice where partner_id=%d and type='out_invoice'and state='open'""" % res.id
            self.env.cr.execute(qry)
            amount_totals = self.env.cr.dictfetchone()
            res.outstanding_invoices_amount = amount_totals.get('sum')

    @api.multi
    def reset_payment_followup_level(self):
        self._cr.execute("update account_move_line set followup_line_id=NULL, followup_date=NULL where partner_id = %s and followup_line_id != NULL and followup_date != NULL" % self.id)
        self._cr.execute("update res_partner set last_sent_date=NULL, last_sent_by=NULL, last_followup_level_id=NULL,last_action_type=NULL, last_send_type=NULL where id = %s" % self.id)
        self.reset_date = fields.Date.today()

    @api.multi
    def get_last_payment(self):
        for res in self:
            payment_id = self.env['account.payment'].search([('partner_id', '=', res.id), ('state', 'not in', ['draft', 'cancelled'])], limit=1)
            if payment_id:
                res.last_payment_amount = payment_id.amount
                res.last_payment_date = payment_id.payment_date

    @api.multi
    def _payment_total(self):
        account_payment = self.env['account.payment']
        if not self.ids:
            self.amount_payment = 0.0
            return True
        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self:
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        # searching account.payment via the orm is comparatively expensive
        # (generates queries "id in []" forcing to build the full table).
        # In simple cases where all invoices are in the same currency than the user's company
        # access directly these elements

        # generate where clause to include multicompany rules
        where_query = account_payment._where_calc([
            ('partner_id', 'in', all_partner_ids), ('state', 'not in', ['draft', 'cancelled']),
            ('partner_type', 'in', ('customer', 'supplier'))
        ])
        account_payment._apply_ir_rules(where_query, 'read')
        from_clause, where_clause, where_clause_params = where_query.get_sql()

        # price_total is in the company currency
        query = """
                  SELECT SUM(amount) as total, partner_id
                    FROM account_payment account_payment
                   WHERE %s
                   GROUP BY partner_id
                """ % where_clause
        self.env.cr.execute(query, where_clause_params)
        amount_totals = self.env.cr.dictfetchall()
        for partner, child_ids in all_partners_and_children.items():
            partner.amount_payment = sum(price['total'] for price in amount_totals if price['partner_id'] in child_ids)

    @api.multi
    def action_view_partner_payments(self):
        payment_ids = self.env['account.payment'].search([('partner_id', '=', self.id)])
        action = self.env.ref('account.action_account_payments_payable')
        result = action.read()[0]
        # choose the view_mode accordingly
        # TS bug
        if len(payment_ids) > 1:
            # result['domain'] = "[('id', 'in', " + str(payment_ids.ids) + ")]"
            result['domain'] = [('id', 'in', payment_ids.ids)]
        elif len(payment_ids) == 1:
            res = self.env.ref('account.view_account_payment_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = payment_ids.id
        return result

    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form' and self.env.context.get('Followupfirst'):
    #         doc = etree.XML(res['arch'], parser=None, base_url=None)
    #         first_node = doc.xpath("//page[@name='followup_tab']")
    #         root = first_node[0].getparent()
    #         root.insert(0, first_node[0])
    #         res['arch'] = etree.tostring(doc, encoding="utf-8")
    #     return res

    @api.multi
    def _get_latest(self):
        company = self.env.user.company_id
        for partner in self:
            amls = partner.unreconciled_aml_ids
            latest_date = False
            latest_level = False
            latest_days = False
            latest_level_without_lit = False
            latest_days_without_lit = False
            for aml in amls:
                aml_followup = aml.followup_line_id
                if (aml.company_id == company) and aml_followup and (not latest_days or latest_days < aml_followup.delay):
                    latest_days = aml_followup.delay
                    latest_level = aml_followup.id
                if (aml.company_id == company) and aml.followup_date and (not latest_date or latest_date < aml.followup_date):
                    latest_date = aml.followup_date
                if (aml.company_id == company) and not aml.blocked and (aml_followup and (not latest_days_without_lit or latest_days_without_lit < aml_followup.delay)):
                    latest_days_without_lit = aml_followup.delay
                    latest_level_without_lit = aml_followup.id
            partner.latest_followup_date = latest_date
            partner.latest_followup_level_id = latest_level
            partner.latest_followup_level_id_without_lit = latest_level_without_lit

    @api.multi
    def do_partner_manual_action(self, partner_ids):
        # partner_ids -> res.partner
        for partner in self.browse(partner_ids):
            # Check action: check if the action was not empty, if not add
            action_text = ""
            followup_without_lit = partner.latest_followup_level_id_without_lit
            if partner.payment_next_action:
                action_text = \
                    (partner.payment_next_action or '') + "\n" + \
                    (followup_without_lit.manual_action_note or '')
            else:
                action_text = followup_without_lit.manual_action_note or ''

            # Check date: only change when it did not exist already
            action_date = partner.payment_next_action_date or \
                fields.Date.today()

            # Check responsible: if partner has not got a responsible already,
            # take from follow-up
            responsible_id = False
            if partner.payment_responsible_id:
                responsible_id = partner.payment_responsible_id.id
            else:
                p = followup_without_lit.manual_action_responsible_id
                responsible_id = p and p.id or False
            partner.write({'payment_next_action_date': action_date,
                           'payment_next_action': action_text,
                           'payment_responsible_id': responsible_id})

    def do_partner_print(self, wizard_partner_ids, data):
        # wizard_partner_ids are ids from special view, not from res.partner
        if not wizard_partner_ids:
            return {}
        data['partner_ids'] = wizard_partner_ids
        datas = {
            'ids': wizard_partner_ids,
            'model': 'payment.followup',
            'form': data
        }
        return self.env.ref('payment_followup.action_report_followup').report_action(self, data=datas)

    @api.multi
    def _get_amounts_and_date(self):
        '''
        Function that computes values for the followup functional fields.
        Note that 'payment_amount_due' is similar to 'credit' field on
        res.partner except it filters on user's company.
        '''
        company = self.env.user.company_id
        current_date = fields.Date.today()
        for partner in self:
            worst_due_date = False
            partner.payment_earliest_due_date = False
            amount_due = amount_overdue = 0.0
            for aml in partner.unreconciled_aml_ids.filtered(lambda x: x.account_id.user_type_id.type == 'receivable'):
                # TS - bug shld filtered out only receivable and posted
                # print (">>", aml.company_id, company, aml.account_id.user_type_id.type, aml.invoice_id, aml.invoice_id.state)
                # Shivam - bug fix for open invoice and remove journal state filter
                if aml.company_id == company and aml.invoice_id and aml.invoice_id.state == 'open':
                    date_maturity = aml.date_maturity or aml.date
                    if not worst_due_date or date_maturity < worst_due_date:
                        worst_due_date = date_maturity
                    amount_due += aml.result
                    if date_maturity <= current_date:
                        amount_overdue += aml.result
            partner.payment_amount_due = amount_due
            partner.payment_amount_overdue = amount_overdue
            partner.payment_earliest_due_date = worst_due_date

    @api.multi
    def _get_followup_overdue_query(self, args, overdue_only=False):
        '''
        This function is used to build the query and arguments to use when
        making a search on functional fields
            * payment_amount_due
            * payment_amount_overdue
        Basically, the query is exactly the same except that for overdue
        there is an extra clause in the WHERE.

        :param args: arguments given to the search in the usual
        domain notation (list of tuples)
        :param overdue_only: option to add the extra argument to filter on
        overdue accounting entries or not
        :returns: a tuple with
            * the query to execute as first element
            * the arguments for the execution of this query
        :rtype: (string, [])
        '''

        company_id = self.env.user.company_id.id
        having_where_clause = ' AND '.join(
            map(lambda x: '(SUM(bal2) %s %%s)' % (x[1]), args))
        having_values = [x[2] for x in args]
        having_where_clause = having_where_clause % (having_values[0])
        overdue_only_str = overdue_only and 'AND date_maturity <= NOW()' or ''
        return ('''SELECT pid AS partner_id, SUM(bal2) FROM
                                    (SELECT CASE WHEN bal IS NOT NULL THEN bal
                                    ELSE 0.0 END AS bal2, p.id as pid FROM
                                    (SELECT (debit-credit) AS bal, partner_id
                                    FROM account_move_line l
                                    WHERE account_id IN
                                            (SELECT id FROM account_account
                                            WHERE user_type_id IN (SELECT id
                                            FROM account_account_type
                                            WHERE type=\'receivable\'
                                            ))
                                    %s AND full_reconcile_id IS NULL
                                    AND company_id = %s) AS l
                                    RIGHT JOIN res_partner p
                                    ON p.id = partner_id ) AS pl
                                    GROUP BY pid HAVING %s''') % (
            overdue_only_str, company_id, having_where_clause)

    @api.multi
    def _payment_overdue_search(self, operator, operand):
        args = [('payment_amount_overdue', operator, operand)]
        query = self._get_followup_overdue_query(args, overdue_only=True)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    @api.multi
    def _payment_earliest_date_search(self, operator, operand):
        args = [('payment_earliest_due_date', operator, operand)]
        company_id = self.env.user.company_id.id
        having_where_clause = ' AND '.join(
            map(lambda x: "(MIN(l.date_maturity) %s '%%s')" % (x[1]), args))
        having_values = [x[2] for x in args]
        having_where_clause = having_where_clause % (having_values[0])
        query = 'SELECT partner_id FROM account_move_line l WHERE account_id IN (SELECT id FROM account_account ' \
                'WHERE user_type_id IN (SELECT id FROM account_account_type WHERE type=\'receivable\')) AND l.company_id = %s ' \
                'AND l.full_reconcile_id IS NULL ' \
                'AND l.move_id in (SELECT id FROM account_move WHERE id in (SELECT move_id FROM account_invoice WHERE type=\'out_invoice\' AND state=\'open\'))' \
                'AND partner_id IS NOT NULL GROUP BY partner_id '
        query = query % (company_id)
        if having_where_clause:
            query += ' HAVING %s ' % (having_where_clause)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    @api.multi
    def _payment_due_search(self, operator, operand):
        args = [('payment_amount_due', operator, operand)]
        query = self._get_followup_overdue_query(args, overdue_only=False)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    def _get_partners(self):
        # this function search for the partners linked to all
        # account.move.line 'ids' that have been changed
        partners = set()
        for aml in self:
            if aml.partner_id:
                partners.add(aml.partner_id.id)
        return list(partners)

    @api.multi
    def _get_followup_emails(self):
        for partner in self:
            payment_emails = []
            if partner.default_payment_email and partner.email:
                payment_emails.append(partner.email)
            payment_partners = partner.child_ids.filtered(lambda c: c.default_payment_email)
            for payment_partner in payment_partners:
                if payment_partner.email and payment_partner.id != partner.id:
                    payment_emails.append(payment_partner.email)
            if len(payment_emails) > 0:
                #print('>>>>>>>>> _get_followup_emails partner=', partner.name)
                #print('>>>>>>>>> _get_followup_emails payment_emails=', str(payment_emails))
                partner.followup_emails = False
                partner.followup_emails = ','.join(payment_emails)

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('make_followup_histry'):
            histry_data = self.env.context.get('histry_data')
            self.env['partner.payment.followup'].create(histry_data)
        return super(ResPartner, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


class ResPartnerFollowupHistry(models.Model):
    _name = 'partner.payment.followup'
    _description = 'Partner Follow-up'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Partner")
    date = fields.Datetime(string="Sent Date")
    sent_by = fields.Many2one('res.users', string="Send By")
    overdue_amount = fields.Float(string="Over Due Amount")
    due_amount = fields.Float(string="Due Amount")
    earliyest_duedate = fields.Date(string="Earliest Due Date")
    inc_over_due_inv = fields.Boolean(string="Include Overdue Inv.")
    inv_due_date = fields.Date(string="Due Date")
    inc_open_inv = fields.Boolean(string="Include Open Inv.")
    send_type = fields.Selection([('soa', "SOA"), ('overdue_invoices', 'Overdue Invoices'), ('soa_overdue', 'SOA + Overdue Invoices'), ('open_invoice', 'Open Invoices'), ('soa_open', 'SOA + Open Invoices')], string="Send Type")
    action_type = fields.Selection([('manual', 'Manual'), ('automatic', ' Automatic')], string="Action Type", default='manual')
    last_followup_level_id = fields.Many2one('payment.followup.line', string="Last Followup Level")
