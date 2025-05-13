from odoo import models,fields, api


class res_partner(models.Model):
    _inherit = 'res.users'

    position = fields.Char(string='Position')
