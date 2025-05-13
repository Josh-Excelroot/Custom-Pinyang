from odoo import models, fields, api


class res_partner(models.Model):
    _inherit = 'res.partner'

    overdue_date = fields.Date(string='Overdue Date')
    soa_currency_id = fields.Many2one('res.currency', string='SOA Currency', compute='_compute_soa_currency')
    invoice_start_date = fields.Date(string='Invoice Date')
    aging_by = fields.Selection([('inv_date', 'Invoice Date'), ('due_date', 'Due Date')], string='Aging By')
    aging_group = fields.Selection([('by_month', 'By Month'), ('by_days', 'By Days')], string='Ageing Group')
    account_type = fields.Selection([('ar', 'Receivable'), ('ap', 'Payable'), ('both', 'Both')], string='Account Type')
    soa_note = fields.Text(related="company_id.soa_note", string='SOA Note', track_visibility='onchange')
    # soa_note = fields.Text(string='SOA Note', track_visibility='onchange', compute="_get_use_soa_note")
    soa_type = fields.Selection([('all', 'All'), ('unpaid_invoices', 'Unpaid Invoices Only')], string='SOA Type')
    attention = fields.Char(string="Attention")
    show_payment_term = fields.Boolean(string='Show Payment Term')

    # @api.multi
    # def _get_use_soa_note(self):
    #     for record in self:
    #         # TS
    #         record.soa_note = self.env.user.company_id.soa_note

    @api.multi
    def _compute_soa_currency(self):
        for record in self:
            invoice = False
            if record.account_type == 'ap':
                invoice = self.env['account.invoice'].search([('partner_id', '=', record.id), ('type', '=', 'in_invoice'), ('state', '=', 'open'), ], limit=1)
                # if record.property_purchase_currency_id:
                #     record.soa_currency_id = record.property_purchase_currency_id.id
                # else:
                #     record.soa_currency_id = self.env.user.company_id.currency_id.id
            elif record.account_type == 'ar':
                invoice = self.env['account.invoice'].search([('partner_id', '=', record.id), ('type', '=', 'out_invoice'), ('state', '=', 'open'), ], limit=1)
            elif record.account_type == 'both':
                invoice = self.env['account.invoice'].search([('partner_id', '=', record.id), ('state', '=', 'open'), ], limit=1)
            # TS - bug (if Open invoices, use Invoice currency, else use the company currency)
            if invoice and record.soa_type == 'unpaid_invoices':
                record.soa_currency_id = invoice.currency_id.id
            else:
                record.soa_currency_id = self.env.user.company_id.currency_id.id
