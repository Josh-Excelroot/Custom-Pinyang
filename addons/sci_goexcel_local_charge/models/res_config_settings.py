# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_local_charge = fields.Boolean(string="Use Local Charge")
    """
    product_thc = fields.Many2one(
        'product.product', string='Product THC', config_parameter='sci_goexcel_local_charge.product_thc')
    product_doc_fee = fields.Many2one(
        'product.product', string='Product Doc Fee', config_parameter='sci_goexcel_local_charge.product_doc_fee')
    product_seal_fee = fields.Many2one(
        'product.product', string='Product Seal Fee', config_parameter='sci_goexcel_local_charge.product_seal_fee')
    product_edi = fields.Many2one(
        'product.product', string='Product EDI', config_parameter='sci_goexcel_local_charge.product_edi')
    product_telex_release_charge = fields.Many2one(
        'product.product', string='Product Telex Release Charge',
        config_parameter='sci_goexcel_local_charge.product_telex_release_charge')
    product_obl = fields.Many2one(
        'product.product', string='Product OBL', config_parameter='sci_goexcel_local_charge.product_obl')
    product_communication = fields.Many2one(
        'product.product', string='Product Communication',
        config_parameter='sci_goexcel_local_charge.product_communication')

    """
    # Approval
    local_charge_approval_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Local Charge Approvers", related='company_id.local_charge_approval_user_ids',)
    local_charge_notification_user_ids = fields.Many2many(
        'res.users', readonly=False, string="Local Charge Approval Notification Recipients" , related='company_id.local_charge_notification_user_ids',)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        use_local_charge = param.get_param('sci_goexcel_local_charge.use_local_charge')
        res.update(use_local_charge=use_local_charge,
                   )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        use_local_charge = self.use_local_charge or False
        param.set_param('sci_goexcel_local_charge.use_local_charge', use_local_charge)
