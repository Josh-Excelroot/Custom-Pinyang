from odoo import api, fields, models, exceptions
import logging
import requests
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    buyer_tin_no = fields.Char(string="Buyers TIN ")
    brn_no = fields.Char(string="BRN Number ")

    buyer_sst_no = fields.Char(string="SST Registration Number")

    ttx_no = fields.Char(string="Tourism Tax Number")

    enable_e_invoice = fields.Boolean(string="Enable E-invoice",compute='check_einvoice_enable')

    msic_code = fields.Many2one('msic.code', string='MSIC Code')

    consolidated_general_public = fields.Boolean(string="Consolidated General Public")

    vaildate_tin_status = fields.Char(string="TIN Status", track_visibility='always', copy=False)

    @api.onchange('consolidated_general_public')
    def _onchange_consolidated_general_public(self):
        if self.consolidated_general_public:
            self.buyer_tin_no = "EI00000000010"
            self.brn_no = 'NA'
            self.customer = True
            self.email = 'NA'
            self.phone = 'NA'
            self.street = 'NA'
            self.street2 = 'NA'
            self.city = 'NA'
            self.zip = 'NA'
            self.state_id = self.company_id.partner_id.state_id.id
            self.company_id = self.company_id.id
            self.country_id = self.company_id.partner_id.country_id.id

        else:
            self.buyer_tin_no = False
            self.brn_no = ""


    def check_einvoice_enable(self):
        for rec in self:
            rec.enable_e_invoice=self.env.user.company_id.enable_e_invoice

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'buyer_tin_no' in vals:
            self.vaildate_tin_status = False
        return res


    def vaildate_tin(self):
        if not self.buyer_tin_no:
            raise UserError("Required TIN No")

        if not self.brn_no:
            raise UserError("Required BRN No")
        if self.vaildate_tin_status == 'TIN Valid':
            raise UserError("TIN already Valid")


        if self.buyer_tin_no and self.brn_no:

            apiBaseUrl = self.env['ir.config_parameter'].sudo().get_param(
                'goexcel_einvoicing_my.login_url_taxpayer_einv')
            generatedAccessToken = self.company_id.authorization_token_einv

            # self.env['ir.config_parameter'].sudo().get_param(
            # 'goexcel_einvoicing_my.authorization_token_einv')

            url = f"{apiBaseUrl}/api/v1.0/taxpayer/validate/{str(self.buyer_tin_no)}?idType=BRN&idValue={str(self.brn_no)}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {generatedAccessToken}'
            }

            vaildate_tin_response = requests.request("GET", url, headers=headers)

            if vaildate_tin_response.status_code == 200:
                self.write({
                    'vaildate_tin_status': 'TIN Valid'
                })

            if vaildate_tin_response.status_code == 404:
                self.write({
                    'vaildate_tin_status': 'TIN Invalid'
                })


    # @api.onchange('country_id')
    # def set_tin_and_brn(self):
    #     for rec in self:
    #         if rec.country_id.name != 'Malaysia':
    #             rec.buyer_tin_no = 'EI00000000020'
    #             rec.brn_no = 'NA'

