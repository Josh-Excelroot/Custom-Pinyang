# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)
    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if self.payment_invoice_ids:
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    payment_invoice_id.invoice_id.last_payment_date = self.payment_date
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    last_payment_date = fields.Date(string="Payment Date", readonly=True)
