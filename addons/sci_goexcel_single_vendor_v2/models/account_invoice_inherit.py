from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import float_round


class AccountInvoiceSingleVendor(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceSingleVendor, self).write(vals)
        # After Save
        print("AccountInvoiceSingleVendor")
        for invoice in self:
            if invoice.type == 'in_invoice' and not invoice.debit_invoice_id:
                for new_invoice_line in invoice.invoice_line_ids:
                    if new_invoice_line.product_id and new_invoice_line.freight_booking:
                        # Check Analytic Account
                        if not new_invoice_line.freight_booking.analytic_account_id:
                            values = {
                                'partner_id': new_invoice_line.freight_booking.customer_name.id,
                                'name': '%s' % new_invoice_line.freight_booking.booking_no,
                                'company_id': self.env.user.company_id.id,
                            }
                            analytic_account = self.env['account.analytic.account'].sudo().create(values)
                            new_invoice_line.freight_booking.write({'analytic_account_id': analytic_account.id,
                                           })
                            new_invoice_line.account_analytic_id = analytic_account.id
                        else:
                            new_invoice_line.account_analytic_id = new_invoice_line.freight_booking.analytic_account_id.id

                        values = {}
                        check_booking = False
                        price_unit = 0
                        freight_currency_rate = 1.000000
                        currency_id = new_invoice_line.freight_currency
                        if new_invoice_line.price_subtotal and (
                                new_invoice_line.price_subtotal > 0 or new_invoice_line.price_subtotal < 0):
                            if invoice.company_id.currency_id != invoice.currency_id:
                                if invoice.exchange_rate_inverse:
                                    price_unit = new_invoice_line.price_unit
                                    freight_currency_rate = invoice.exchange_rate_inverse
                                    currency_id = invoice.currency_id
                                else:
                                    raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                            else:
                                if new_invoice_line.freight_currency_rate != 1:
                                    price_unit = float_round(
                                        new_invoice_line.price_subtotal / new_invoice_line.quantity / new_invoice_line.freight_currency_rate,
                                        2, rounding_method='HALF-UP')
                                else:
                                    price_unit = float_round(
                                        new_invoice_line.price_subtotal / new_invoice_line.quantity, 2,
                                        rounding_method='HALF-UP')
                                freight_currency_rate = new_invoice_line.freight_currency_rate
                                currency_id = new_invoice_line.freight_currency

                            values = {
                                'booking_id': new_invoice_line.freight_booking.id,
                                'product_id': new_invoice_line.product_id.id,
                                'product_name': new_invoice_line.product_id.name,
                                'cost_price': price_unit,
                                'cost_qty': new_invoice_line.quantity,
                                'invoiced': True,
                                'vendor_id': invoice.partner_id.id,
                                'vendor_bill_id': invoice.id,
                                'vendor_bill_ids': [(4, invoice.id)],
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                            }

                        if not new_invoice_line.booking_line_id:
                            # Get C&P
                            booking_cost_profits = self.env['freight.cost_profit'].search([
                                ('booking_id', '=', new_invoice_line.freight_booking.id),
                                ('product_id', '=', new_invoice_line.product_id.id),
                                ('invoiced', '=', False),
                            ])
                            if booking_cost_profits:
                                if len(booking_cost_profits) > 1:
                                    for booking_cost_profit in booking_cost_profits:
                                        other_invoice_line = self.env['account.invoice.line'].search([
                                            ('booking_line_id', '=', booking_cost_profit.id),
                                        ])
                                        if other_invoice_line:
                                            continue
                                        else:
                                            booking_cost_profit.write(values)
                                            new_invoice_line.booking_line_id = booking_cost_profit.id
                                            break
                                else:
                                    booking_cost_profits[0].write(values)
                                    new_invoice_line.booking_line_id = booking_cost_profits[0].id


                            else:
                                cost_profit_line = self.env['freight.cost_profit'].sudo().create(values)
                                new_invoice_line.booking_line_id = cost_profit_line.id

                        else:
                            new_invoice_line.booking_line_id.write({
                                'vendor_bill_id': invoice.id,
                                'vendor_bill_ids': [(4, invoice.id)],
                                'cost_price': price_unit,
                                'cost_qty': new_invoice_line.quantity,
                                'vendor_id': invoice.partner_id.id,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                            })


        return res

    # main purpose is to update the vendor_bill_ids in the cost&profit items
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        for invoice_line in self.invoice_line_ids:
            if invoice_line.booking_line_id and (invoice_line.invoice_type == 'in_invoice' or invoice_line.invoice_type == 'in_refund'):
                if invoice_line.freight_booking:
                    # TS - fix bug (Analytic Account is false when VCN is created) TODO
                    if not invoice_line.freight_booking.analytic_account_id:
                        values = {
                            'partner_id': invoice_line.freight_booking.customer_name.id,
                            'name': '%s' % invoice_line.freight_booking.booking_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        invoice_line.freight_booking.write({'analytic_account_id': analytic_account.id,
                                                            })
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        invoice_line.account_analytic_id = invoice_line.freight_booking.analytic_account_id.id

                    if not self._origin.id:
                        raise exceptions.ValidationError('Please Save the Invoice/Vendor Bill First and Proceed!!!')

        purchase_ids = self.invoice_line_ids.mapped('purchase_id')
        if purchase_ids:
            self.origin = ', '.join(purchase_ids.mapped('name'))
        # TS - this is important to recalculate the Tax, if there is any change to qty, price, etc
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines


class AccountInvoiceLineSingleVendor(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('freight_booking', 'price_subtotal')
    def onchange_freight_booking(self):  # trigger second
        print("Deleted")