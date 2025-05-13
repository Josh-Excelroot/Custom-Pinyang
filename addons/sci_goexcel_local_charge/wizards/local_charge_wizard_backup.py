from odoo import api, fields, models
from datetime import datetime


class LocalChargeWizard(models.TransientModel):
    _inherit = 'charge.wizard'

    service = fields.Selection(selection_add=[('local_charges', 'Local Charges')])
    local_charge_check = fields.Boolean('Local Charge', default=True)

    carrier = fields.Many2one('res.partner', string="Carrier")
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    currency = fields.Many2one('res.currency', string="Currency")

    price_thc = fields.Float(string='THC Charge', digits=(12, 2))
    price_doc_fee = fields.Float(string='Doc Fee Charge', digits=(12, 2))
    price_seal_fee = fields.Float(string='Seal Fee Charge', digits=(12, 2))
    price_edi = fields.Float(string='EDI Charge', digits=(12, 2))
    price_telex_release_charge = fields.Float(string='Telex Release Charge', digits=(12, 2))
    price_obl = fields.Float(string='OBL Charge', digits=(12, 2))
    price_communication = fields.Float(string='Communication Charge', digits=(12, 2))

    @api.model
    def default_get(self, fields):
        local_charge_check = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.use_local_charge')

        result = super(LocalChargeWizard, self).default_get(fields)
        sq_id = self.env.context.get('sq_id')

        booking_id = self.env.context.get('booking_id')
        invoice_id = self.env.context.get('invoice_id')

        price_thc = 0
        price_doc_fee = 0
        price_seal_fee = 0
        price_edi = 0
        price_telex_release_charge = 0
        price_obl = 0
        price_communication = 0

        port_of_loading = False
        carrier = False
        currency = False

        check_local_charge = self.env['freight.local.charge'].search(
            [('valid_to', '<', datetime.today())])
        for check_local_charge_line in check_local_charge:
            check_local_charge_line.state = 'draft'

        if sq_id:
            sq = self.env['sale.order'].browse(sq_id)
            port_of_loading = sq.POL.id
            carrier = sq.carrier.id
            currency = sq.currency_id.id

            if port_of_loading and carrier and currency:
                local_charge = self.env['freight.local.charge'].search(
                    [('carrier.id', '=', carrier), ('port_of_loading.id', '=', port_of_loading),
                     ('currency.id', '=', currency), ('state', '=', 'active')],limit=1)
                if local_charge:
                    price_thc = local_charge.price_thc
                    price_doc_fee = local_charge.price_doc_fee
                    price_seal_fee = local_charge.price_seal_fee
                    price_edi = local_charge.price_edi
                    price_telex_release_charge = local_charge.price_telex_release_charge
                    price_obl = local_charge.price_obl
                    price_communication = local_charge.price_communication

        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            port_of_loading = booking.port_of_loading.id
            carrier = booking.carrier.id
            currency = self.env.user.company_id.currency_id.id

            if port_of_loading and carrier and currency:
                local_charge = self.env['freight.local.charge'].search(
                    [('carrier.id', '=', carrier), ('port_of_loading.id', '=', port_of_loading),
                     ('currency.id', '=', currency), ('state', '=', 'active')],limit=1)
                if local_charge:
                    price_thc = local_charge.price_thc
                    price_doc_fee = local_charge.price_doc_fee
                    price_seal_fee = local_charge.price_seal_fee
                    price_edi = local_charge.price_edi
                    price_telex_release_charge = local_charge.price_telex_release_charge
                    price_obl = local_charge.price_obl
                    price_communication = local_charge.price_communication

        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            port_of_loading = invoice.port_of_loading.id
            carrier = invoice.carrier.id
            currency = invoice.currency_id.id

            if port_of_loading and carrier and currency:
                local_charge = self.env['freight.local.charge'].search(
                    [('carrier.id', '=', carrier), ('port_of_loading.id', '=', port_of_loading),
                     ('currency.id', '=', currency), ('state', '=', 'active')],limit=1)
                if local_charge:
                    price_thc = local_charge.price_thc
                    price_doc_fee = local_charge.price_doc_fee
                    price_seal_fee = local_charge.price_seal_fee
                    price_edi = local_charge.price_edi
                    price_telex_release_charge = local_charge.price_telex_release_charge
                    price_obl = local_charge.price_obl
                    price_communication = local_charge.price_communication

        # for rec in self:
        result.update({'port_of_loading': port_of_loading or False,
                       'carrier': carrier or False,
                       'currency': currency or False,
                       'local_charge_check': local_charge_check or False,
                       'price_thc': price_thc,
                       'price_doc_fee': price_doc_fee,
                       'price_seal_fee': price_seal_fee,
                       'price_edi': price_edi,
                       'price_telex_release_charge': price_telex_release_charge,
                       'price_obl': price_obl,
                       'price_communication': price_communication,
                       })
        result = self._convert_to_write(result)
        return result

    @api.onchange('service', 'carrier', 'port_of_loading', 'currency')
    def onchange_local_charge(self):
        if self.port_of_loading and self.carrier and self.currency:
            local_charge = self.env['freight.local.charge'].search(
                [('carrier.id', '=', self.carrier.id), ('port_of_loading.id', '=', self.port_of_loading.id),
                 ('currency.id', '=', self.currency.id), ('state', '=', 'active')],limit=1)
            if local_charge:
                self.price_thc = local_charge.price_thc
                self.price_doc_fee = local_charge.price_doc_fee
                self.price_seal_fee = local_charge.price_seal_fee
                self.price_edi = local_charge.price_edi
                self.price_telex_release_charge = local_charge.price_telex_release_charge
                self.price_obl = local_charge.price_obl
                self.price_communication = local_charge.price_communication
            else:
                self.price_thc = 0
                self.price_doc_fee = 0
                self.price_seal_fee = 0
                self.price_edi = 0
                self.price_telex_release_charge = 0
                self.price_obl = 0
                self.price_communication = 0
        else:
            self.price_thc = 0
            self.price_doc_fee = 0
            self.price_seal_fee = 0
            self.price_edi = 0
            self.price_telex_release_charge = 0
            self.price_obl = 0
            self.price_communication = 0



    @api.multi
    def action_local_charge(self):
        product_thc = self.env['product.product'].sudo().search(
            [('id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_thc'))], limit=1)
        product_doc_fee = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_doc_fee'))], limit=1)
        product_seal_fee = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_seal_fee'))], limit=1)
        product_edi = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_edi'))], limit=1)
        product_telex_release_charge = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_telex_release_charge'))], limit=1)
        product_obl = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_obl'))], limit=1)
        product_communication = self.env['product.product'].sudo().search(
            [('id', '=',
              self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_local_charge.product_communication'))], limit=1)

        sq_id = self.env.context.get('sq_id')
        sq = self.env['sale.order'].browse(sq_id)
        if sq:
            sale_order_line = self.env['sale.order.line']
            check_product_thc = False
            check_product_doc_fee = False
            check_product_seal_fee = False
            check_product_edi = False
            check_product_telex_release_charge = False
            check_product_obl = False
            check_product_communication = False

            for order in sq.order_line:
                if order.product_id == product_thc:
                    order.write({'price_unit': self.price_thc})
                    check_product_thc = True
                if order.product_id == product_doc_fee:
                    order.write({'price_unit': self.price_doc_fee})
                    check_product_doc_fee = True
                if order.product_id == product_seal_fee:
                    order.write({'price_unit': self.price_seal_fee})
                    check_product_seal_fee = True
                if order.product_id == product_edi:
                    order.write({'price_unit': self.price_edi})
                    check_product_edi = True
                if order.product_id == product_telex_release_charge:
                    order.write({'price_unit': self.price_telex_release_charge})
                    check_product_telex_release_charge = True
                if order.product_id == product_obl:
                    order.write({'price_unit': self.price_obl})
                    check_product_obl = True
                if order.product_id == product_communication:
                    order.write({'price_unit': self.price_communication})
                    check_product_communication = True

            if not check_product_thc:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_thc.name,
                    'product_id': product_thc.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_thc,
                })

            if not check_product_doc_fee:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_doc_fee.name,
                    'product_id': product_doc_fee.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_doc_fee,
                })

            if not check_product_seal_fee:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_seal_fee.name,
                    'product_id': product_seal_fee.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_seal_fee,
                })

            if not check_product_edi:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_edi.name,
                    'product_id': product_edi.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_edi,
                })

            if not check_product_telex_release_charge:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_telex_release_charge.name,
                    'product_id': product_telex_release_charge.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_telex_release_charge,
                })

            if not check_product_obl:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_obl.name,
                    'product_id': product_obl.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_obl,
                })

            if not check_product_communication:
                order_list = sale_order_line.create({
                    'order_id': sq.id,
                    'name': product_communication.name,
                    'product_id': product_communication.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price_communication,
                })





