# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    air_freight_rate_product = fields.Many2one('product.product', string='Air Freight Rate Product',
                                      config_parameter='sci_goexcel_freight_2.air_freight_rate_product')
    consolidation_freight_rate_product = fields.Many2one('product.product', string='Consol. Ocean Rate Product',
                                       config_parameter='sci_goexcel_freight_2.consolidation_freight_rate_product')
    cbm_uom = fields.Many2one('uom.uom', string='Cm UoM', config_parameter='sci_goexcel_freight_2.cbm_uom')
    inc_uom = fields.Many2one('uom.uom', string='Inches UoM', config_parameter='sci_goexcel_freight_2.inc_uom')
    send_si = fields.Boolean(string="Send Booking Conf. with SI Excel?", default=False)

    air_freight = fields.Many2one("product.product", string="Air Freight Product" , config_parameter='sci_goexcel_freight_2.air_freight_product' )


    def set_values(self):
        """Override set_values to update the is_air_freight_product field"""
        super(ResConfigSettings, self).set_values()

        # Clear the `is_air_freight_product` flag on all products
        self.env['product.product'].search([('is_air_freight_product', '=', True)]).write({
            'is_air_freight_product': False
        })

        # Set the selected product's `is_air_freight_product` flag to True
        if self.air_freight:
            self.air_freight.is_air_freight_product = True

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     param = self.env['ir.config_parameter'].sudo()
    #     use_haulage_charge = param.get_param('sci_goexcel_haulage_charge.use_haulage_charge')
    #     use_trucking_service = param.get_param('sci_goexcel_haulage_charge.use_trucking_service')
    #     res.update(use_haulage_charge=use_haulage_charge,
    #                use_trucking_service=use_trucking_service,
    #                )
    #     return res

    # @api.multi
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     param = self.env['ir.config_parameter'].sudo()
    #     use_haulage_charge = self.use_haulage_charge or False
    #     use_trucking_service = self.use_trucking_service or False
    #     param.set_param('sci_goexcel_haulage_charge.use_haulage_charge', use_haulage_charge)
    #     param.set_param('sci_goexcel_haulage_charge.use_trucking_service', use_trucking_service)
