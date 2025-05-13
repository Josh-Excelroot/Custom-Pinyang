from odoo import models,fields, api
from odoo import tools
class res_partner(models.Model):
    _inherit ='res.users'

    signature_image = fields.Binary(string="Signature", readonly=False)


