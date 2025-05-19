from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class InvoiceWizard1(models.TransientModel):
    _inherit = "invoice.wizard"

    pricelist_currency = fields.Many2one('res.currency', required=True)

    @api.multi
    def action_create_invoice(self):
        if self.booking_no:
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no),
                                                          ('shipment_booking_status', '!=', '09')], limit=1)
            create_invoice = False
            for booking_line in self.cost_profit_ids:
                if booking_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the freight."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                if booking.service_type == "land":
                    invoice_type = "lorry"
                else:
                    invoice_type = "without_lorry"
                salesperson_id = False
                if self.customer_name.user_id:
                    salesperson_id = self.customer_name.user_id.id
                elif booking.sales_person:
                    salesperson_id = booking.sales_person.id
                inv_currency_id = self.env.user.company_id.currency_id.id
                inv_currency_name = self.env.user.company_id.currency_id.name
                if self.pricelist_currency:
                    inv_currency_id = self.pricelist_currency.id
                    inv_currency_name = self.pricelist_currency.name
                sale_currency_rate = 1.000000
                apply_manual_currency_exchange = False
                if self.cost_profit_ids and inv_currency_name != self.env.user.company_id.currency_id.name:
                    apply_manual_currency_exchange = True
                    for cp_line in self.cost_profit_ids:
                        if cp_line.add_to_invoice and cp_line.booking_line_id.profit_currency.id == inv_currency_id:
                            sale_currency_rate = cp_line.booking_line_id.profit_currency_rate
                            break
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': self.customer_name.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': booking.booking_no,
                    'freight_booking': booking.id,
                    'account_id': self.customer_name.property_account_receivable_id.id or False,
                    'company_id': booking.company_id.id,
                    'user_id': salesperson_id,
                    'invoice_type': invoice_type,
                    'invoice_description': self.container_product_name,
                    'currency_id': inv_currency_id,
                    'exchange_rate_inverse': sale_currency_rate,
                    'apply_manual_currency_exchange': apply_manual_currency_exchange,
                }
                invoice = inv_obj.create(inv_val)
                for booking_line in self.cost_profit_ids:
                    if booking_line.add_to_invoice:
                        line_item = booking_line.cost_profit_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.list_price * line_item.profit_currency_rate
                        # fixed by zaman
                        account_id = False
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        uom_id = False
                        if line_item.uom_id:
                            uom_id = line_item.uom_id.id
                        else:
                            uom_id = line_item.product_id.uom_id.id
                        currency_rate = line_item.profit_currency_rate
                        if inv_currency_id != self.env.user.company_id.currency_id.id:
                            if line_item.profit_currency != self.env.user.company_id.currency_id:
                                currency_rate = currency_rate / sale_currency_rate
                            else:
                                if line_item.profit_currency_rate != 1:
                                    currency_rate = line_item.profit_currency_rate
                                else:
                                    currency_rate = 1 / sale_currency_rate

                            sale_unit_price_converted = line_item.list_price * currency_rate

                        if account_id:
                            # Ahmad Zaman - 21/8/24 - Added Fiscal Position (B2B Exemption) Support
                            fiscal_position = line_item.booking_id.customer_name.property_account_position_id
                            inv_line_tax = False
                            if fiscal_position:
                                tax_mapping = fiscal_position.tax_ids.filtered(
                                    lambda x: x.tax_src_id.id == line_item.tax_id.id)
                                if tax_mapping:
                                    inv_line_tax = tax_mapping[
                                        0].tax_dest_id.ids
                                else:
                                    inv_line_tax = line_item.tax_id.ids
                            else:
                                inv_line_tax = line_item.tax_id.ids

                            if sale_unit_price_converted > 0:
                                inv_line = inv_line_obj.with_context(create_from_job=True).create({
                                    'booking_line_id': line_item.id or False,
                                    'freight_booking': line_item.booking_id.id or False,
                                    'invoice_id': invoice.id or False,
                                    'account_id': account_id.id or False,
                                    'name': line_item.product_name or '',
                                    'product_id': line_item.product_id.id or False,
                                    'quantity': line_item.profit_qty or 0.0,
                                    'freight_currency': line_item.profit_currency.id or False,
                                    'freight_foreign_price': line_item.list_price or 0.00,
                                    'freight_currency_rate': float_round(currency_rate, 6, rounding_method='HALF-UP') or 1.000000,
                                    'uom_id': uom_id or False,
                                    'price_unit': float_round(sale_unit_price_converted, 6, rounding_method='HALF-UP') or 0.00,
                                    'account_analytic_id': booking.analytic_account_id.id or False,
                                    'invoice_line_tax_ids': [(6, 0, inv_line_tax)],
                                    'origin': booking.booking_no,
                                })
                                line_item.write({'invoice_id': invoice.id or False,
                                                 'inv_line_id': inv_line.id or False})

                        else:
                            raise ValidationError(
                                _('Please check the income/expense account for the product: %s') % line_item.product_id.name)
                invoice.compute_taxes()
            for check_line in booking.cost_profit_ids:
                if check_line.added_to_invoice:
                    booking.invoice_status = '03'
                else:
                    booking.invoice_status = '02'

        if self.bl_no:
            bl = self.env['freight.bol'].search([('bol_no', '=', self.bl_no)])
            create_invoice = False
            for bl_line in self.cost_profit_bl_ids:
                if bl_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the freight."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                if bl.service_type == "land":
                    invoice_type = "lorry"
                else:
                    invoice_type = "without_lorry"
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': self.customer_name.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': bl.bol_no,
                    'freight_booking': bl.booking_ref.id,
                    'account_id': self.customer_name.property_account_receivable_id.id or False,
                    'company_id': bl.company_id.id,
                    'user_id': bl.sales_person.id,
                    'invoice_type': invoice_type,
                    'invoice_description': self.container_product_name,
                    'freight_bol': bl.id or False
                }
                invoice = inv_obj.create(inv_val)
                for bl_line in self.cost_profit_bl_ids:
                    if bl_line.add_to_invoice:
                        line_item = bl_line.cost_profit_bl_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.list_price * line_item.profit_currency_rate
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        uom_id = False
                        if line_item.uom_id:
                            uom_id = line_item.uom_id.id
                        else:
                            uom_id = line_item.product_id.uom_id.id
                        if sale_unit_price_converted > 0:
                            inv_line = inv_line_obj.with_context(create_from_job=True).create({
                                'bl_line_id': line_item.id or False,
                                'invoice_id': invoice.id or False,
                                'account_id': account_id.id or False,
                                'name': line_item.product_name or '',
                                'product_id': line_item.product_id.id or False,
                                'quantity': line_item.profit_qty or 0.0,
                                'uom_id': uom_id or False,
                                'price_unit': sale_unit_price_converted or 0.0,
                                'account_analytic_id': bl.analytic_account_id.id or False,
                                'invoice_line_tax_ids': [(6, 0, line_item.tax_id.ids)],
                                'origin': bl.bol_no,
                            })
                            line_item.write({'invoice_id': invoice.id or False,
                                             'inv_line_id': inv_line.id or False})
                invoice.compute_taxes()
            for check_line in bl.cost_profit_ids:
                if check_line.added_to_invoice:
                    bl.invoice_status = '03'
                else:
                    bl.invoice_status = '02'

    @api.model
    def default_get(self, fields):
        # print('in default_get')
        result = super(InvoiceWizard1, self).default_get(fields)
        booking_id = self.env.context.get('booking_id')
        bl_id = self.env.context.get('bl_id')
        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            result['pricelist_currency'] = booking.customer_name.property_product_pricelist.currency_id.id
            if not booking.analytic_account_id:
                values = {
                    'partner_id': booking.customer_name.id,
                    'name': '%s' % booking.booking_no,
                    'code': booking.booking_no,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                booking.write({'analytic_account_id': analytic_account.id,
                               })

            # for rec in self:
            result.update({'customer_name': booking.customer_name.id,
                           'booking_no': booking.booking_no,
                           })
            booking_list = []
            for booking_line in booking.cost_profit_ids:
                if not booking_line.added_to_invoice:
                    booking_list.append({
                        'booking_line_id': booking_line.id,
                        'product_id': booking_line.product_id,
                        'product_name': booking_line.product_name,
                        'list_price': booking_line.list_price,
                        'profit_qty': booking_line.profit_qty,
                        'sale_total': booking_line.sale_total,
                        'sale_currency_rate': booking_line.profit_currency_rate,
                        'cost_profit_line': booking_line,
                        'analytic_account_id': booking.analytic_account_id,
                    })

            if booking.cargo_type == 'fcl':
                if booking.operation_line_ids:
                    result.update({'container_product_name': booking.operation_line_ids[0].container_product_name})

            if booking.cargo_type == 'lcl':
                if booking.operation_line_ids2:
                    result.update({'container_product_name': booking.operation_line_ids2[0].container_product_name})

            result['cost_profit_ids'] = booking_list
            result = self._convert_to_write(result)

        elif bl_id:
            bl = self.env['freight.bol'].browse(bl_id)
            print('in default_get BL=', bl)
            if not bl.analytic_account_id:
                values = {
                    # 'partner_id': bl.customer_name.id,
                    # 'name': '%s' % bl.booking_ref.booking_no,
                    'code': bl.booking_ref.booking_no,
                    # 'company_id': self.env.user.company_id.id,
                    'name': '%s' % bl.bol_no,
                    'partner_id': bl.customer_name.id,
                    # 'partner_id': self.customer_name.id,
                    'company_id': bl.booking_ref.company_id.id,
                }
                if not bl.booking_ref.analytic_account_id:
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    # bl.booking_ref.write({'analytic_account_id': analytic_account.id})
                    bl.write({'analytic_account_id': analytic_account.id,
                              })
                else:
                    bl.write({'analytic_account_id': bl.analytic_account_id.id,
                              })

            # for rec in self:
            result.update({'customer_name': bl.customer_name.id,
                           'bl_no': bl.bol_no,
                           })
            bl_list = []
            for bl_line in bl.cost_profit_ids:
                if not bl_line.added_to_invoice:
                    bl_list.append({
                        'bl_line_id': bl_line.id,
                        'product_id': bl_line.product_id,
                        'list_price': bl_line.list_price,
                        'profit_qty': bl_line.profit_qty,
                        'sale_total': bl_line.sale_total,
                        'cost_profit_bl_line': bl_line,
                        'analytic_account_id': bl.analytic_account_id.id,
                    })

            if bl.cargo_line_ids:
                result.update({'container_product_name': bl.cargo_line_ids[0].container_product_name})

            result['cost_profit_bl_ids'] = bl_list
            result = self._convert_to_write(result)
        # print(result)
        return result


class InvoiceWizardLine(models.TransientModel):
    _inherit = "invoice.wizard.line"

    sale_currency_rate = fields.Float(string='Rate', digits=(12, 6))
    product_name = fields.Text(string="Product Name")