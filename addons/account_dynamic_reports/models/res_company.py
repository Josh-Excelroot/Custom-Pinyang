from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    load_last_dynamic_reports_record = fields.Boolean()
    partner_ageing_exch_entries = fields.Boolean()
    partner_ageing_exclude_accounts = fields.Many2many('account.account')
    general_ledger_exch_entries = fields.Boolean()
    unposted_entries_dynamic_reports = fields.Boolean()

    unrealized_forex_gain_account_id = fields.Many2one('account.account')
    unrealized_forex_loss_account_id = fields.Many2one('account.account')

    strict_range = fields.Boolean(string='Use Strict Range', default=True,
                                  help='Use this if you want to show TB with retained earnings section')
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=30)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=60)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=90)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=120)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=180)
    date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Default Date Range', default='this_financial_year', required=True
    )
    financial_year = fields.Selection([
        ('april_march', '1 April to 31 March'),
        ('july_june', '1 july to 30 June'),
        ('january_december', '1 Jan to 31 Dec')
    ], string='Financial Year', default='january_december', required=True)
    tb_date_from = fields.Date(string='Start date')
    tb_date_to = fields.Date(string='End date')


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    excel_format = fields.Char(
        string='Excel format', default='_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ', required=True)
    # excel_format = fields.Char(string='Excel format', default='#,##0.00', required=True)


