from odoo import fields, models, api


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
                                          related='company_id.currency_id', store=True)
