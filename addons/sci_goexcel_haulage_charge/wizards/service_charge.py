from odoo import api, fields, models


class ServiceChargeWizard(models.TransientModel):
    _name = 'service.charge.wizard'

    service = fields.Selection([('01', 'Haulage'), ('02', 'Trucking')],
                               string='Service', default='01')

    haulage_service_check = fields.Boolean('Haulage', default=True)
    trucking_service_check = fields.Boolean('Trucking', default=True)

    pick_up_from = fields.Many2one('freight.ports', string='Pick Up From')
    place_of_delivery = fields.Many2one('freight.haulage.charge', string='Place of Delivery')

    haulage_charge = fields.Float(string='Haulage Charge')
    trucking_service_weight = fields.Selection([('01', '1T'),
                                                ('02', '3T'),
                                                ('03', '3T/20'),
                                                ('04', '5T')],
                                               string="Trucking Service Weight", default="01")
    trucking_service_charge = fields.Float(string='Trucking Service Charge')

    @api.model
    def default_get(self, fields):
        haulage_service_check = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.use_haulage_charge')
        trucking_service_check = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.use_trucking_service')

        result = super(ServiceChargeWizard, self).default_get(fields)
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        # for rec in self:
        result.update({'pick_up_from': sq.POL.id or False,
                       'haulage_service_check': haulage_service_check or False,
                       'trucking_service_check': trucking_service_check or False,
                       })
        result = self._convert_to_write(result)
        return result

    @api.onchange('service', 'pick_up_from', 'place_of_delivery','trucking_service_weight')
    def onchange_service(self):
        if self.service == '01':
            self.haulage_charge = self.place_of_delivery.total
        if self.service == '02':
            if self.trucking_service_weight == '01':
                self.trucking_service_charge = self.place_of_delivery.one_ton
            if self.trucking_service_weight == '02':
                self.trucking_service_charge = self.place_of_delivery.three_ton
            if self.trucking_service_weight == '03':
                self.trucking_service_charge = self.place_of_delivery.three_ton_20
            if self.trucking_service_weight == '04':
                self.trucking_service_charge = self.place_of_delivery.five_ton

    @api.multi
    def action_haulage(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        haulage_charge = self.env['product.product'].sudo().search(
            [('id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.haulage_product'))]
            , limit=1)
        sale_order_line = sq.env['sale.order.line']
        check_product = False
        for order in sq.order_line:
            if order.product_id == haulage_charge:
                order.write({'product_uom_qty': 1,
                             'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                             'price_unit': self.haulage_charge,
                             })
                check_product = True
        if not check_product:
            order_list = sale_order_line.create({
                'order_id': self.id,
                'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                'product_id': haulage_charge.id,
                'product_uom_qty': 1,
                'price_unit': self.haulage_charge,
            })

    @api.multi
    def action_haulage(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        haulage_charge = self.env['product.product'].sudo().search(
            [('id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.haulage_product'))]
            , limit=1)
        sale_order_line = self.env['sale.order.line']
        check_product = False
        for order in sq.order_line:
            if order.product_id == haulage_charge:
                order.write({'product_uom_qty': 1,
                             'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                             'price_unit': self.haulage_charge,
                             })
                check_product = True
        if not check_product:
            order_list = sale_order_line.create({
                'order_id': sq.id,
                'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                'product_id': haulage_charge.id,
                'product_uom_qty': 1,
                'price_unit': self.haulage_charge,
            })

    @api.multi
    def action_trucking(self):
        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        trucking_service = self.env['product.product'].sudo().search(
            [('id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.trucking_product'))]
            , limit=1)
        sale_order_line = self.env['sale.order.line']
        check_product = False
        for order in sq.order_line:
            if order.product_id == trucking_service:
                order.write({'product_uom_qty': 1,
                             'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                             'price_unit': self.trucking_service_charge,
                             })
                check_product = True
        if not check_product:
            order_list = sale_order_line.create({
                'order_id': sq.id,
                'name': self.pick_up_from.name + ' to ' + self.place_of_delivery.name,
                'product_id': trucking_service.id,
                'product_uom_qty': 1,
                'price_unit': self.trucking_service_charge,
            })