class ins_account_financial_report(models.Model):
    _name = "ins.account.financial.report"
    _description = "Account Report"

    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    def _get_children_by_order(self, strict_range):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search(
            [('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order(strict_range)
        if not strict_range:
            res -= self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_unallocated_earnings0')
            res -= self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_equitysum0')
        return res

    def update_display_detail(self, option):
        self.display_detail_temp = option

    #### Margin % in P&L and BS (CR-9 Additional #A3) | Rajeel | 17/03/2023 ####
    def _get_percent_margin_divisor_record_id(self):
        record = self._get_children_by_order(strict_range=True).filtered('percent_margin_divisor')
        if record:
            return record[0].id
        return False

    #### Margin % in P&L and BS (CR-9 Additional #A3) | Rajeel | 17/03/2023 ####

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('ins.account.financial.report', 'Parent')
    children_ids = fields.One2many(
        'ins.account.financial.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_get_level', string='Level', store=True)
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
    ], 'Type', default='sum')
    account_ids = fields.Many2many(
        'account.account', 'ins_account_account_financial_report', 'report_line_id', 'account_id', 'Accounts')
    exclude_account_ids = fields.Many2many(
        'account.account', 'ins_account_account_financial_report', 'report_line_id', 'account_id', 'Exclude Accounts')
    account_report_id = fields.Many2one(
        'ins.account.financial.report', 'Report Value')
    account_type_ids = fields.Many2many(
        'account.account.type', 'ins_account_account_financial_report_type', 'report_id', 'account_type_id', 'Account Types')
    sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')], 'Sign on Reports', required=True, default='1',
                            help='For accounts that are typically more debited than credited and that you would like to print as negative amounts in your reports, you should reverse the sign of the balance; e.g.: Expense account. The same applies for accounts that are typically more credited than debited and that you would like to print as positive amounts in your reports; e.g.: Income account.')
    range_selection = fields.Selection([
        ('from_the_beginning', 'From the Beginning'),
        ('current_date_range', 'Based on Current Date Range'),
        ('initial_date_range', 'Based on Initial Date Range')],
        help='"From the beginning" will select all the entries before and on the date range selected.'
             '"Based on Current Date Range" will select all the entries strictly on the date range selected'
             '"Based on Initial Date Range" will select only the initial balance for the selected date range',
        string='Custom Date Range')
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_flat')
    display_detail_temp = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Automatic formatting'),
        ('1', 'Main Title 1 (bold, underlined)'),
        ('2', 'Title 2 (bold)'),
        ('3', 'Title 3 (bold, smaller)'),
        ('4', 'Normal Text'),
        ('5', 'Italic Text (smaller)'),
        ('6', 'Smallest Text'),
    ], 'Financial Report Style', default='0',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    percent_margin_divisor = fields.Boolean(string='Margin % Divisor')
    company_id = fields.Many2one('res.company')
    financial_report_menu = fields.Selection([('none', 'None'), ('profit_loss', 'Profit and Loss'),
                                              ('balance_sheet', 'Balance Sheet'), ('cash_flow', 'Cash Flow Report')],
                                             default='none')

    def get_children(self):
        children_ids = self.mapped('children_ids')
        return children_ids + children_ids.get_children_tree()

    def change_children_company(self):
        for child in self.children_ids:
            child.company_id = self.company_id.id
            child.change_children_company()

    def get_children_tree(self, depth=0):
        result = ""
        children = self.children_ids
        for child in children:
            result += f"> {'> ' * depth} {child.name}\n"
            result += child.get_children_tree(depth + 1)
        return result

    @api.onchange('company_id')
    def _onchange_company_id(self):
        try:
            rec = self._origin
        except AttributeError:
            rec = self
        tree = rec.get_children_tree()
        if tree:
            return {'warning': {'title': 'Warning',
                                'message': 'Changing company will also change company to all these children\n' + tree}}

    @api.constrains('company_id')
    def validate_company(self):
        if self.parent_id and self.company_id and self.parent_id.company_id != self.company_id:
            raise ValidationError(f'Company is not matching with parent\'s company ({self.parent_id.company_id.name}) !\n'
                                  f'Record can not be saved.')
        self.change_children_company()


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def get_cashflow_domain(self):
        cash_flow_id = self.env.ref(
            'account_dynamic_reports.ins_account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_category = fields.Many2one(
        'ins.account.financial.report', string="Cash Flow type", domain=get_cashflow_domain)

    @api.onchange('cash_flow_category')
    def onchange_cash_flow_category(self):
        # Add account to cash flow record to account_ids
        if self._origin and self._origin.id:
            self.cash_flow_category.write(
                {'account_ids': [(4, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(4, self._origin.id)]})
        # Remove account from previous category
        # In case of changing/ removing category
        if self._origin.cash_flow_category:
            self._origin.cash_flow_category.write(
                {'account_ids': [(3, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(3, self._origin.id)]})


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    @api.depends('move_line_ids.reconciled', 'move_line_ids.full_reconcile_id')
    def _get_move_reconciled_state(self):
        for payment in self:
            rec = True
            unreconciled_amount = 0.0
            amount_in_cc = 0.0
            for aml in payment.move_line_ids.filtered(lambda x: x.account_id.reconcile):
                if not aml.full_reconcile_id:
                    rec = False
                    unreconciled_amount += aml.amount_residual
                amount_in_cc += abs(aml.balance)
            payment.move_reconciled_state = rec
            payment.unreconciled_amount = unreconciled_amount
            payment.amount_in_cc = amount_in_cc

    move_reconciled_state = fields.Boolean(
        compute="_get_move_reconciled_state", readonly=True, store=True)
    unreconciled_amount = fields.Float(
        compute="_get_move_reconciled_state", string='Unreconciled Amount', store=True)
    amount_in_cc = fields.Float(
        compute="_get_move_reconciled_state", string='Amount in CC', store=True)


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    @api.depends('move_id.line_ids.reconciled')
    def _get_move_reconciled_state(self):
        for voucher in self:
            rec = True
            unreconciled_amount = 0.0
            amount_in_cc = 0.0
            for aml in voucher.move_id.line_ids.filtered(lambda x: x.account_id.reconcile):
                if not aml.reconciled:
                    rec = False
                    unreconciled_amount += aml.amount_residual
                amount_in_cc += abs(aml.balance)
            voucher.move_reconciled_state = rec
            voucher.unreconciled_amount = unreconciled_amount
            voucher.amount_in_cc = amount_in_cc

    move_reconciled_state = fields.Boolean(
        compute="_get_move_reconciled_state", readonly=True, store=True)
    unreconciled_amount = fields.Float(
        compute="_get_move_reconciled_state", string='Unreconciled Amount', store=True)
    amount_in_cc = fields.Float(
        compute="_get_move_reconciled_state", string='Amount in CC', store=True)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_description = fields.Char()


class AccountMove(models.Model):
    _inherit = 'account.move'

    period_13 = fields.Boolean(help='By checking, This JE will be considered as Period 13 JE')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _query_get(self, domain=None):
        if domain is None:
            domain = []
        if 'include_period_13' in self._context and not self._context.get('include_period_13'):
            domain.append(('move_id.period_13', '=', False))
        return super(AccountMoveLine, self)._query_get(domain=domain)
