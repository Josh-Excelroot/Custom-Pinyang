from odoo import fields, models, api


class BookingInvoiceLines(models.Model):
    _name = "booking.invoice.line"

    invoice_no = fields.Char(string="Invoice No")
    reference = fields.Char(string="Vendor Invoice/Payment Ref.")
    invoice_amount = fields.Float(string="Amount", store=True)
    type = fields.Char(string='Type', help="invoice, vendor bill, customer CN and vendor CN, vendor debit note")
    booking_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    job_no = fields.Char(string="Job No")
    total_sale = fields.Float(compute='_get_total_sale_cost', store=True)
    total_cost = fields.Float(compute='_get_total_sale_cost', store=True)

    @api.multi
    def _get_total_sale_cost(self):
        for rec in self:
            rec.total_sale = 0.0
            rec.total_cost = 0.0
            if rec.type in ('in_invoice', 'in_refund', 'purchase_receipt'):
                rec.total_cost += rec.invoice_amount
            if rec.type in ('out_invoice', 'out_refund'):
                rec.total_sale += rec.invoice_amount