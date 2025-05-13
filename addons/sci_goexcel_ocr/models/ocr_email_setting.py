# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class OCREmailSetting(models.Model):

    _name = "ocr.email.setting"
    _inherit = ['mail.alias.mixin', 'mail.thread']
    _description = 'OCR Email Setting'

    alias_id = fields.Many2one('mail.alias', string='Alias', required=True, help="The email address associated with this channel. "
                        "New emails received will automatically create new vendor bill assigned to the channel.")
    #user_id = fields.Many2one('res.users', string="Claim Handler", domain=[('share', '=', False)])

    # def get_alias_values(self):
    #     values = super(OCREmailSetting, self).get_alias_values()
    #     values['alias_defaults'] = defaults = safe_eval(self.alias_defaults or "{}")
    #     return values
    #
    # def get_alias_model_name(self, vals):
    #     return 'ocr.email.setting'

    # def write(self, vals):
    #     result = super(OCREmailSetting, self).write(vals)
    #     if 'alias_defaults' in vals:
    #         for team in self:
    #             team.alias_id.write(team.get_alias_values())
    #     return result
