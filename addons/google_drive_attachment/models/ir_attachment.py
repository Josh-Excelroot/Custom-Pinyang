# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import requests
from .common import create_stream_file, create_file_on_drive, delete_file_from_drive
from googleapiclient.http import HttpError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    file_id = fields.Char()
    folder_id = fields.Char()

    def create_folder_on_google_drive(self, folder_name, model_obj=None):
        # check for token expirey
        self.env.user.company_id.check_token_expirey()
        url = 'https://www.googleapis.com/drive/v3/files'
        access_token = self.env.user.company_id.gdrive_access_token
        headers = {
            'Authorization': 'Bearer {}'.format(access_token),
            'Content-Type': 'application/json'
        }
        folder_id = self.env['multi.folder.drive'].search(
            [('model_id.model', '=', model_obj)], limit=1).folder_id
        parent_id = folder_id
        if not parent_id:
            parent_id = self.env.user.company_id.drive_folder_id
        metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = requests.post(url, headers=headers,
                                 data=json.dumps(metadata))
        if response.status_code == 200:
            des = response.text.encode("utf-8")
            d = json.loads(des)
            return d.get('id')

    @api.model
    def create(self, vals):
        res = super(IrAttachment, self).create(vals)
        model_ids = self.env.user.company_id.model_ids
        active_model = res.res_model
        if active_model in model_ids.mapped('model'):
            record=False
            print("upload")
            active_id = res.res_id
            folder =  self.env.user.company_id.folder_type
            parent_id = self.env.user.company_id.drive_folder_id
            if res.res_id:
                record = self.env[active_model].browse(res.res_id)
                if record:
                    folder = record.company_id.folder_type
                    parent_id = record.company_id.drive_folder_id

            if folder == 'single_folder':
                parent_id = parent_id
            if folder == 'multi_folder':
                m_folder_id = self.env['multi.folder.drive'].search(
                    [('model_id.model', '=', active_model),('company_id','=',record.company_id.id if record else self.env.user.company_id.id)])
                parent_id = m_folder_id.folder_id and m_folder_id.folder_id or parent_id
            if folder == 'record_wise_folder':
                rec_id = self.env[active_model].browse(active_id)
                attachment = self.env['ir.attachment'].search(
                    [('res_model', '=', active_model), ('res_id', '=', active_id), ('folder_id', '!=', False)])
                if not attachment:
                    parent_id = self.create_folder_on_google_drive(
                        rec_id.name or res.res_name, active_model)
                    res.folder_id = parent_id
                else:
                    parent_id = attachment.folder_id
            if parent_id:
                fname = False
                if res.res_field:

                    if active_model == 'freight.booking':
                        if res.res_field == 'pl_attachment':
                            fname = 'pl_file_name'

                        elif res.res_field == 'si_attachment':
                            fname = 'si_file_name'

                        elif res.res_field == 'ci_attachment':
                            fname = 'ci_file_name'
                        elif res.res_field == 'obl_attachment':
                            fname = 'obl_file_name'
                        elif res.res_field == 'cc_attachment':
                            fname = 'cc_file_name'

                        if fname:
                            record = self.env[active_model].browse(res.res_id)
                            if record:
                                fname = record[fname]

                file_name = fname or res.name
                stream_path = self.create_stream_file(file_name, res.datas)
                file_metadata = {'name': file_name, 'parents': [parent_id]}
                drive_file_obj = self.create_file_on_drive(file_metadata, stream_path)
                if drive_file_obj.get('download_link') and not res.res_field:
                    res.write({
                        'datas': False,
                        'store_fname': '',
                        'db_datas': False,
                        'type': 'url',
                        'file_id': drive_file_obj.get('id'),
                        'url': drive_file_obj.get('download_link'),
                    })
                else:
                    res.write({
                        'file_id': drive_file_obj.get('id'),
                        'url': drive_file_obj.get('download_link'),
                    })
                if fname:
                    res.datas_fname = fname
        return res

    def create_stream_file(self, file_name, datas):
        return create_stream_file(file_name, datas)

    def create_file_on_drive(self, file_metadata, stream_path):
        return create_file_on_drive(self, file_metadata, stream_path)

    def delete_file_from_drive(self, file_id):
        delete_file_from_drive(self, file_id)

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.file_id:
                try:
                    self.delete_file_from_drive(rec.file_id)
                except HttpError as error:
                    if error.error_details[0].get('reason') == 'insufficientFilePermissions':
                        self.env['google.file.upload'].delete_from_google_drive(rec.file_id)
                    else:
                        raise UserError(str(error))
        return super(IrAttachment, self).unlink()
