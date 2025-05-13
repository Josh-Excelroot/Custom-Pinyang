# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields, api
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import requests
import json
from .common import create_folder_on_drive


class MultiFolderDrive(models.Model):

    _name = 'multi.folder.drive'
    _description = 'Multi Folder on Drive'

    model_id = fields.Many2one('ir.model', 'Model')
    name = fields.Char('Folder Name')
    folder_id = fields.Char('Folder ID')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    @api.multi
    def create_folder_on_drive(self):
        parent_id = self.env.user.company_id.drive_folder_id
        folder_id = create_folder_on_drive(self, self.name, parent_id)
        self.folder_id = folder_id

