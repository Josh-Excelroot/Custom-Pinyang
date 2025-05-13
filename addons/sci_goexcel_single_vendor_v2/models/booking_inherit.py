from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import float_round


class CostProfitSingleVendor(models.Model):
    _inherit = "freight.cost_profit"

    account_invoice_line = fields.Many2one('account.invoice.line')


class BookingSingleVendor(models.Model):
    _inherit = "freight.booking"

    # Booking
    @api.multi
    def action_create_vendor_bill(self):
        print("Single Vendor")
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        vendor_po = vendor_po.filtered(lambda c: c.invoiced == False)
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.customer_name.id,
                'name': '%s' % self.booking_no,
                'company_id': self.company_id.id,
            }
            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            if line.vendor_bill_id and not line.invoiced:
                raise exceptions.ValidationError('Some items are already billed. Please tick on "Billed" column for the items that are already billed.')
            if not line.invoiced:
                if line.vendor_id != vendor_id:
                    vb = self.env['account.invoice']
                    vendor_count = True
                    vendor_id = line.vendor_id
                    # combine multiple cost lines from same vendor
                    value = []
                    vendor_bill_created = []
                    filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                    for vb_line in filtered_vb_lines:
                        account_id = False
                        price_after_converted = float_round(vb_line.cost_price * vb_line.cost_currency_rate, 6, rounding_method='HALF-UP')
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        print(account_id)
                        value.append([0, 0, {
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'product_desc': vb_line.product_name or '',
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'freight_booking': self.id,
                            'booking_line_id': vb_line.id,
                            'freight_currency': vb_line.cost_currency.id or False,
                            'freight_foreign_price': vb_line.cost_price or 0.0,
                            'freight_currency_rate': float_round(vb_line.cost_currency_rate, 6, rounding_method='HALF-UP') or 1.000000,
                        }])
                        vb_line.invoiced = True

                    vendor_bill_id = False
                    if value:
                        vendor_bill_id = vb.with_context(create_from_job=True).create({
                            'type': 'in_invoice',
                            'invoice_line_ids': value,
                            'default_currency_id': self.env.user.company_id.currency_id.id,
                            'company_id': self.company_id.id,
                            'date_invoice': fields.Date.context_today(self),
                            'origin': self.booking_no,
                            'partner_id': vendor_id.id,
                            'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                            'freight_booking': self.id,
                        })

        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')