from odoo import api, fields, models, exceptions
from odoo.exceptions import AccessError, ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    # supplier_registration_no = fields.Char(string="Supplier Registration#")
    # supplier_sst_no = fields.Char(string="Supplier SST Registration Number")
    supplier_tourism_tax_reg_no = fields.Char(string="Supplier Tourism Tax Registration Number")
    supplier_msic_code = fields.Char(string="Supplier (MSIC) Code")
    supplier_buisness_activity_desc = fields.Char(string="Supplier Business Activity Description")

    enable_e_invoice = fields.Boolean(string="Enable E-Invoice")


    authorization_token_einv = fields.Char(string="Authorization Token")
    client_id_einv = fields.Char(string="Client ID")
    client_secret_id_einv = fields.Char(string="Clinet Secret ID")




