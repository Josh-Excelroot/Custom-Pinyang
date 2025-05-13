# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import api, models
from odoo.exceptions import UserError
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import os
import base64
import json
import requests
import tempfile


class IrConfigParameter(models.Model):

    _inherit = "ir.config_parameter"

    @api.multi
    def write(self, vals):
        if 'value' in vals:
            if self.key == 'google_drive_service_account_json_key':
                if 'key' in vals:
                    vals['key'] = 'google_drive_service_account_json_key'
                file_path = self.sudo().get_param('google_drive_service_account_json_key_file_path')
                if file_path == 'false':
                    raise UserError('Please set file path parameter first!')
                with open(file_path, 'w') as file:
                    file.write(vals['value'])
                vals['value'] = True

            if self.key == 'google_drive_service_account_json_key_file_path':
                if 'key' in vals:
                    vals['key'] = 'google_drive_service_account_json_key_file_path'

        return super(IrConfigParameter, self).write(vals)
