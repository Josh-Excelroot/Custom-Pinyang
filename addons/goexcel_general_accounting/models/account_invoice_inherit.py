from odoo import api, fields, models, exceptions, _
import logging
from datetime import date

from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # def unlink(self):
    #     # for rec in self:
    #     if self.state in 'draft':
    #         raise ValidationError(_("Warning!"))

    # @api.multi
    # def action_invoice_open_ip(self):
    #     res = super(AccountInvoice, self).action_invoice_open_ip()
    #     if res.company_id.currency_id != res.currency_id and res.exchange_rate_inverse == 1.000000:
    #         raise Warning('Warning!')
    #     return res

    # @api.multi
    def write(self, vals):
        if self:
            raise Warning('Warning!')
        res = super(AccountInvoice, self).write(vals)
        # if res.company_id.currency_id != res.currency_id and res.exchange_rate_inverse == 1.000000:

        return res

    # def write(cr, uid, ids, vals, context=None):
    #     # your code
    #     res = super(AccountInvoice).write(cr, uid, ids, vals, context=context)
    #     print("save data", res)
    #     if res.exchange_rate_inverse == 1.000000:
    #         raise Warning('Warning!')
    #     return res
    # def write(self, vals):
    #     res = super(AccountInvoice, self).write(vals)

    # @api.multi
    # def action_invoice_open_ip(self):

    # @api.onchange('exchange_rate_inverse')
    # def onchange_exchange_rate_inverse(self):
    #     if self.exchange_rate_inverse == 1.000000:
    #         raise Warning('Warning!!')

    # @api.onchange('currency_id')
    # def onchange_currency_id(self):
    #     # Custom Module by Sitaram Solutions
    #     if self.company_id or self.currency_id:
    #         if self.company_id.currency_id != self.currency_id:
    #             self.active_manual_currency_rate = True
    #         else:
    #             self.active_manual_currency_rate = False
    #     else:
    #         self.active_manual_currency_rate = False
    #
    # @api.onchange('currency_id')
    # def onchange_currency_id(self):
    #     # Custom Module by Sitaram Solutions
    #     if self.company_id or self.currency_id:
    #         if self.company_id.currency_id != self.currency_id:
    #             self.active_manual_currency_rate = True
    #         else:
    #             self.active_manual_currency_rate = False
    #     else:
    #         self.active_manual_currency_rate = False
