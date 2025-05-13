'''
Created on Oct 21, 2021

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    account_netting_id = fields.Many2one('account.netting', readonly = True)
    
    @api.model
    def _compute_payment_amount(self, invoices=None, currency=None):
        if self._context.get('default_account_netting_id'):
            doc = self.env['account.netting'].browse(self._context.get('default_account_netting_id'))
            payment_currency = currency
            if not payment_currency:
                payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id
            return doc.currency_id._convert(abs(doc.amount_residual), payment_currency, doc.company_id, self.payment_date or fields.Date.today())
            
        return super(AccountPayment, self)._compute_payment_amount(invoices =invoices, currency = currency)
    
        
    def post(self):
        res = super(AccountPayment, self).post()
        
        for record in self:           
            if record.account_netting_id:                
                line_ids = (record.account_netting_id.receivable_line_ids + record.account_netting_id.payable_line_ids).sorted(key = lambda line: (line.date_maturity or line.date, line.id))
                for line in line_ids:
                    if line.reconciled:
                        continue
                    payment_line = record.move_line_ids.filtered(lambda payment_line : payment_line.account_id == line.account_id)
                    if not payment_line:
                        continue
                    if payment_line.reconciled:
                        break
                    (line + payment_line).reconcile()
                    
        return res


    @api.onchange('amount')
    def _onchange_amount(self):
        res = super(AccountPayment, self)._onchange_amount()

        return res
