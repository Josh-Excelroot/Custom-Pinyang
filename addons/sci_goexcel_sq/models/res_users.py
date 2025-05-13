# -*- coding: UTF-8 -*-

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    is_sales_member = fields.Boolean(string="Is a Sales Member")

