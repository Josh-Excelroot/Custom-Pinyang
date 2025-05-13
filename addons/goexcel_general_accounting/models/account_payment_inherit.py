from odoo import api, fields, models, exceptions, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        for rec in self:
            if rec.company_id.currency_id != rec.currency_id and rec.exchange_rate_inverse == 1.000000:
                raise exceptions.Warning('The Currency Exchange Rate Should Not Equal to 1.000!!')
        res = super(AccountPayment, self).post()
        # if self.payment_invoice_ids:
        #     for payment_invoice_id in self.payment_invoice_ids:
        #         if payment_invoice_id.reconcile_amount > 0:
        #             payment_invoice_id.invoice_id.last_payment_date = self.payment_date
        return res


