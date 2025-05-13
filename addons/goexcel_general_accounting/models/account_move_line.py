from odoo import api, fields, models,exceptions
import logging
from datetime import date
_logger = logging.getLogger(__name__)
from odoo.tools import float_round


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "id, sequence desc"

    sequence = fields.Integer(string="sequence")
    journal_currency_rate = fields.Float(string='Exc. Rate', default="1.000000",
                                         digits=(12, 6),
                                         compute='_compute_currency_rate',
                                         inverse='_set_currency_rate',
                                         store=True,
                                         track_visibility='onchange')
    amount_currency = fields.Monetary(default=0.0,
                                      compute='_compute_amount_currency',
                                      inverse='_set_debit_field',
                                      store=True,
                                      help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    def _set_currency_rate(self):
        for rec in self:
            pass

    @api.depends('journal_currency_rate')
    @api.onchange('journal_currency_rate')
    def _compute_currency_rate(self):
        for rec in self:
            if rec.journal_currency_rate != 1 and rec.amount_currency != 0:
                if rec.balance > 0 :
                    rec.debit = float_round(rec.journal_currency_rate * rec.amount_currency, 2,
                                             rounding_method='HALF-UP')
                if rec.balance < 0 :
                    if rec.amount_currency < 0:
                        rec.credit = float_round((rec.journal_currency_rate * -rec.amount_currency), 2,
                                          rounding_method='HALF-UP')
                    else:
                        rec.credit = float_round((rec.journal_currency_rate * rec.amount_currency), 2,
                                                  rounding_method='HALF-UP')

    @api.depends('amount_currency')
    @api.onchange('amount_currency')
    def _compute_amount_currency(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.currency_id.id != rec.currency_id.id:
                    if rec.amount_currency > 0:
                        if not rec.balance > 0 and  rec.balance != 0.0 :
                            rec.update({'balance': -rec.balance})
                            rec.update({'debit': rec.balance})
                            rec.update({'credit': 0.0})




    def _set_debit_field(self):
        for rec in self:
            pass
    @api.model
    def default_get(self, fields):
        rec = super(AccountMoveLine, self).default_get(fields)
        if 'line_ids' not in self._context:
            return rec

        # compute the default credit/debit of the next line in case of a manual entry
        balance = 0
        amount_currency = 0
        for line in self.move_id.resolve_2many_commands(
                'line_ids', self._context['line_ids'], fields=['credit', 'debit']):
            balance += line.get('debit', 0) - line.get('credit', 0)
            currency_id = line.get('currency_id')
            amount_currency += line.get('amount_currency')
            journal_currency_rate = line.get('journal_currency_rate')
        # if we are here, line_ids is in context, so journal_id should also be.
        currency = self._context.get('journal_id') and self.env["account.journal"].browse(
            self._context['journal_id']).company_id.currency_id
        if currency:
            balance = currency.round(balance)
        if balance < 0:
            rec.update({'debit': -balance})
        if balance > 0:
            rec.update({'credit': balance})
            if currency.id != currency_id:
                rec.update({'amount_currency': -amount_currency})
                rec.update({'journal_currency_rate': journal_currency_rate})
                rec.update({'currency_id': currency_id})

        return rec


    @api.onchange('amount_currency', 'currency_id')
    def _onchange_amount_currency(self):
        for line in self:
            company_currency_id = line.account_id.company_id.currency_id
            amount = line.amount_currency
            if line.currency_id and company_currency_id and line.currency_id != company_currency_id:

                amount = line.currency_id._convert(amount, company_currency_id, line.company_id,
                                                   line.date or fields.Date.today())
                if line.balance > 0:
                    amount = line.balance
                line.debit = amount > 0 and amount or 0.0
                line.credit = amount < 0 and -amount or 0.0



    # @api.onchange('journal_currency_rate', 'amount_currency')
    # def _onchange_journal_currency_rate(self):
    #     if self.journal_currency_rate !=1 and self.amount_currency !=0:
    #         if self.account_id.user_type_id.name in ['Fixed Asset','Receivable','Bank and Cash', 'Current Assets',
    #                                                  'Prepayment', 'Expenses', 'Current Year Earnings'] and self.amount_currency > 0:
    #             self.debit = float_round(self.journal_currency_rate * self.amount_currency, 2, rounding_method='HALF-UP')
    #         else:
    #              if self.amount_currency > 0:
    #                 self.credit = float_round(  (self.journal_currency_rate * self.amount_currency)   , 2, rounding_method='HALF-UP')
    #              else:
    #                 self.credit = float_round((self.journal_currency_rate * -(self.amount_currency)), 2, rounding_method='HALF-UP')
