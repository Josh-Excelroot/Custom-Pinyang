# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    service_provider = fields.Char("Service Provider")
    tariff_code = fields.Char("Tariff Code")
