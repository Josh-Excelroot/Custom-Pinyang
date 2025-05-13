from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    transaction_act_id = fields.Many2one('transaction.template')
