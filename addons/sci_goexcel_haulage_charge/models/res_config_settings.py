# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_haulage_charge = fields.Boolean(string="Use Haulage Charge")
    use_trucking_service = fields.Boolean(string="Use Trucking Service")

    faf_rate = fields.Float(string='FAF %')
    haulage_product = fields.Many2one('product.product', string='Haulage Charge Product',
                                      config_parameter='sci_goexcel_haulage_charge.haulage_product')
    trucking_product = fields.Many2one('product.product', string='Trucking Product',
                                       config_parameter='sci_goexcel_haulage_charge.trucking_product')

    # Approval
    haulage_charge_approval_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Haulage Charge Approvers", related='company_id.haulage_charge_approval_user_ids',)
    haulage_charge_notification_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Haulage Charge Approval Notification Recipients" , related='company_id.haulage_charge_notification_user_ids',)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        use_haulage_charge = param.get_param('sci_goexcel_haulage_charge.use_haulage_charge')
        use_trucking_service = param.get_param('sci_goexcel_haulage_charge.use_trucking_service')
        res.update(use_haulage_charge=use_haulage_charge,
                   use_trucking_service=use_trucking_service,
                   )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        use_haulage_charge = self.use_haulage_charge or False
        use_trucking_service = self.use_trucking_service or False
        param.set_param('sci_goexcel_haulage_charge.use_haulage_charge', use_haulage_charge)
        param.set_param('sci_goexcel_haulage_charge.use_trucking_service', use_trucking_service)
