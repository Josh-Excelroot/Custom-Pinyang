from odoo import models, fields, api
from odoo.exceptions import Warning


class TransportJobType(models.Model):
    _name = 'transport.job.type'
    _description = 'Job_Type'
    name = fields.Char(string='Name')


class TransportTemperatureType(models.Model):
    _name = 'temperature.type'
    _description = 'Temperature_Type'
    name = fields.Char(string='Name')
