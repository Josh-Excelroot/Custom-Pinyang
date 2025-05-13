from odoo import api, fields, models
from datetime import datetime


class HaulageChargeWizard(models.TransientModel):
    _inherit = 'charge.wizard'

    service = fields.Selection(selection_add=[('haulage_charge', 'Haulage Charge'),('trucking_service', 'Trucking Service')])
    haulage_charge_check = fields.Boolean('Haulage Charge', default=True)
    trucking_service_check = fields.Boolean('Trucking', default=True)
    carrier = fields.Many2one('res.partner', string="Carrier")
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    place_of_delivery = fields.Many2one('freight.haulage.charge', string='Pick Up/ Delivery To Location')

    currency = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.user.company_id.currency_id.id)

    haulage_charge = fields.Float(string='Haulage Charge', digits=(12, 2))
    haulage_cost = fields.Float(string='Haulage Cost', digits=(12, 2))
    trucking_service_weight = fields.Selection([('01', '1T'),
                                                ('02', '3T'),
                                                ('03', '3T/20'),
                                                ('04', '5T')],
                                               string="Trucking Service Weight", default="01")
    trucking_service_charge = fields.Float(string='Trucking Service Charge', digits=(12, 2))

    @api.multi
    @api.depends("place_of_delivery")
    def _get_vendor_domain(self):
        for obj in self:
            vendor_ids = []
            for line in obj.place_of_delivery.haulage_charge_line_ids:
                for vendor_id in line.vendor_id.ids:
                    vendor_ids.append(vendor_id)
                self.vendor_list = [(6,0, vendor_ids)]

    vendor = fields.Many2one('res.partner', string="Vendor")
    vendor_list = fields.Many2many('res.partner',store=True,compute=_get_vendor_domain)

    @api.model
    def default_get(self, fields):
        haulage_charge_check = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.use_haulage_charge')
        trucking_service_check = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.use_trucking_service')

        result = super(HaulageChargeWizard, self).default_get(fields)
        sq_id = self.env.context.get('sq_id')
        booking_id = self.env.context.get('booking_id')
        invoice_id = self.env.context.get('invoice_id')

        port_of_loading = False
        carrier = False
        currency = self.env.user.company_id.currency_id.id
        #print('>>>> haulage wizard default_get=', self.env.user.company_id.currency_id.name)

        check_haulage_charge = self.env['freight.haulage.charge'].search(
            [('valid_to', '<', datetime.today())])
        for check_haulage_charge_line in check_haulage_charge:
            check_haulage_charge_line.state = 'draft'

        if sq_id:
            sq = self.env['sale.order'].browse(sq_id)
            port_of_loading = sq.POL.id
            carrier = sq.carrier.id
            #currency = sq.currency_id.id

        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            port_of_loading = booking.port_of_loading.id
            carrier = booking.carrier.id
            #currency = self.env.user.company_id.currency_id.id
            
        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            port_of_loading = invoice.port_of_loading.id
            carrier = invoice.carrier.id
            #currency = invoice.currency_id.id

        haulage_charge = False
        if port_of_loading and carrier and currency:
            haulage_charge = self.env['freight.haulage.charge'].search(
                [('carrier.id', '=', carrier), ('port_of_loading.id', '=', port_of_loading),
                 ('valid_from', '>=', datetime.today()),('currency.id', '=', currency), ('state', '=', 'active')], limit=1)

        if haulage_charge:
            haulage_charge_price = haulage_charge.rate
        else:
            haulage_charge_price = 0

        #print('>>>> haulage wizard default_get currency=', currency)
        # for rec in self:
        result.update({'port_of_loading': port_of_loading or False,
                       'carrier': carrier or False,
                       'currency': currency or False,
                       'haulage_charge_check': haulage_charge_check or False,
                       'trucking_service_check': trucking_service_check or False,
                       'haulage_charge': haulage_charge_price,
                       })
        result = self._convert_to_write(result)
        return result

    @api.onchange('service', 'port_of_loading','place_of_delivery','trucking_service_weight')
    def onchange_haulage_charge(self):
        if self.service == 'haulage_charge':
            self.haulage_charge = self.place_of_delivery.total
            self.currency = self.place_of_delivery.currency.id

        if self.service == 'trucking_service':
            if self.trucking_service_weight == '01':
                self.trucking_service_charge = self.place_of_delivery.one_ton
            if self.trucking_service_weight == '02':
                self.trucking_service_charge = self.place_of_delivery.three_ton
            if self.trucking_service_weight == '03':
                self.trucking_service_charge = self.place_of_delivery.three_ton_20
            if self.trucking_service_weight == '04':
                self.trucking_service_charge = self.place_of_delivery.five_ton
        """
        if self.port_of_loading and self.carrier and self.currency:
            haulage_charge = self.env['freight.haulage.charge'].search(
                [('carrier.id', '=', self.carrier.id), ('port_of_loading.id', '=', self.port_of_loading.id),
                 ('port_of_discharge.id', '=', self.port_of_discharge.id), ('valid_from', '<=', datetime.today()),
                 ('container_product_id', '=', self.container_product_id.id),
                 ('currency.id', '=', self.currency.id), ('state', '=', 'active')], limit=1)
            if haulage_charge:
                self.haulage_charge = haulage_charge.rate
        """

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            for line in self.place_of_delivery.haulage_charge_line_ids:
                if self.vendor.id in line.vendor_id.ids:
                    self.haulage_cost = line.cost_after_rebate
                    break


    @api.multi
    def action_haulage(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        booking_id = self.env.context.get('booking_id')
        booking = self.env['freight.booking'].browse(booking_id)
        invoice_id = self.env.context.get('invoice_id')
        invoice = self.env['account.invoice'].browse(invoice_id)

        haulage_charge_product = self.env['product.product'].sudo().search(
            [(
             'id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.haulage_product'))]
            , limit=1)
        #print(haulage_charge_product)
        #print(haulage_charge_product.name)
        if sq:
            check_product = False
            sale_order_line = self.env['sale.order.line']
            for order in sq.order_line:
                if order.product_id == haulage_charge_product:
                    order.write({'price_unit': self.haulage_charge})
                    check_product = True
            if not check_product:
                val = {
                    'order_id': sq.id,
                    'name': haulage_charge_product.name,
                    'product_id': haulage_charge_product.id,
                    #'product_uom_qty': 1,
                    'price_unit': self.haulage_charge,
                }
                sale_order_line.create(val)

        if booking:
            check_product = False
            booking_line = self.env['freight.cost_profit']
            for booking_cost in booking.cost_profit_ids:
                if booking_cost.product_id == haulage_charge_product:
                    booking_cost.write({'list_price': self.haulage_charge,
                                        'cost_price': self.haulage_cost,
                                        'vendor_id': self.vendor.id,
                                            })
                    check_product = True
            if not check_product:
                val = {
                    'booking_id': booking.id,
                    'product_name': haulage_charge_product.name,
                    'product_id': haulage_charge_product.id,
                    'profit_qty': 1,
                    'list_price': self.haulage_charge,
                }
                booking_line.create(val)

        if invoice:
            check_product = False
            invoice_line = self.env['account.invoice.line']
            for invoice_cost in invoice.invoice_line_ids:
                if invoice_cost.product_id == haulage_charge_product:
                    invoice_cost.write({'price_unit': self.haulage_charge})
                    check_product = True
            if haulage_charge_product.property_account_income_id:
                account_id = haulage_charge_product.property_account_income_id
            elif haulage_charge_product.categ_id.property_account_income_categ_id:
                account_id = haulage_charge_product.categ_id.property_account_income_categ_id

            if not check_product:
                val = {
                    'invoice_id': invoice.id,
                    'account_id': account_id.id,
                    'name': haulage_charge_product.name,
                    'product_id': haulage_charge_product.id,
                    'quantity': 1,
                    'price_unit': self.haulage_charge,
                }
                invoice_line.create(val)

    @api.multi
    def action_trucking(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        booking_id = self.env.context.get('booking_id')
        booking = self.env['freight.booking'].browse(booking_id)
        invoice_id = self.env.context.get('invoice_id')
        invoice = self.env['account.invoice'].browse(invoice_id)

        trucking_service_product = self.env['product.product'].sudo().search(
            [(
                'id', '=',
                self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.trucking_product'))]
            , limit=1)

        if sq:
            check_product = False
            sale_order_line = self.env['sale.order.line']
            for order in sq.order_line:
                if order.product_id == trucking_service_product:
                    order.write({'price_unit': self.trucking_service_charge})
                    check_product = True
            if not check_product:
                val = {
                    'order_id': sq.id,
                    'name': trucking_service_product.name,
                    'product_id': trucking_service_product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.trucking_service_charge,
                }
                sale_order_line.create(val)

        if booking:
            check_product = False
            booking_line = self.env['freight.cost_profit']
            for booking_cost in booking.cost_profit_ids:
                if booking_cost.product_id == trucking_service_product:
                    booking_cost.write({'list_price': self.trucking_service_charge})
                    check_product = True
            if not check_product:
                val = {
                    'booking_id': booking.id,
                    'product_name': trucking_service_product.name,
                    'product_id': trucking_service_product.id,
                    'profit_qty': 1,
                    'list_price': self.trucking_service_charge,
                }
                booking_line.create(val)

        if invoice:
            check_product = False
            invoice_line = self.env['account.invoice.line']
            for invoice_cost in invoice.invoice_line_ids:
                if invoice_cost.product_id == trucking_service_product:
                    invoice_cost.write({'price_unit': self.trucking_service_charge})
                    check_product = True
            if trucking_service_product.property_account_income_id:
                account_id = trucking_service_product.property_account_income_id
            elif trucking_service_product.categ_id.property_account_income_categ_id:
                account_id = trucking_service_product.categ_id.property_account_income_categ_id

            if not check_product:
                val = {
                    'invoice_id': invoice.id,
                    'account_id': account_id.id,
                    'name': trucking_service_product.name,
                    'product_id': trucking_service_product.id,
                    'quantity': 1,
                    'price_unit': self.trucking_service_charge,
                }
                invoice_line.create(val)