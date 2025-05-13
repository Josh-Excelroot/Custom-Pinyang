'''
Created on Oct 24, 2021

@author: Zuhair Hammadi
'''
from odoo import models, api

class AccountMove(models.Model):
    _inherit = "account.move"
    
    @api.multi
    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        netting_ids = self.env['account.netting'].search([('move_id','in', self.ids)])
        if netting_ids:
            self.env.add_todo(netting_ids._fields['state'], netting_ids)
            netting_ids.recompute()
        return res