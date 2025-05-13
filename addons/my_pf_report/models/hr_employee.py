# See LICENSE file for full copyright and licensing details

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    epf_no = fields.Char('EPF No.')
    ahli_kwsp_note = fields.Char('Ahli Kwsp Note', size=64)
