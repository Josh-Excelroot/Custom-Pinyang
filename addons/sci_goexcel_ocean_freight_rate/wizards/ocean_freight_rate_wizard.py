from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import Warning


class OceanFreightRateWizard(models.TransientModel):
    _inherit = 'charge.wizard'

    service = fields.Selection(selection_add=[('ocean_freight_rate', 'Ocean Freight')])
    ocean_freight_rate_check = fields.Boolean('Ocean Freight Rate', default=True)
    carrier = fields.Many2one('res.partner', string="Carrier")
    container_product_id = fields.Many2one('product.product', string='Container Size')
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge')
    currency = fields.Many2one('res.currency', string="Currency")
    ocean_freight_rate = fields.Float(string='Rate', digits=(12, 2))
    ocean_freight_cost = fields.Float(string='Cost', digits=(12, 2))
    customer = fields.Many2one('res.partner', string='Customer')
    booking_date = fields.Datetime(string='ETA/ETD Date')

    # CR5 - Canon
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name')
    carrier_booking_no = fields.Char(string='Carrier Booking No')

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.model
    def default_get(self, fields):
        ocean_freight_rate_check = self.env['ir.config_parameter'].sudo().get_param(
            'sci_goexcel_ocean_freight_rate.use_ocean_freight_rate')

        result = super(OceanFreightRateWizard, self).default_get(fields)
        sq_id = self.env.context.get('sq_id')
        booking_id = self.env.context.get('booking_id')
        invoice_id = self.env.context.get('invoice_id')

        port_of_loading = False
        port_of_discharge = False
        carrier = False
        customer = False
        container_product_id = False
        booking_date = False
        vessel_name = False
        carrier_booking_no = False

        if sq_id:
            sq = self.env['sale.order'].browse(sq_id)
            port_of_loading = sq.POL.id
            port_of_discharge = sq.POD.id
            carrier = sq.carrier.id
            customer = sq.partner_id
            container_product_id = sq.container_product_id.id
            booking_date = datetime.today().date()

        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            port_of_loading = booking.port_of_loading.id
            port_of_discharge = booking.port_of_discharge.id
            carrier = booking.carrier.id
            customer = booking.customer_name
            container_product_id = booking.container_product_id
            booking_date = booking.booking_date_time
            vessel_name = booking.vessel_name.id
            carrier_booking_no = booking.carrier_booking_no

        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            port_of_loading = invoice.port_of_loading.id
            port_of_discharge = invoice.port_of_discharge.id
            carrier = invoice.carrier.id
            customer = invoice.partner_id
            booking_date = datetime.today()

        current_date = datetime.today()
        ocean_freight_rate = False
        ocean_freight_rate_ids = False
        if customer:
            ocean_freight_rate_ids = self.env['freight.ocean.freight.rate.line'].search(
                [('valid_from', '<=', booking_date), ('valid_to', '>=', booking_date), ('customer', '=', customer.id)])

        rate = 0.00
        cost = 0.00
        if port_of_loading and port_of_discharge:
            port_pair_ids = self.env['freight.port.pair'].search(
                [('port_of_loading', '=', port_of_loading), ('port_of_discharge', '=', port_of_discharge)], limit=1)

        if booking_id and ocean_freight_rate_ids:
            if vessel_name or carrier_booking_no:
                if vessel_name and carrier_booking_no:
                    with_vessel_name_carrier_booking_no = ocean_freight_rate_ids.search([
                        ('vessel_name', '=', vessel_name),('carrier_booking_no', '=', carrier_booking_no)])
                if vessel_name:
                    with_vessel_name = ocean_freight_rate_ids.search([('vessel_name', '=', vessel_name)])
                if carrier_booking_no:
                    with_carrier_booking_no = ocean_freight_rate_ids.search([('carrier_booking_no', '=', carrier_booking_no)])
                if len(with_vessel_name_carrier_booking_no) > 0:
                    ocean_freight_rate_ids = with_vessel_name_carrier_booking_no
                elif len(with_vessel_name) > 0:
                    ocean_freight_rate_ids = with_vessel_name
                elif len(with_carrier_booking_no) > 0:
                    ocean_freight_rate_ids = with_carrier_booking_no
                else:
                    ocean_freight_rate_ids = ocean_freight_rate_ids

        if ocean_freight_rate_ids:
            for i in ocean_freight_rate_ids:
                if port_pair_ids in i.ocean_freight_rate_id.port_pair:
                    if carrier == i.ocean_freight_rate_id.carrier.id and i.ocean_freight_rate_id.state == 'active':
                        rate = i.rate
                        cost = i.cost_rate
        currency = self.env['res.currency'].search([('name', '=', 'USD')])
        # for rec in self:

        # booking_date = booking_date.date()

        result.update({
            'customer': customer or False,
            'port_of_loading': port_of_loading or False,
            'port_of_discharge': port_of_discharge or False,
            'carrier': carrier or False,
            'ocean_freight_rate_check': ocean_freight_rate_check or False,
            'ocean_freight_rate': rate or 0.00,
            'ocean_freight_cost': cost or 0.00,
            'currency': currency.id or False,
            'container_product_id':container_product_id or False,
            'booking_date': booking_date or False,
            'vessel_name': vessel_name or False,
            'carrier_booking_no': carrier_booking_no or False,
        })
        result = self._convert_to_write(result)
        return result

    @api.onchange('service', 'carrier', 'port_of_loading', 'port_of_discharge', 'currency', 'container_product_id')
    def onchange_ocean_freight_rate(self):
        if self.service =='ocean_freight_rate':
            current_date = datetime.today()
            ocean_freight_rate_ids = False

            if self.customer:
                ocean_freight_rate_ids = self.env['freight.ocean.freight.rate.line'].search(
                    [('valid_from', '<=', self.booking_date), ('valid_to', '>=', self.booking_date),
                     ('customer', '=', self.customer.id)])

            self.ocean_freight_rate = 0
            if self.port_of_loading and self.port_of_discharge:
                port_pair_ids = self.env['freight.port.pair'].search(
                    [('port_of_loading', '=', self.port_of_loading.id),
                     ('port_of_discharge', '=', self.port_of_discharge.id)], limit=1)

            check_carrier = False
            check_container = False
            check_state = False
            check_portpair = False
            if ocean_freight_rate_ids:
                if self.vessel_name or self.carrier_booking_no:
                    if self.vessel_name and self.carrier_booking_no:
                        with_vessel_name_carrier_booking_no = ocean_freight_rate_ids.search([
                            ('vessel_name', '=', self.vessel_name.id), ('carrier_booking_no', '=', self.carrier_booking_no)])
                    if self.vessel_name:
                        with_vessel_name = ocean_freight_rate_ids.search([('vessel_name', '=', self.vessel_name.id)])
                    if self.carrier_booking_no:
                        with_carrier_booking_no = ocean_freight_rate_ids.search(
                            [('carrier_booking_no', '=', self.carrier_booking_no)])
                    if len(with_vessel_name_carrier_booking_no) > 0:
                        ocean_freight_rate_ids = with_vessel_name_carrier_booking_no
                    elif len(with_vessel_name) > 0:
                        ocean_freight_rate_ids = with_vessel_name
                    elif len(with_carrier_booking_no) > 0:
                        ocean_freight_rate_ids = with_carrier_booking_no
                    else:
                        ocean_freight_rate_ids = ocean_freight_rate_ids

            if ocean_freight_rate_ids:
                for i in ocean_freight_rate_ids:
                    if port_pair_ids in i.ocean_freight_rate_id.port_pair:
                        check_portpair = True
                        if self.carrier == i.ocean_freight_rate_id.carrier:
                            check_carrier = True
                            if self.container_product_id.id == i.ocean_freight_rate_id.container_product_id.id:
                                check_container = True
                                if i.ocean_freight_rate_id.state == 'active':
                                    check_state = True
                                    self.ocean_freight_rate = i.rate
                                    self.ocean_freight_cost = i.cost_rate
            else:
                raise Warning('No Ocean Freight Rate found. Please check customer and validity date.')

            if ocean_freight_rate_ids:
                if not check_portpair:
                    raise Warning('No Port Pair found.')
                elif not check_carrier:
                    raise Warning('No Carrier found.')
                elif not check_container:
                    raise Warning('No Container found.')
                elif not check_state:
                    raise Warning('No Active Ocean Freight Rate found.')
            

    @api.multi
    def action_ocean_freight_rate(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        booking_id = self.env.context.get('booking_id')
        booking = self.env['freight.booking'].browse(booking_id)
        invoice_id = self.env.context.get('invoice_id')
        invoice = self.env['account.invoice'].browse(invoice_id)

        ocean_freight_rate_product = self.env['product.product'].sudo().search(
            [(
                'id', '=', self.env['ir.config_parameter'].sudo().get_param(
                    'sci_goexcel_ocean_freight_rate.product_ocean_freight_rate'))]
            , limit=1)

        if sq:
            check_product = False
            sale_order_line = self.env['sale.order.line']
            for order in sq.order_line:
                if order.product_id == ocean_freight_rate_product:
                    order.write({'price_unit': self.ocean_freight_rate
                                 })
                    check_product = True
            if not check_product:
                val = {
                    'order_id': sq.id,
                    'name': ocean_freight_rate_product.name,
                    'product_id': ocean_freight_rate_product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.ocean_freight_rate,
                    'freight_currency': self.currency.id,
                }
                sale_order_line.create(val)

        if booking:
            check_product = False
            booking_line = self.env['freight.cost_profit']
            for booking_cost in booking.cost_profit_ids:
                if booking_cost.product_id == ocean_freight_rate_product:
                    booking_cost.write({'list_price': self.ocean_freight_rate,
                                        'profit_currency': self.currency.id,
                                        'cost_price': self.ocean_freight_cost,
                                        'cost_currency': self.currency.id,
                                        'vendor_id': self.carrier.id,
                                        })
                    check_product = True
            if not check_product:
                val = {
                    'booking_id': booking.id,
                    'product_name': ocean_freight_rate_product.name,
                    'product_id': ocean_freight_rate_product.id,
                    #'profit_qty': 1,
                    'list_price': self.ocean_freight_rate,
                    'profit_currency': self.currency.id,
                    'cost_price': self.ocean_freight_cost,
                    'cost_currency': self.currency.id,
                    'vendor_id': self.carrier.id,
                }
                booking_line.create(val)

        if invoice:
            check_product = False
            invoice_line = self.env['account.invoice.line']
            for invoice_cost in invoice.invoice_line_ids:
                if invoice_cost.product_id == ocean_freight_rate_product:
                    invoice_cost.write({'price_unit': self.ocean_freight_rate})
                    check_product = True
            if ocean_freight_rate_product.property_account_income_id:
                account_id = ocean_freight_rate_product.property_account_income_id
            elif ocean_freight_rate_product.categ_id.property_account_income_categ_id:
                account_id = ocean_freight_rate_product.categ_id.property_account_income_categ_id

            if not check_product:
                val = {
                    'invoice_id': invoice.id,
                    'account_id': account_id.id,
                    'name': ocean_freight_rate_product.name,
                    'product_id': ocean_freight_rate_product.id,
                    'quantity': 1,
                    'price_unit': self.ocean_freight_rate,
                    'freight_currency': self.currency.id,
                }
                invoice_line.create(val)
