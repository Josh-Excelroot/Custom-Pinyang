# -*- coding: utf-8 -*-
from odoo import api, models


class ConfirmationWiz(models.TransientModel):
    _name = 'confirmation.wiz'

    @api.multi
    def action_yes(self):
        if 'active_model' in self._context and self._context.get('active_model') == 'account.payment':
            payment_id = self.env['account.payment'].browse(self._context.get('active_ids'))
            if payment_id:
                return payment_id.with_context({'confirm': True}).post()

    @api.multi
    def action_no(self):
        return True
