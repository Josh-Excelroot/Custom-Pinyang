# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import api, models, fields, _
from odoo.http import request
import json
from werkzeug import urls
import requests
from datetime import timedelta
from odoo.exceptions import UserError

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_API_BASE_URL = 'https://www.googleapis.com'


class ResCompany(models.Model):

    _inherit = 'res.company'

    drive_folder_id = fields.Char(string='Folder ID', help="make a folder on drive in which you want to upload files; then open that folder; the last thing in present url will be folder id")
    folder_type = fields.Selection([('single_folder', 'Single Folder'),
                                    ('multi_folder', 'Multi Folder'),
                                    ('record_wise_folder', 'Record wise Folder')], default='single_folder')
    model_ids = fields.Many2many('ir.model', string='Models')

    gdrive_refresh_token = fields.Char(string='Google drive Refresh Token', copy=False)
    gdrive_access_token = fields.Char(string='Google Drive Access Token', copy=False)
    gdrive_client_id = fields.Char(string='Google Drive Client ID', copy=False)
    gdrive_client_secret = fields.Char(string='Google Drive Client Secret', copy=False)
    gdrive_token_validity = fields.Datetime(string='Google Drive Token Validity', copy=False)
    gdrive_redirect_uri = fields.Char(string='Google Drive Redirect URI', compute='_compute_redirect_uri')
    is_google_drive_token_generated = fields.Boolean(string='Google drive Token Generated',
                                                     compute='_compute_is_google_drive_token_generated', copy=False)

#kashif 13july23 : added functionality to share toekn and access code with all companies
    allow_share_token_refresh = fields.Boolean(default=True,string="Allow Share")

    def onclick_get_token(self,access,refresh_token,expiry):
        if self.allow_share_token_refresh:
            for rec in self.search([('id','!=',self.id)]).filtered(lambda r:r.allow_share_token_refresh):
                rec.gdrive_access_token = access
                if refresh_token:
                    rec.gdrive_refresh_token = refresh_token
                rec.gdrive_token_validity = expiry
    #end

    # @api.onchange('folder_type','gdrive_client_id','gdrive_client_secret')
    # def onchange_drive_parameters(self):
    #     for rec in self.search([('id','!=',self.id)]):
    #         rec.folder_type = self.folder_type
    #         rec.gdrive_client_id = self.gdrive_client_id
    #         rec.gdrive_client_secret = self.gdrive_client_secret


    def _compute_redirect_uri(self):
        for rec in self:
            base_url = request.env['ir.config_parameter'].get_param('web.base.url')
            rec.gdrive_redirect_uri = base_url + '/google_drive/authentication'

    def action_get_gdrive_auth_code(self):
        """
        Generate ogoogle drive authorization code
        """

        action = self.env.ref('base.action_res_company_form').read()[0]
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        url_return = '/web#id=%d&action=%d&view_type=form&model=%s' % (self.id, action['id'], 'res.company')
        state = {
            'config_id': self.id,
            'url_return': url_return
        }
        encoded_params = urls.url_encode({
            'response_type': 'code',
            'client_id': self.gdrive_client_id,
            'scope': 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file',
            'redirect_uri': base_url + '/google_drive/authentication',
            'access_type': 'offline',
            'state': json.dumps(state),
            'approval_prompt': 'force',
        })
        auth_url = "%s?%s" % (GOOGLE_AUTH_ENDPOINT, encoded_params)
        #print("auth_url", auth_url)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': auth_url,
        }

    @api.depends('gdrive_access_token', 'gdrive_refresh_token')
    def _compute_is_google_drive_token_generated(self):
        """
        Set True if the Google Drive refresh token is generated
        """
        for rec in self:
            rec.is_google_drive_token_generated = bool(rec.gdrive_access_token) and bool(rec.gdrive_refresh_token)

    def generate_gdrive_refresh_token(self):
        """
        generate google drive access token from refresh token if expired
        """
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': self.gdrive_refresh_token,
            'client_id': self.gdrive_client_id,
            'client_secret': self.gdrive_client_secret,
            'grant_type': 'refresh_token',
        }


        try:
            res = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers)
            print('>>>>>>>>>>>>> generate_gdrive_refresh_token res=', str(res))
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.sudo().write({
                    'gdrive_access_token': response.get('access_token'),
                    'gdrive_token_validity': fields.Datetime.now() + timedelta(seconds=expires_in) if expires_in else False,
                })
                # kashif 22aug23 : added functionality to share toekn and access code with all companies

                self.onclick_get_token(response.get('access_token'), response.get('refresh_token'),
                                       fields.Datetime.now() + timedelta(
                                           seconds=expires_in) if expires_in else False)
                # end
        except requests.HTTPError as error:
            error_key = error.response.json().get("error", "nc")
            print('>>>>>>>>>>>>> generate_gdrive_refresh_token error=', str(error))
            # error_msg = _(
            #     "An error occurred while generating the token. Your authorization code may be invalid or has already expired [%s]. "
            #     "You should check your Client ID and secret on the Google APIs plateform or try to stop and restart your calendar synchronisation.",
            #     str(error))
            raise UserError(error)

    def get_gdrive_tokens(self, authorize_code):
        """
        Generate onedrive tokens from authorization code
        """

        base_url = request.env['ir.config_parameter'].get_param('web.base.url')

        headers = {"content-type": "application/x-www-form-urlencoded"}
        #kashif 25sept23: added access offline ... to generate refresh tokken offline
        data = {
            'code': authorize_code,
            'client_id': self.gdrive_client_id,
            'client_secret': self.gdrive_client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': base_url + '/google_drive/authentication',
            'access_type': 'offline',
            'prompt': 'consent'

        }
        try:
            res = requests.post(GOOGLE_TOKEN_ENDPOINT, params=data,
                                headers=headers)
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.sudo().write({
                    'gdrive_access_token': response.get('access_token'),
                    'gdrive_refresh_token': response.get('refresh_token'),
                    'gdrive_token_validity': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
                # kashif 13july23 : added functionality to share toekn and access code with all companies

                self.onclick_get_token(response.get('access_token'),response.get('refresh_token'),fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False)
                #end

        except requests.HTTPError:
            error_msg = _("Something went wrong during your token generation. Maybe your Authorization Code is invalid")
            raise UserError(error_msg)

    def check_token_expirey(self):
        if self.gdrive_token_validity <= fields.Datetime.now():
            self.generate_gdrive_refresh_token()
