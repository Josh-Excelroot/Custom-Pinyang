from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    branch_ids = fields.Many2many('account.analytic.tag', string='Branch')
    default_branch = fields.Many2one('account.analytic.tag', string='Default Branch', required=1)
