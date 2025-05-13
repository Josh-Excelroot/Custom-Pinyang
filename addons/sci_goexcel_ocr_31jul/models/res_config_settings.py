# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ocr_use_first_page_only = fields.Boolean(string="OCR - Use First Page Only")
    is_installed_sale = fields.Boolean(string="Is the Sale Module Installed")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        ocr_use_first_page_only = param.get_param('sci_goexcel_ocr.ocr_use_first_page_only')
        res.update(ocr_use_first_page_only=ocr_use_first_page_only,
                   )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        ocr_use_first_page_only = self.ocr_use_first_page_only or False
        param.set_param('sci_goexcel_ocr.ocr_use_first_page_only', ocr_use_first_page_only)
