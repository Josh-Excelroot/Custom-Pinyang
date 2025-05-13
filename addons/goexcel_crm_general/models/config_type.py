from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class ConfigType(models.Model):
    _name = 'crm.config.type'

    type = fields.Many2one(string='Type')
