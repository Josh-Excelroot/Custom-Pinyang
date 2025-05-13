from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime
from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp


class SaleQuotation(models.Model):
    _inherit = "sale.order"
    show_subtotal = fields.Boolean('Show Total', default=True)
    hide_subtotal = fields.Boolean('Hide Subtotal', default=False)
    show_subtotal_in_line = fields.Boolean('Show Total in Line', default=True)
    show_foreign_currency = fields.Boolean("Show in Foreign Currency", default=False)
    # Yulia 07102024 merge from ion module
    total_sales = fields.Float("Total Sales", compute="_compute_total_sales")
    total_cost = fields.Float("Total Cost", compute="_compute_total_sales")
    total_profit = fields.Float("Total Profit", compute="_compute_total_sales")

    @api.model
    def create(self, vals):
        # Add custom logic before creating the record
        record = super(SaleQuotation, self).create(vals)
        # Add custom logic after creating the record
        return record

    def _report_data(self):
        print()

    # def write(self, vals):
    #     # Custom logic before updating the record
    #
    #     # Call the original write method to perform the update
    #     res = super(SaleQuotation, self).write(vals)
    #
    #     # Custom logic after updating the record
    #
    #     return res



    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleQuotation, self).onchange_partner_id()
        partners_invoice = []
        partners_shipping = []
        domain = {}
        for record in self:
            if record.partner_id:
                record.partner_invoice_id = record.partner_id.id
                record.partner_shipping_id = record.partner_id.id
                if record.partner_id.child_ids:
                    for partner in record.partner_id.child_ids:
                        if partner.type == 'invoice':
                            partners_invoice.append(partner.id)
                        if partner.type == 'delivery':
                            partners_shipping.append(partner.id)
                if partners_invoice:
                    domain['partner_invoice_id'] = [('id', 'in', partners_invoice)]
                else:
                    partners_invoice.append(record.partner_id.id)
                    domain['partner_invoice_id'] = [('id', 'in', partners_invoice)]
                if partners_shipping:
                    domain['partner_shipping_id'] = [('id', 'in', partners_shipping)]
                else:
                    partners_shipping.append(record.partner_id.id)
                    domain['partner_shipping_id'] = [('id', 'in', partners_shipping)]

            else:
                domain['partner_invoice_id'] = [('type', '=', 'invoice')]
                domain['partner_shipping_id'] = [('type', '=', 'delivery')]

        return {'domain': domain}

    @api.multi
    def action_copy_to_booking(self):
        if self.validity_date and self.validity_date < datetime.today().date():
            raise UserError('The Quotation is expired.')
        else:
            booking_obj = self.env['freight.booking']
            cost_profit_obj = self.env['freight.cost_profit']
            freight_booking_val = {
                'shipment_booking_status': '01',
                'customer_name': self.partner_id.id or False,
                'billing_address': self.partner_id.id or False,
                'sq_reference': self.id,
                'company_id': self.company_id.id,
                'sales_person': self.user_id.id,
                'incoterm': self.incoterm.id or False,
                'direction': self.mode or False,
                'port_of_loading': self.POL.id or False,
                'port_of_discharge': self.POD.id or False,
                'commodity1': self.commodity1.id or False,
                'payment_term': self.payment_term_id.id or False,
                'cargo_type': self.type or False,
                'carrier_booking_no': self.carrier_booking_no,
                'contact_name': self.contact_name.id or False,
                'shipper': self.shipper.id or False,
                'forwarding_agent_code': self.forwarding_agent_code.id or False,
                'consignee': self.consignee.id or False,
                'hs_code': self.hs_code.id or False,
                'coo': self.coo,
                'fumigation': self.fumigation,
                'insurance': self.insurance,
                'cpc': self.cpc,
                'warehouse_hours': self.warehouse_hours.id or False,
                'service_type': self.service_type,
                'airport_departure': self.airport_departure.id or False,
                'airport_destination': self.airport_destination.id or False,
                'transporter_company': self.transporter_company.id or False,
            }
            if self.mode == 'import':
                freight_booking_val = {
                    'shipment_booking_status': '01',
                    'customer_name': self.partner_id.id or False,
                    'billing_address': self.partner_id.id or False,
                    'sq_reference': self.id,
                    'company_id': self.company_id.id,
                    'sales_person': self.user_id.id,
                    'incoterm': self.incoterm.id or False,
                    'direction': self.mode or False,
                    'port_of_loading': self.POL.id or False,
                    'port_of_discharge': self.POD.id or False,
                    'commodity1': self.commodity1.id or False,
                    'payment_term': self.payment_term_id.id or False,
                    'cargo_type': self.type or False,
                    'carrier_booking_no': self.carrier_booking_no,
                    'contact_name': self.contact_name.id or False,
                    'shipper': self.shipper.id or False,
                    'forwarding_agent_code': self.forwarding_agent_code.id or False,
                    'hs_code': self.hs_code.id or False,
                    'coo': self.coo,
                    'fumigation': self.fumigation,
                    'insurance': self.insurance,
                    'cpc': self.cpc,
                    'warehouse_hours': self.warehouse_hours.id or False,
                    'consignee': self.partner_id.id or False,
                    'notify_party': self.partner_id.id or False,
                    'service_type': self.service_type,
                    'airport_departure': self.airport_departure.id or False,
                    'airport_destination': self.airport_destination.id or False,
                    'transporter_company': self.transporter_company.id or False,
                }

            booking = booking_obj.create(freight_booking_val)
            if booking.service_type == 'air':
                booking.cargo_type = 'lcl'
                booking.land_cargo_type = 'ltl'
            for line in self.order_line:
                # _logger.warning('action_copy_to_booking 1')
                if line.product_id:
                    # _logger.warning('action_copy_to_booking 2')

                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    else:
                        price_unit = line.price_unit
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'product_name': line.name or False,
                        'booking_id': booking.id or '',
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                        'tax_id': [(6, 0, line.tax_id.ids)],
                        'cost_price': line.cost_price or 0.0,
                        'cost_currency': line.cost_currency.id or False,
                        'cost_currency_rate': line.freight_currency_rate or 1.0,
                    })
                    # booking.write({'booking_id': booking.id or False,
                    #             'cost_profit_ids': cost_profit_line.id or False})
                    booking.write({'cost_profit_ids': cost_profit_line or False})

            self.state = 'sale'

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        # print(">>>>>>>uniship onchange_sale_order_template_id")
        if self.sale_order_template_id:
            if not self._origin.id:
                raise exceptions.ValidationError('Please save the quotation.')
        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            # print(">>>>>>>uniship onchange_sale_order_template_id data1=", data)
            if line.product_id:
                price = line.price_unit
                curr_id = ""

                if  line.currency_id:
                    if line.currency_id != self.env.user.company_id.currency_id:
                        curr_id = line.currency_id
                else:
                    curr_id = self.env.user.company_id.currency_id
                data.update({
                    'price_unit':  price if curr_id == self.env.user.company_id.currency_id else 0,
                    'freight_foreign_price': price if curr_id != self.env.user.company_id.currency_id else 0,
                    'freight_currency':line.currency_id,
                    'cost_currency':line.cost_currency,
                    'discount': 0.00,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'cost_price': line.cost_price,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                    'freight_currency_rate':1,
                    'cost_exc_rate':1
                })
                if self.pricelist_id:
                    data.update(self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id,
                                                                                line.product_uom_id,
                                                                                fields.Date.context_today(self)))
                    # print(">>>>>>>uniship onchange_sale_order_template_id with price list")

            # print(">>>>>>>uniship onchange_sale_order_template_id data2=", data)
            order_lines.append((0, 0, data))

        self.order_line = order_lines
        self.order_line._compute_tax_id()

        option_lines = []
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))
        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.to_string(datetime.now() + timedelta(template.number_of_days))

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if template.note:
            self.note = template.note

    @api.depends('order_line.freight_foreign_price', "order_line.product_uom_qty", "order_line.freight_currency",
                 "order_line.freight_currency_rate", "order_line.cost_price", "order_line.cost_currency",
                 "order_line.price_unit")
    def _compute_total_sales(self):
        for order in self:
            total_sales = total_cost = total_profit = 0

            for line in order.order_line:
                price_sale = line.price_unit * line.product_uom_qty
                total_sales += price_sale
                total_cost += line.cost_price
                total_profit += line.profit
            order.update({
                'total_sales': total_sales,
                "total_cost": total_cost,
                "total_profit": total_profit
            })


