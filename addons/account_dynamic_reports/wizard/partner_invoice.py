from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

FETCH_RANGE = 2000


class InsPartnerInvoice(models.TransientModel):
    _name = "ins.partner.invoice"
    _inherit = ['dynamic.reports.mixin']
    _description = "Partner Invoice"

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Partner Invoice'))
        return res

    invoice_type = fields.Selection(
        [('in_invoice', 'Vendor Bills'),
         ('in_refund', 'Vendor Refunds'),
         ('out_invoice', 'Customer Invoice'),
         ('out_refund', 'Customer Refund')],
        string='Invoice Type', required=False
    )
    # partner_type = fields.Selection(
    #     [('customer', 'Customer'),
    #      ('supplier', 'Supplier')],
    #     string='Partner Type', required=False
    # )
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
    invoice_number = fields.Char(
        string='Invoice Number'
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    include_partner_ref = fields.Boolean('Include Partner\'s ref', default=True)

    @api.model
    def create(self, vals):
        ret = super(InsPartnerInvoice, self).create(vals)
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

        ret = super(InsPartnerInvoice, self).write(vals)
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

        # filters['partner_type'] = ''
        # if data.get('partner_type') == 'customer':
        #     filters['partner_type'] = 'Customers'
        # if data.get('partner_type') == 'supplier':
        #     filters['partner_type'] = 'Suppliers'

        filters['invoice_type'] = ''
        if data.get('invoice_type') == 'in_invoice':
            filters['invoice_type'] = 'Vendor Bills'
        if data.get('invoice_type') == 'in_refund':
            filters['invoice_type'] = 'Vendor refund'
        if data.get('invoice_type') == 'out_invoice':
            filters['invoice_type'] = 'Customer Invoice'
        if data.get('invoice_type') == 'out_refund':
            filters['invoice_type'] = 'Customer Refund'

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

        filters['company_currency_name'] = self.env.user.company_id.currency_id.name
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
                WHERE += ' AND inv.reconciled'
            if data.get('reconciled') == 'unreconciled':
                WHERE += ' AND NOT inv.reconciled'

            if data.get('invoice_type'):
                WHERE += " AND inv.type = '%s'" % (data.get('invoice_type'))

            # if data.get('partner_type'):
            #     WHERE += " AND inv.partner_type = '%s'" % (data.get('partner_type'))

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

            if data.get('invoice_number', False):
                WHERE += " AND inv.number ILIKE '%%%s%%'" % (
                    data.get('invoice_number', False))

            WHERE += " AND inv.state IN ('open','paid')"

            # if data.get('target_moves') == 'posted_only':
            #     WHERE += " AND m.state = 'posted'"
            #print('>>>>>>>>>>> WHERE=', WHERE)
            return WHERE

    def build_detailed_move_lines(self, invoice=0, fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param payment: Integer - Payment ID
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list )
        '''
        move_lines = []
        aml_lines = []
        invoices = self.env['account.invoice'].browse(invoice)
        for invoice in invoices:
            for line in invoice.move_id.line_ids:
                if line.account_id.reconcile:
                    aml_lines.append(line.id)

        for aml in self.env['account.move.line'].browse(aml_lines):
            # Debit ids
            for debit_line in aml.matched_debit_ids:
                debit_ml = debit_line.debit_move_id
                debit_move = debit_ml.move_id
                credit_ml = debit_line.credit_move_id
                credit_move = credit_ml.move_id
                company_currency_id = debit_line.company_currency_id.id
                company_currency = self.env['dynamic.reports.mixin'].create_query_and_fetch('res_currency', 'id,name,symbol,rounding,position',f'id={company_currency_id}',first_column=False, obj_format=True, limit=1)
                currency_id = debit_line.currency_id.id or company_currency_id
                currency = self.env['dynamic.reports.mixin'].create_query_and_fetch('res_currency', 'id,name,symbol,rounding,position',f'id={currency_id}',first_column=False, obj_format=True, limit=1)
                matched_lines = {
                    'date': credit_ml.date,
                    'ref': debit_move.name,
                    'description': credit_ml.invoice_id.reference or
                    #debit_line.credit_move_id.invoice_id.communication or
                    credit_ml.ref or
                    credit_ml.name,
                    'doc_amount': debit_ml.balance,
                    'knock_off_amount': debit_line.amount,
                    'knock_off_in_currency': debit_line.amount_currency,
                    'move_id': credit_move.id,
                    'analytic_account_id': credit_ml.analytic_account_id and
                    credit_ml.analytic_account_id.id,
                    'analytic_account_string': credit_ml.analytic_account_id and
                    credit_ml.analytic_account_id.name or '',
                    'analytic_tags_ids': [' ,'.join(tag.name) for tag in
                                          credit_ml.analytic_tag_ids],
                    'currency_id': currency.id,
                    'currency_name': currency.name,
                    'currency_symbol': currency.symbol,
                    'currency_precision': currency.rounding,
                    'currency_position': currency.position,
                    'company_currency_id': company_currency.id,
                    'company_currency_name': company_currency.name,
                    'company_currency_symbol': company_currency.symbol,
                    'company_currency_position': company_currency.position,
                    'company_currency_precision': company_currency.rounding,
                }
                move_lines.append(matched_lines)
            # Credit ids
            for credit_line in aml.matched_credit_ids:
                debit_ml = credit_line.debit_move_id
                debit_move = debit_ml.move_id
                credit_ml = credit_line.credit_move_id
                credit_move = credit_ml.move_id
                company_currency_id = credit_line.company_currency_id.id
                company_currency = self.env['dynamic.reports.mixin'].create_query_and_fetch('res_currency', 'id,name,symbol,rounding,position',f'id={company_currency_id}',first_column=False, obj_format=True, limit=1)
                currency_id = credit_line.currency_id.id or company_currency_id
                currency = self.env['dynamic.reports.mixin'].create_query_and_fetch('res_currency', 'id,name,symbol,rounding,position',f'id={currency_id}',first_column=False, obj_format=True, limit=1)
                matched_lines = {
                    'date': debit_ml.date,
                    'ref': credit_move.name,
                    'description': debit_ml.invoice_id.reference or
                    #credit_line.debit_move_id.invoice_id.communication or
                    debit_ml.ref or
                    debit_ml.name,
                    'doc_amount': credit_ml.balance,
                    'knock_off_amount': credit_line.amount,
                    'knock_off_in_currency': credit_line.amount_currency,
                    'move_id': debit_move.id,
                    'analytic_account_id': debit_ml.analytic_account_id and
                    debit_ml.analytic_account_id.id,
                    'analytic_account_string': debit_ml.analytic_account_id and
                    debit_ml.analytic_account_id.name or '',
                    'analytic_tags_ids': [', '.join(tag.name) for tag in
                                          debit_ml.analytic_tag_ids],
                    'currency_id': currency.id,
                    'currency_name': currency.name,
                    'currency_symbol': currency.symbol,
                    'currency_precision': currency.rounding,
                    'currency_position': currency.position,
                    'company_currency_id': company_currency.id,
                    'company_currency_name': company_currency.name,
                    'company_currency_symbol': company_currency.symbol,
                    'company_currency_position': company_currency.position,
                    'company_currency_precision': company_currency.rounding,
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

        WHERE_FULL = WHERE + " AND inv.date_invoice >= '%s'" % data.get('date_from') + " AND inv.date_invoice <= '%s'" % data.get(
            'date_to')
        sql = (f'''
            SELECT
                inv.id AS invid,
                inv.partner_id AS partner_id,
                inv.date_invoice AS date_invoice,
                inv.currency_id,
                inv.number AS lname,
                inv.type AS invoice_type,
                mov.name AS journal_entry,
                inv.reference AS ref,
                inv.reconciled AS reco_state,
                j.code AS journal_code,
                c.id AS currency_id,
                c.name AS currency_name,
                c.symbol AS currency_symbol,
                c.position AS currency_position,
                c.rounding AS currency_precision,
                cc.id AS company_currency_id,
                cc.symbol AS company_currency_symbol,
                cc.rounding AS company_currency_precision,
                cc.position AS company_currency_position,
                p.name {self.include_partner_ref and "|| ' (' || COALESCE(p.ref, '') || ')'"} AS partner_name,
                COALESCE(inv.amount_total,0) AS amount_currency,
                ABS(COALESCE(inv.residual,0)) AS amount_unreconciled,
                CASE
                    WHEN c.id!=cc.id THEN COALESCE(inv.amount_total,0) * inv.exchange_rate_inverse
                    ELSE COALESCE(inv.amount_total,0)
                END as amount_company_currency,
                CASE
                    WHEN c.id!=cc.id THEN COALESCE(inv.residual,0) * inv.exchange_rate_inverse
                    ELSE COALESCE(inv.residual,0)
                END as amount_unreconciled_company_currency
            FROM account_invoice inv
            LEFT JOIN res_currency c ON (inv.currency_id=c.id)
            LEFT JOIN res_partner p ON (inv.partner_id=p.id)
            LEFT JOIN account_move mov ON (inv.move_id=mov.id)
            JOIN account_journal j ON (inv.journal_id=j.id)
            LEFT JOIN res_company com ON (j.company_id=com.id)
            LEFT JOIN res_currency cc ON (com.currency_id=cc.id)
            WHERE %s
            ORDER BY inv.date_invoice asc, inv.partner_id 
        ''') % WHERE_FULL
        cr.execute(sql)
        res= cr.dictfetchall()
        for row in res:
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
        # self.onchange_date_range()
        # TS - fix the bug that the user must select the empty date_range if want to use the start_date and end_date
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
            'invoice_type': self.invoice_type,
            'include_details': self.include_details,
            'invoice_number': self.invoice_number,
            'partner_category_ids': self.partner_category_ids.ids,
            'journals_list': self.create_query_and_fetch('account_journal', 'id,name', f'id in {journals._ids + (0,0)}', fetchall=True, first_column=False),
            'accounts_list': self.create_query_and_fetch('account_account', 'id,name', f'id in {accounts._ids + (0,0)}', fetchall=True, first_column=False),
            'partners_list': self.create_query_and_fetch('res_partner', 'id,name', f'id in {partners._ids + (0,0)}', fetchall=True, first_column=False),
            'category_list': self.create_query_and_fetch('res_partner_category', 'id,name', f'id in {categories._ids + (0,0)}', fetchall=True, first_column=False),
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
                        invoice=line['invid'])
                    line.update({'sub_lines': sub_lines})
            return filters, account_lines

    def action_pdf(self):
        filters, account_lines = self.get_report_datas(call_from=True)
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_partner_invoice').with_context(landscape=True).report_action(
            self, data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PI View',
            'tag': 'dynamic.pi',
            'context': {'wizard_id': self.id}
        }
        return res
