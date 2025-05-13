from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

FETCH_RANGE = 2000


class InsPartnerPayment(models.TransientModel):
    _name = "ins.partner.payment"
    _inherit = ['dynamic.reports.mixin']
    _description = "Partner Payment"

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Partner Payment'))
        return res

    payment_type = fields.Selection(
        [('outbound', 'Send Money'),
         ('inbound', 'Receive Money')],
        string='Payment Type', required=False
    )
    partner_type = fields.Selection(
        [('customer', 'Customer'),
         ('supplier', 'Supplier')],
        string='Partner Type', required=False
    )
    reconciled = fields.Selection([('reconciled', 'Reconciled Only'),
                                   ('unreconciled', 'Unreconciled Only')],
                                  string='Reconcile Type')
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals',
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Partners'
    )
    include_details = fields.Boolean(
        string='Include Details', default=True
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    include_partner_ref = fields.Boolean(
        'Include Partner\'s ref', default=True
    )

    @api.model
    def create(self, vals):
        ret = super(InsPartnerPayment, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):

        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range': False})
        if vals.get('date_range'):
            date_from, date_to = self.get_dates_from_date_range(vals.get('date_range'))
            vals.update({'date_from': date_from, 'date_to': date_to})

        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'journal_ids') if type(j) is not list] + vals.get('journal_ids')})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('account_ids'):
            vals.update({'account_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'account_ids') if type(j) is not list] + vals.get('account_ids')})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})

        if vals.get('partner_ids'):
            vals.update({'partner_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'partner_ids') if type(j) is not list] + vals.get('partner_ids')})
        if vals.get('partner_ids') == []:
            vals.update({'partner_ids': [(5,)]})

        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(5, 0, 0)] + [(4, j) for j in vals.get('partner_category_ids') if
                                                                type(j) is not list] + vals.get(
                'partner_category_ids')})
        if vals.get('partner_category_ids') == []:
            vals.update({'partner_category_ids': [(5,)]})

        ret = super(InsPartnerPayment, self).write(vals)
        return ret

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(
                _('"Date from" must be less than or equal to "Date to"'))
        return True

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}

        filters['partner_type'] = ''
        if data.get('partner_type') == 'customer':
            filters['partner_type'] = 'Customers'
        if data.get('partner_type') == 'supplier':
            filters['partner_type'] = 'Suppliers'

        filters['payment_type'] = ''
        if data.get('payment_type') == 'inbound':
            filters['payment_type'] = 'Received Money'
        if data.get('payment_type') == 'outbound':
            filters['payment_type'] = 'Send Money'

        if data.get('journal_ids', []):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids', [])).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']

        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('partner_category_ids', []):
            filters['categories'] = self.env['res.partner.category'].browse(
                data.get('partner_category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        filters['reconciled'] = '-'
        if data.get('reconciled') == 'reconciled':
            filters['reconciled'] = 'Yes'
        if data.get('reconciled') == 'unreconciled':
            filters['reconciled'] = 'No'

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False

        filters['journals_list'] = data.get('journals_list')
        filters['accounts_list'] = data.get('accounts_list')
        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def build_where_clause(self, data=False):
        if not data:
            data = self.get_filters(default_filters={})

        if data:

            WHERE = '(1=1)'

            if data.get('reconciled') == 'reconciled':
                WHERE += ' AND pay.move_reconciled_state'
            if data.get('reconciled') == 'unreconciled':
                WHERE += ' AND NOT pay.move_reconciled_state'

            if data.get('payment_type'):
                WHERE += " AND pay.payment_type = '%s'" % (
                    data.get('payment_type'))

            if data.get('partner_type'):
                WHERE += " AND pay.partner_type = '%s'" % (
                    data.get('partner_type'))

            if data.get('journal_ids', []):
                WHERE += ' AND j.id IN %s' % str(
                    tuple(data.get('journal_ids')) + tuple([0]))

            if data.get('account_ids', []):
                WHERE += ' AND a.id IN %s' % str(
                    tuple(data.get('account_ids')) + tuple([0]))

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))
            # TS - add the Partner Tags
            if data.get('partner_category_ids', []):
                company_id = self.env.user.company_id
                partner_company_domain = [('parent_id', '=', False),
                                          '|',
                                          ('customer', '=', True),
                                          ('supplier', '=', True),
                                          '|',
                                          ('company_id', '=', company_id.id),
                                          ('company_id', '=', False)]
                partner_company_domain.append(
                    ('category_id', 'in', self.partner_category_ids.ids))
                partner_ids = self.env['res.partner'].search(
                    partner_company_domain)
                WHERE += ' AND p.id IN ' + str(tuple(partner_ids.ids))

            if data.get('company_id', False):
                WHERE += ' AND com.id = %s' % data.get('company_id')

            WHERE += " AND pay.state IN ('posted','sent','reconciled')"

            # if data.get('target_moves') == 'posted_only':
            #     WHERE += " AND m.state = 'posted'"
            return WHERE

    def build_where_clause_voucher(self, data=False):
        if not data:
            data = self.get_filters(default_filters={})

        if data:

            WHERE = '(1=1)'

            if data.get('reconciled') == 'reconciled':
                WHERE += ' AND vou.move_reconciled_state'
            if data.get('reconciled') == 'unreconciled':
                WHERE += ' AND NOT vou.move_reconciled_state'

            if data.get('payment_type'):
                if data.get('payment_type') == 'inbound':
                    WHERE += " AND vou.voucher_type = 'purchase'"
                else:
                    WHERE += " AND vou.voucher_type = 'sale'"

            if data.get('partner_type'):
                if data.get('partner_type') == 'customer':
                    WHERE += " AND vou.voucher_type = 'sale'"
                else:
                    WHERE += " AND vou.voucher_type = 'purchase'"

            if data.get('journal_ids', []):
                WHERE += ' AND j.id IN %s' % str(
                    tuple(data.get('journal_ids')) + tuple([0]))

            if data.get('account_ids', []):
                WHERE += ' AND a.id IN %s' % str(
                    tuple(data.get('account_ids')) + tuple([0]))

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))

            if data.get('company_id', False):
                WHERE += ' AND com.id = %s' % data.get('company_id')

            WHERE += " AND vou.state IN ('posted')"

            # if data.get('target_moves') == 'posted_only':
            #     WHERE += " AND m.state = 'posted'"
            return WHERE

    def build_detailed_move_lines(self, payment=0, internal_type='payment', fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param payment: Integer - Payment ID
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list )
        '''
        move_lines = []
        aml_lines = []
        if internal_type == 'payment':
            payments = self.env['account.payment'].browse(payment)
            for payment in payments:
                for line in payment.move_line_ids:
                    if line.account_id.reconcile:
                        aml_lines.append(line.id)
        else:
            payments = self.env['account.voucher'].browse(payment)
            for payment in payments:
                for line in payment.move_id.line_ids:
                    if line.account_id.reconcile:
                        aml_lines.append(line.id)

        for aml in self.env['account.move.line'].browse(aml_lines):
            # Debit ids
            for debit_line in aml.matched_debit_ids:
                matched_lines = {
                    'date': debit_line.credit_move_id.date,
                    'ref': debit_line.debit_move_id.move_id.name,
                    'description': debit_line.credit_move_id.payment_id.reference or
                    debit_line.credit_move_id.payment_id.communication or
                    debit_line.credit_move_id.ref or
                    debit_line.credit_move_id.name,
                    'doc_amount': debit_line.debit_move_id.balance,
                    'knock_off_amount': debit_line.amount,
                    'knock_off_in_currency': debit_line.amount_currency,
                    'move_id': debit_line.credit_move_id.move_id.id,
                    'analytic_account_id': debit_line.credit_move_id.analytic_account_id and
                    debit_line.credit_move_id.analytic_account_id.id,
                    'analytic_account_string': debit_line.credit_move_id.analytic_account_id and
                    debit_line.credit_move_id.analytic_account_id.name or '',
                    'analytic_tags_ids': [' ,'.join(tag.name) for tag in
                                          debit_line.credit_move_id.analytic_tag_ids],
                    'currency_id': debit_line.currency_id.id,
                    'currency_symbol': debit_line.currency_id.symbol,
                    'currency_precision': debit_line.currency_id.rounding,
                    'currency_position': debit_line.currency_id.position,
                    'company_currency_id': debit_line.company_currency_id.id,
                    'company_currency_symbol': debit_line.company_currency_id.symbol,
                    'company_currency_position': debit_line.company_currency_id.position,
                    'company_currency_precision': debit_line.company_currency_id.rounding,
                }
                move_lines.append(matched_lines)
            # Credit ids
            for credit_line in aml.matched_credit_ids:
                matched_lines = {
                    'date': credit_line.debit_move_id.date,
                    'ref': credit_line.credit_move_id.move_id.name,
                    'description': credit_line.debit_move_id.payment_id.reference or
                    credit_line.debit_move_id.payment_id.communication or
                    credit_line.debit_move_id.ref or
                    credit_line.debit_move_id.name,
                    'doc_amount': credit_line.credit_move_id.balance,
                    'knock_off_amount': credit_line.amount,
                    'knock_off_in_currency': credit_line.amount_currency,
                    'move_id': credit_line.debit_move_id.move_id.id,
                    'analytic_account_id': credit_line.debit_move_id.analytic_account_id and
                    credit_line.debit_move_id.analytic_account_id.id,
                    'analytic_account_string': credit_line.debit_move_id.analytic_account_id and
                    credit_line.debit_move_id.analytic_account_id.name or '',
                    'analytic_tags_ids': [', '.join(tag.name) for tag in
                                          credit_line.debit_move_id.analytic_tag_ids],
                    'currency_id': credit_line.currency_id.id,
                    'currency_symbol': credit_line.currency_id.symbol,
                    'currency_precision': credit_line.currency_id.rounding,
                    'currency_position': credit_line.currency_id.position,
                    'company_currency_id': credit_line.company_currency_id.id,
                    'company_currency_symbol': credit_line.company_currency_id.symbol,
                    'company_currency_position': credit_line.company_currency_id.position,
                    'company_currency_precision': credit_line.company_currency_id.rounding,
                }
                move_lines.append(matched_lines)
        return move_lines

    def process_data(self):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        cr = self.env.cr

        data = self.get_filters(default_filters={})

        ################## data from Receipts##########################################

        WHERE = self.build_where_clause(data)

        move_lines = []

        WHERE_FULL = WHERE + " AND pay.payment_date >= '%s'" % data.get('date_from') + " AND pay.payment_date <= '%s'" % data.get(
            'date_to')

        if self.include_partner_ref:
            partner_name = "CASE WHEN ref IS NOT NULL THEN CONCAT(p.name, ' (',p.ref, ')') ELSE p.name END"
        else:
            partner_name = "p.name"

        sql = (f'''
            SELECT
                pay.id AS payid,
                pay.partner_id AS partner_id,
                pay.payment_date AS payment_date,
                pay.currency_id,
                pay.name AS lname,
                pay.payment_type AS payment_type,
                pay.move_name AS journal_entry,
                pay.communication AS ref,
                pay.move_reconciled_state AS reco_state,
                'payment' AS internal_type,
                j.code AS journal_code,
                c.symbol AS currency_symbol,
                c.position AS currency_position,
                c.rounding AS currency_precision,
                cc.id AS company_currency_id,
                cc.symbol AS company_currency_symbol,
                cc.rounding AS company_currency_precision,
                cc.position AS company_currency_position,
                {partner_name} AS partner_name,
                COALESCE(pay.amount_in_cc,0) AS amount_currency,
                ABS(COALESCE(pay.unreconciled_amount,0)) AS amount_unreconciled
            FROM account_payment pay
            LEFT JOIN res_currency c ON (pay.currency_id=c.id)
            LEFT JOIN res_partner p ON (pay.partner_id=p.id)
            JOIN account_journal j ON (pay.journal_id=j.id)
            LEFT JOIN res_company com ON (j.company_id=com.id)
            LEFT JOIN res_currency cc ON (com.currency_id=cc.id)
            WHERE %s
            ORDER BY pay.payment_date asc, pay.partner_id 
        ''') % WHERE_FULL
        cr.execute(sql)
        for row in cr.dictfetchall():
            move_lines.append(row)

        ################## data from Vouchers ##########################################
        WHERE = self.build_where_clause_voucher(data)
        WHERE_FULL = WHERE + " AND vou.date >= '%s'" % data.get(
            'date_from') + " AND vou.date <= '%s'" % data.get(
            'date_to')
        sql = ('''
                    SELECT
                        vou.id AS payid,
                        vou.partner_id AS partner_id,
                        vou.date AS payment_date,
                        vou.currency_id,
                        vou.number AS lname,
                        '' AS payment_type,
                        move.name AS journal_entry,
                        vou.name AS ref,
                        vou.move_reconciled_state AS reco_state,
                        'voucher' AS internal_type,
                        j.code AS journal_code,
                        c.symbol AS currency_symbol,
                        c.position AS currency_position,
                        c.rounding AS currency_precision,
                        cc.id AS company_currency_id,
                        cc.symbol AS company_currency_symbol,
                        cc.rounding AS company_currency_precision,
                        cc.position AS company_currency_position,
                        p.name AS partner_name,
                        COALESCE(vou.amount_in_cc,0) AS amount_currency,
                        ABS(COALESCE(vou.unreconciled_amount,0)) AS amount_unreconciled
                    FROM account_voucher vou
                    LEFT JOIN res_currency c ON (vou.currency_id=c.id)
                    LEFT JOIN res_partner p ON (vou.partner_id=p.id)
                    JOIN account_journal j ON (vou.journal_id=j.id)
                    LEFT JOIN res_company com ON (j.company_id=com.id)
                    LEFT JOIN res_currency cc ON (com.currency_id=cc.id)
                    LEFT JOIN account_move move ON (move.id=vou.move_id)
                    WHERE %s
                    ORDER BY vou.date asc, vou.partner_id 
                ''') % WHERE_FULL
        cr.execute(sql)
        for row in cr.dictfetchall():
            move_lines.append(row)

        return move_lines

    def get_page_list(self, total_count):
        '''
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        '''
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i+1 for i in range(0, int(page_count))] or []

    def get_filters(self, default_filters={}):
        # TS - fix the bug that the user must select the empty date_range if want to use the start_date and end_date
        # self.onchange_date_range()
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('customer', '=', True),
                                  ('supplier', '=', True),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]
        if self.partner_category_ids:
            partner_company_domain.append(
                ('category_id', 'in', self.partner_category_ids.ids))
        journals = self.journal_ids if self.journal_ids else self.env['account.journal'].search(
            company_domain)
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(
            company_domain)
        partners = self.partner_ids if self.partner_ids else self.env['res.partner'].search(
            partner_company_domain)
        categories = self.partner_category_ids if self.partner_category_ids else self.env['res.partner.category'].search([
        ])

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'reconciled': self.reconciled,
            'partner_type': self.partner_type,
            'payment_type': self.payment_type,
            'include_details': self.include_details,
            'partner_category_ids': self.partner_category_ids.ids,
            'journals_list': [(j.id, j.name) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'partners_list': [(p.id, p.name) for p in partners],
            'category_list': [(c.id, c.name) for c in categories],
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_report_datas(self, default_filters={}, call_from=False):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
            account_lines = self.process_data()
            if call_from:
                for line in account_lines:
                    sub_lines = self.build_detailed_move_lines(
                        payment=line['payid'], internal_type=line['internal_type'])
                    line.update({'sub_lines': sub_lines})
            return filters, account_lines

    def action_pdf(self):
        filters, account_lines = self.get_report_datas(call_from=True)
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_partner_payment').with_context(landscape=True).report_action(
            self, data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PP View',
            'tag': 'dynamic.pp',
            'context': {'wizard_id': self.id}
        }
        return res
