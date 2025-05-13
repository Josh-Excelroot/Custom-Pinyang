from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    show_attachment = fields.Boolean()

    # @api.multi
    # def action_invoice_open_ip(self):
    #     res = super(AccountInvoice, self).action_invoice_open_ip()

    def show_attachment_preview(self):
        self.show_attachment = True

    def hide_attachment_preview(self):
        self.show_attachment = False

    def get_invoice_type(self):
        if self.type == 'out_invoice' and self.debit_invoice_id:
            return 'Customer Debit Note'
        elif self.type == 'out_invoice':
            return 'Customer Invoice'
        elif self.type == 'out_refund':
            return 'Customer Credit Note'
        elif self.type == 'in_invoice' and self.debit_invoice_id:
            return 'Vendor Debit Note'
        elif self.type == 'in_invoice':
            return 'Vendor Bill'
        elif self.type == 'in_refund':
            return 'Vendor Credit Note / Refund'
        return ''

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    # 12.0.1.1 - change default function description autofill format
    def _get_invoice_line_name_from_product(self):
        result = super(AccountInvoiceLine, self)._get_invoice_line_name_from_product()
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()
        if not self.product_id:
            return ''
        invoice_type = self.invoice_id.type
        rslt = self.product_id.name
        if invoice_type in ('in_invoice', 'in_refund'):
            if self.product_id.description_purchase:
                rslt += '\n' + self.product_id.description_purchase
        else:
            if self.product_id.description_sale:
                rslt += '\n' + self.product_id.description_sale

        return rslt
