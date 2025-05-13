import json
from odoo.tools import date_utils
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank_charge_account_id = fields.Many2one('account.account', string='Bank Charge Account',
                                             domain=[('user_type_id.name', '=', 'Expenses')])


class AccountInvoice(models.Model):
    # Add by Kinjal - Version 1.0.2.4 - 1.0.2.5 - 21 Aug
    _inherit = "account.invoice"

    @api.one
    @api.depends('payment_move_line_ids.amount_residual')
    def _get_payment_info_JSON(self):
        self.payments_widget = json.dumps(False)
        if self.payment_move_line_ids:
            content = self._get_payments_vals()
            for c in content:
                if 'account_payment_id' in c:
                    c['ref'] = self.env['account.payment'].search(
                        [('id', '=', c['account_payment_id'])]).name
            info = {'title': _('Less Payment'),
                    'outstanding': False, 'content': content}
            self.payments_widget = json.dumps(
                info, default=date_utils.json_default)

    # Ahmad Zaman 27/5/24 - Added validation if exchange rate's 0 or 1
    @api.multi
    def action_invoice_open_ip(self):
        exchange_rate = self.exchange_rate_inverse
        foreign_currency = False
        if self.currency_id != self.company_id.currency_id:
            foreign_currency = True
        if foreign_currency and (exchange_rate == 0 or exchange_rate == 1):
            raise ValidationError(f"The Exchange Rate cannot be 0.00 or 1.00.")
        return super(AccountInvoice, self).action_invoice_open_ip()
    # end