class SaleQuotationLine(models.Model):
    _inherit = 'sale.order.line'

    freight_currency_rate = fields.Float(string='Conversion Rate', default="1.000000", track_visibility='onchange',
                                         digits=(12, 6))
    cost_currency = fields.Many2one('res.currency', string='Cost Curr.',
                                    default=lambda self: self.env.user.company_id.currency_id.id,
                                    track_visibility='onchange')
    cost_price = fields.Float(string='Cost Price', track_visibility='onchange')
    vendor = fields.Many2one(
        "res.partner", string="Vendor", domain=[("supplier", "=", True)]
    )

    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'))

    # new field 22Aug24 - YL
    profit = fields.Float(string="Profit", compute='_compute_profit_auto')

    # Yulia 08112024 exc rate for cost
    cost_exc_rate = fields.Float(string="conv. rate", default="1.000000", digits=(12,6))


    @api.depends("freight_currency", "product_uom_qty", "freight_foreign_price", "freight_currency_rate", "cost_price",
                 "cost_currency", "price_unit","cost_exc_rate")
    def _compute_profit_auto(self):
        for record in self:
            if record.freight_foreign_price != 0:
                # record.profit = (
                #                         record.product_uom_qty * record.freight_foreign_price * record.freight_currency_rate) - (
                #                         record.product_uom_qty * record.cost_price * record.freight_currency_rate)
                record.price_unit = record.freight_foreign_price *  record.freight_currency_rate
                record.profit = (
                                        record.product_uom_qty * record.freight_foreign_price * record.freight_currency_rate) - (
                                        record.cost_price * record.cost_exc_rate)
                record.price_subtotal = record.product_uom_qty * record.freight_foreign_price
            else:
                # record.profit = (
                #                         record.product_uom_qty * record.price_unit * record.freight_currency_rate) - (
                #                         record.product_uom_qty * record.cost_price * record.freight_currency_rate)
                record.profit = (
                                        record.product_uom_qty * record.price_unit) - (
                                        record.cost_price * record.cost_exc_rate)
                record.price_subtotal = record.product_uom_qty * record.price_unit

    # @api.onchange("freight_foreign_price")
    # def _onchange_freight_foreign_price(self):
    #     self.price_unit = self.freight_foreign_price * self.freight_currency_rate or 0.0
    #
    # @api.onchange("freight_currency_rate")
    # def _onchange_freight_currency_rate(self):
    #     self.price_unit = self.freight_foreign_price * self.freight_currency_rate or 0.0

    @api.onchange('product_id')
    def _onchange_product_id1(self):
        # res = super(SaleQuotationLine, self)._onchange_product_id()
        name = self.product_id.name
        self.name = name
        # return res

