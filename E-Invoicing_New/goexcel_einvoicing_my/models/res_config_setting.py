from odoo import fields, models
from datetime import datetime, timedelta
import requests
import json
from odoo.exceptions import UserError

class ResConfigSettingsAccount(models.TransientModel):
    _inherit = 'res.config.settings'

    qrcode_url_einv = fields.Char(string="Qr Code URL", config_parameter='goexcel_einvoicing_my.qrcode_url_einv')
    sned_url_einv = fields.Char(string="Invoice Send URL", config_parameter='goexcel_einvoicing_my.sned_url_einv')
    # cancel_url_einv = fields.Char(string="Invoice Cancel URL",config_parameter='goexcel_einvoicing_my.cancel_url_einv')
    login_url_taxpayer_einv = fields.Char(string="Login TaxPayer URL",config_parameter='goexcel_einvoicing_my.login_url_taxpayer_einv')
    login_url_intermediary = fields.Char(string="Login Intermediary URL",config_parameter='goexcel_einvoicing_my.login_url_intermediary')
    authorization_token_einv = fields.Char(string="Authorization Token", related='company_id.authorization_token_einv', readonly=False)
    client_id_einv =  fields.Char(string="Client ID", related='company_id.client_id_einv', readonly=False)
    client_secret_id_einv = fields.Char(string="Clinet Secret ID",   related='company_id.client_secret_id_einv' , readonly=False)
    token_expiry_time =  fields.Datetime(string='Token  Expiry Time')

    enable_e_invoice = fields.Boolean(string='Enable E-Invoice',
                                      related='company_id.enable_e_invoice', readonly=False)

    # def set_values(self):
    #     super(ResConfigSettingsAccount, self).set_values()
    #     if self.token_expiry_time:
    #         self.env['ir.config_parameter'].set_param('goexcel_einvoicing_my.token_expiry_time',
    #                                                   str(self.token_expiry_time))

    def set_values(self):
        """
        Override set_values to update the value of enable_e_invoice in res.company.
        """
        super(ResConfigSettingsAccount, self).set_values()
        # Fetch the value from the config settings
        # enable_e_invoice = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.enable_e_invoice')
        # client_id_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.client_id_einv')
        # client_secret_id_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.client_secret_id_einv')
        # authorization_token_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.authorization_token_einv')


        # Update the value in res.company
        self.company_id.sudo().write({
            'enable_e_invoice': self.enable_e_invoice ,
            'client_id_einv': self.client_id_einv,
            'client_secret_id_einv': self.client_secret_id_einv,
            'authorization_token_einv': self.authorization_token_einv,
        })

    def generate_token_einvoice(self):

        # url = self.login_url_taxpayer_einv
        url = f"{self.login_url_taxpayer_einv}/connect/token"
        if self.login_url_taxpayer_einv and self.client_id_einv and self.client_secret_id_einv:

            payload = {
                'client_id': self.client_id_einv,
                'client_secret': self.client_secret_id_einv,
                'grant_type': 'client_credentials',
                'scope': 'InvoicingAPI'
            }
            files = [
    
            ]
            headers = {
                'client_id': self.client_id_einv,
                'client_secret': self.client_secret_id_einv,
                'grant_type': 'client_credentials',
                'scope': 'InvoicingAPI'
            }
    
            response = requests.request("POST", url, data=payload)

            if response.status_code == 200:
    
                response_data = json.loads(response.text)
                #
                #

                #

                access_token = response_data['access_token']
                expires_in = response_data['expires_in']
                token_type = response_data['token_type']
                scope = response_data['scope']

                current_datetime = fields.Datetime.now()
                one_hour_later = current_datetime + timedelta(hours=1)
                self.token_expiry_time = one_hour_later


                self.company_id.authorization_token_einv = str(access_token)

                self.company_id.write({
                    "authorization_token_einv": str(access_token)
                })


                self.write({
                    "token_expiry_time":one_hour_later,
                    "authorization_token_einv":access_token,
                })

                if self.token_expiry_time:
                    self.env['ir.config_parameter'].set_param('goexcel_einvoicing_my.token_expiry_time',
                                                              str(self.token_expiry_time))

                if self.authorization_token_einv:
                    self.env['ir.config_parameter'].set_param('goexcel_einvoicing_my.authorization_token_einv',
                                                              str(access_token))


            else:
                raise UserError(f"Invalid Response {response.text}")