from odoo import api, models, fields, _
import datetime

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    #is_first_order = fields.Boolean()

    # @api.multi
    # def write(self, values):
    #     state = values.get('state', False)
    #     partner = self.partner_id
    #     if state == 'open' and partner.customer and partner.status in ['inactive', 'lost_customer']:
    #         partner.status = 'active'
    #         self.is_first_order = True
    #     return super(AccountInvoice, self).write(values)

    @api.multi
    def write(self, values):
        for record in self:
            if values.get('state'):
                partner = record.partner_id
                if values.get('state') == 'open' and record.type == 'out_invoice':
                    date_invoice = record.date_invoice or datetime.datetime.now().date()
                    if (partner.last_invoice_date and partner.last_invoice_date < date_invoice) or not partner.last_invoice_date:
                        partner.last_invoice_date = date_invoice
                    #kashif 12june23 : fix bug for tenton first order condition checking . missing fasle status value
                    if partner.customer and partner.status in ['inactive', 'lost_customer',False]:
                        partner.status = 'active'
                    #kashif 1august23 : fix bug for tenton first order condition checking . check if any inv exist for the partner
                    invoice = self.env['account.invoice'].search([('partner_id', '=', partner.id),('type', '=', 'out_invoice'), ('state', 'not in', ['draft']), ], limit=1)
                    if not invoice:
                        record.first_order = True
                    #end
        return super(AccountInvoice, self).write(values)