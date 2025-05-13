# See LICENSE file for full copyright and licensing details

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    badge_id = fields.Char("Badge ID")
