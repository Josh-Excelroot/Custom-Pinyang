# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_ocean_freight_rate = fields.Boolean(string="Use Ocean Freight Rate")
    product_ocean_freight_rate = fields.Many2one(
        'product.product', string='Ocean Freight Rate Product', config_parameter='sci_goexcel_ocean_freight_rate.product_ocean_freight_rate')

    # Approval
    ocean_freight_rate_approval_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Ocean Freight Rate Approvers", related='company_id.ocean_freight_rate_approval_user_ids',)
    ocean_freight_rate_notification_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Ocean Freight Rate Approval Notification Recipients" , related='company_id.ocean_freight_rate_notification_user_ids',)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        use_ocean_freight_rate = param.get_param('sci_goexcel_ocean_freight_rate.use_ocean_freight_rate')
        res.update(use_ocean_freight_rate=use_ocean_freight_rate,
                   )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        use_ocean_freight_rate = self.use_ocean_freight_rate or False
        param.set_param('sci_goexcel_ocean_freight_rate.use_ocean_freight_rate', use_ocean_freight_rate)
