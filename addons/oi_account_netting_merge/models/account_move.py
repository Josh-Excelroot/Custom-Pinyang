'''
Created on Oct 24, 2021

@author: Zuhair Hammadi
'''
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    netting_id = fields.Many2one('account.netting')

    @api.multi
    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        netting_ids = self.env['account.netting'].search(
            [('move_id', 'in', self.ids)])
        if netting_ids:
            self.env.add_todo(netting_ids._fields['state'], netting_ids)
            netting_ids.recompute()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    netting_id = fields.Many2one('account.netting')
