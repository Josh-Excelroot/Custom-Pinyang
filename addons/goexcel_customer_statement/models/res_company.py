from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_bank_account = fields.Many2one('res.partner.bank', string="Default Bank Account", domain="[('partner_id', '=', id)]")
    soa_note = fields.Text(string="Additional Notes for SOA")
    soa_type = fields.Selection([('all', 'All'), ('unpaid_invoices', 'Unpaid Invoices Only')], string='SOA Type')
    soa_invoice_date_type = fields.Selection([('current_mth', 'Current Month'), ('last_mth', 'Last Month'), ('last_6_mth', 'Last 6 Months'),
                                              ('last_12_mth', 'Last 12 Months'), ('beginning', 'From Beginning')], string='Invoice Date')
    show_payment_term = fields.Boolean(string='Show Payment Term')
    aging_group = fields.Selection([('by_month', 'By Month'), ('by_days', 'By Days')], string='Ageing Group')