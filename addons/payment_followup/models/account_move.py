# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _get_result(self):
        for aml in self:
            aml.result = aml.debit - aml.credit

    followup_line_id = fields.Many2one('payment.followup.line', 'Follow-up Level', ondelete='set null')
    # restrict deletion of the followup line
    followup_date = fields.Date('Latest Follow-up')
    result = fields.Float(compute='_get_result', string="Balance")
    # 'balance' field is not the same
