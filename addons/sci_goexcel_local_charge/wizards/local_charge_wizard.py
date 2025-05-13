from distutils import extension

from odoo import api, fields, models
from datetime import datetime


class LocalChargeWizard(models.TransientModel):
    _inherit = 'charge.wizard'

    service = fields.Selection(selection_add=[('local_charges', 'Local Charges')])
    local_charge_check = fields.Boolean('Local Charge', default=True)

    carrier = fields.Many2one('res.partner', string="Carrier")
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    currency = fields.Many2one('res.currency', string="Currency",
                               default=lambda self: self.env.user.company_id.currency_id.id)
    # currency = fields.Many2one('res.currency', string="Currency")
    local_charge_line_ids = fields.One2many('charge.wizard.line', 'local_charge_id', string="Local Charge Line")

    @api.model
    def default_get(self, fields):
        local_charge_check = self.env['ir.config_parameter'].sudo().get_param(
            'sci_goexcel_local_charge.use_local_charge')

        result = super(LocalChargeWizard, self).default_get(fields)
        sq_id = self.env.context.get('sq_id')
        booking_id = self.env.context.get('booking_id')
        invoice_id = self.env.context.get('invoice_id')


        # sale_id = self.env.context.get('sale.order.line')

        port_of_loading = False
        carrier = False
        currency = self.env.user.company_id.currency_id.id

        check_local_charge = self.env['freight.local.charge'].search(
            [('valid_to', '>', datetime.today())])

        for check_local_charge_line in check_local_charge:
            check_local_charge_line.state = 'active'
            print("freight.local.charge")
            print(check_local_charge_line.carrier.id)
            print(check_local_charge_line.currency.id)
            print(check_local_charge_line.port_of_loading.id)

        if sq_id:
            sq = self.env['sale.order'].browse(sq_id)
            port_of_loading = sq.POL.id
            carrier = sq.carrier.id
            currency = sq.currency_id.id

        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            port_of_loading = booking.port_of_loading.id
            carrier = booking.carrier.id
            currency = self.env.user.company_id.currency_id.id

        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            port_of_loading = invoice.port_of_loading.id
            carrier = invoice.carrier.id
            currency = invoice.currency_id.id
        local_charge_list = []

        if port_of_loading and carrier and currency:
            local_charge = self.env['freight.local.charge'].search(
                [('carrier.id', '=', carrier), ('port_of_loading.id', '=', port_of_loading),
                 ('currency.id', '=', currency), ('state', '=', 'active')], limit=1)

            # print("Local_Charge", local_charge)
            # for j in local_charge.local_charge_line_ids:
            #     print(j.product_id)
            #     print(j.cost_price)
            #     print(j.price)

            #  print("Hussain")

            for local_charge_line in local_charge.local_charge_line_ids:
                #    print("Quizilbash")
                #    print(local_charge_line.product_id.id)
                #   print(local_charge_line.price)
                #   print(local_charge_line.cost_price)
                local_charge_list.append({
                    'product_id': local_charge_line.product_id.id,
                    'price': local_charge_line.price,
                    'cost_price': local_charge_line.cost_price,
                })

        # for rec in self:
        result.update({'port_of_loading': port_of_loading or False,
                       'carrier': carrier or False,
                       'currency': currency or False,
                       'local_charge_check': local_charge_check or False,
                       })
        result['local_charge_line_ids'] = local_charge_list
        result = self._convert_to_write(result)

        #
        # print(result.carrier.id)
        # #self.carrier = sq.carrier
        # #self.port_of_loading = sq.POL
        # print(self.port_of_loading.id)
        # #self.currency   = sq.currency_id
        # print(self.currency.id)

        # print(check_local_charge.cost_price)

        return result

    @api.onchange('service', 'carrier', 'port_of_loading', 'currency')
    def onchange_local_charge(self):
        if self.port_of_loading and self.carrier and self.currency:
            local_charge = self.env['freight.local.charge'].search(
                [('carrier.id', '=', self.carrier.id), ('port_of_loading.id', '=', self.port_of_loading.id),
                 ('valid_to', '>=', datetime.now().date()), ('state', '=', 'active')], limit=1)
            if local_charge:
                self.currency=local_charge.currency.id
                local_charge_list = []
                for local_charge_line in local_charge.local_charge_line_ids:
                    local_charge_list.append({
                        'product_id': local_charge_line.product_id.id,
                        'price': local_charge_line.price,
                        'cost_price': local_charge_line.cost_price,

                    })
                self.local_charge_line_ids = [(6, 0, [])]
                self.local_charge_line_ids = local_charge_list
        # MH Auto Update Carrier Port of loading
        # search([('id', '!=', 0)])

        # if self.port_of_loading and self.carrier :
        #     # name = self.env['sale.order'].search(
        #     #     [('carrier.id', '=', self.carrier.id), ('POL.id', '=', self.port_of_loading.id)]
        #     #     , limit=1)
        #     #
        # name = self.env['sale.order'].search(['carrier', '=', self.carrier.id])
        # print(name.carrier)
        # # name = self.env['sale.order.line'].search([("id", "=", self.order_id)])

        # self.carrier.id = name.carrier
        # print(self.carrier.id)
        # #('port_of_loading.id', '=', self.port_of_loading
        # self.port_of_loading.id = name.port_of_loading
        # print(self.port_of_loading.id)

    @api.multi
    def action_local_charge(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        booking_id = self.env.context.get('booking_id')
        booking = self.env['freight.booking'].browse(booking_id)
        invoice_id = self.env.context.get('invoice_id')
        invoice = self.env['account.invoice'].browse(invoice_id)

        if sq:
            sale_order_line = self.env['sale.order.line']
            checked_list = []
            for order in sq.order_line:
                for local_charge in self.local_charge_line_ids:
                    if order.product_id == local_charge.product_id:
                        checked_list.append(local_charge.product_id.id)
                        print("sale_order_line_product_id", local_charge.product_id.id)
                        order.write({'price_unit': local_charge.price})
                        order.write({'cost_price': local_charge.cost_price})
            for local_charge1 in self.local_charge_line_ids:
                if local_charge1.product_id.id not in checked_list:
                    val = {
                        'order_id': sq.id,
                        'name': local_charge1.product_id.name,
                        'product_id': local_charge1.product_id.id,
                        'product_uom_qty': 1,
                        'price_unit': local_charge1.price,
                        'cost_price': local_charge1.cost_price,
                        'freight_currency': self.currency.id,
                    }
                    sale_order_line.create(val)
        if booking:
            booking_line = self.env['freight.cost_profit']
            checked_list = []
            for booking_cost in booking.cost_profit_ids:
                for local_charge in self.local_charge_line_ids:
                    if booking_cost.product_id == local_charge.product_id:
                        checked_list.append(local_charge.product_id.id)
                        booking_cost.write({'list_price': local_charge.price})
            for local_charge1 in self.local_charge_line_ids:
                if local_charge1.product_id.id not in checked_list:
                    # print(local_charge1.product_id.name)
                    # print(local_charge1.price)
                    val = {
                        'booking_id': booking.id,
                        'product_name': local_charge1.product_id.name,
                        'product_id': local_charge1.product_id.id,
                        'profit_qty': 1,
                        'list_price': local_charge1.price,
                        'profit_currency': self.currency.id,
                        'cost_qty': 1,
                        'cost_price': local_charge1.cost_price,
                        'cost_currency': self.currency.id,
                    }
                    booking_line.create(val)
        if invoice:
            invoice_line = self.env['account.invoice.line']
            checked_list = []
            for invoice_cost in invoice.invoice_line_ids:
                for local_charge in self.local_charge_line_ids:
                    if invoice_cost.product_id == local_charge.product_id:
                        checked_list.append(local_charge.product_id.id)
                        invoice_cost.write({'price_unit': local_charge.price})
                        invoice_cost.write({'cost_price': local_charge.cost_price})
            for local_charge1 in self.local_charge_line_ids:
                if local_charge1.product_id.id not in checked_list:
                    if local_charge1.product_id.property_account_income_id:
                        account_id = local_charge1.product_id.property_account_income_id
                    elif local_charge1.product_id.categ_id.property_account_income_categ_id:
                        account_id = local_charge1.product_id.categ_id.property_account_income_categ_id
                    val = {
                        'invoice_id': invoice.id,
                        'account_id': account_id.id,
                        'name': local_charge1.product_id.name,
                        'product_id': local_charge1.product_id.id,
                        'quantity': 1,
                        'price_unit': local_charge1.price,
                        'cost_price': local_charge1.cost_price,
                        'freight_currency': self.currency.id,
                    }
                    invoice_line.create(val)


class LocalChargeWizardLine(models.TransientModel):
    _inherit = 'charge.wizard.line'

    local_charge_id = fields.Many2one('charge.wizard', string='Local Charge', required=True, ondelete='cascade',
                                      index=True, copy=False)

    product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    price = fields.Float(string='Selling Price', digits=(12, 2), track_visibility='onchange')
    cost_price = fields.Float(string='Cost Price', digits=(12, 2), track_visibility='onchange')
