# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import api, models
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import os
import base64
import json
import requests
import tempfile


class GoogleFileUpload(models.TransientModel):

    _name = "google.file.upload"
    _description = 'Google File Upload'

    def upload_to_google_drive(self, file_name, file_data, folder_id,record=False):
        # check for token expirey
        # kashif 22aug23 :checks token expiry for record company
        if record:
            record.company_id.sudo().check_token_expirey()
        else:
            self.sudo().env.user.company_id.check_token_expirey()
        folder = tempfile.gettempdir()
        file_path = os.path.join(folder, file_name)
        parent_id = folder_id
        if not parent_id:
            parent_id = self.env['multi.folder.drive'].search([
                ('model_id.model', '=', self._name)]).folder_id
        if not parent_id:
            parent_id = self.sudo().env.user.company_id.drive_folder_id
        # g_drive = self.env['google.drive.config']
        # access_token = GoogleDrive.get_access_token(g_drive)
        access_token = self.sudo().env.user.company_id.gdrive_access_token
        with open(file_path, 'wb') as fp:
            fp.write(base64.decodestring(file_data))
        # file upload
        headers = {"Authorization": "Bearer %s" % (access_token)}
        para = {
            "name": "%s" % (str(file_name)),
            "parents": ["%s" % str(parent_id)]
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open("%s" % (str(file_path)), "rb")
        }
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        if r.status_code == 200:
            des = r.text.encode("utf-8")
            d = json.loads(des)
            download_url = """https://drive.google.com/uc?export=download&id="""
            url = "%s%s" % (download_url, d.get('id'))
            return {'url': url, 'file_id': d.get('id')}

    @api.multi
    def delete_from_google_drive(self, file_id):
        # check for token expirey
        self.sudo().env.user.company_id.check_token_expirey()
        access_token = self.env.user.company_id.gdrive_access_token
        headers = {"Authorization": "Bearer %s" % (access_token)}
        url = """https://www.googleapis.com/drive/v3/files/%s""" % file_id
        r = requests.delete(url, headers=headers)
        if r.status_code == 200:
            des = r.text.encode("utf-8")
            d = json.loads(des)
            return d
