# coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_register_payment(self):
        action = super(AccountInvoice, self).action_register_payment()
        if (self.type or '').endswith('refund'):
            action['context']['default_credit_invoice_ids'] = list(action['context']['default_payment_invoice_ids'])
            del action['context']['default_payment_invoice_ids']
        return action
