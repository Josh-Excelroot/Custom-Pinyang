# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _compute_amount_fields(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(
            company) if company else self.env.user.company_id
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            if self._context.get('active_manual_currency'):
                # TS - bug 18/2/2021(TMI)
                #print('>>>>>>>>>>>>>> _compute_amount_fields active manual currency=', self._context.get('active_manual_currency')
                #      , ' , manual_rate=', self._context.get('manual_rate'))
                if self._context.get('manual_rate') != 0:
                    amount = float_round(
                        amount / self._context.get('manual_rate'), 5, rounding_method='HALF-UP')
                else:
                    raise ValidationError(_('Exchange Rate Cannot Be Zero!!'))
                # END
            else:
                amount = src_currency._convert(
                    amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id

    # For partial payment cancel -> exchange amount entry - Version 11
    @api.multi
    def remove_move_reconcile(self):
        """ Undo a reconciliation """
        if not self:
            return True
        rec_move_ids = self.env['account.partial.reconcile']
        for account_move_line in self:
            for invoice in account_move_line.payment_id.invoice_ids:
                if invoice.id == self.env.context.get('invoice_id') and account_move_line in invoice.payment_move_line_ids:
                    account_move_line.payment_id.write(
                        {'invoice_ids': [(3, invoice.id, None)]})
            rec_move_ids += account_move_line.matched_debit_ids
            rec_move_ids += account_move_line.matched_credit_ids
        if self.env.context.get('invoice_id'):
            current_invoice = self.env['account.invoice'].browse(
                self.env.context['invoice_id'])
            aml_to_keep = current_invoice.move_id.line_ids | current_invoice.move_id.line_ids.mapped(
                'full_reconcile_id.exchange_move_id.line_ids')
            rec_move_ids = rec_move_ids.filtered(
                lambda r: (r.debit_move_id + r.credit_move_id) & aml_to_keep
            )
        if rec_move_ids:
            exchange_rate_entries = self.env['account.move'].search(
                [('rate_diff_partial_rec_id', 'in', rec_move_ids.ids)])
            if exchange_rate_entries:
                for exchange in exchange_rate_entries:
                    # For Reversed Exchange Rate Entry Date should be Payment Date
                    exchange.reverse_moves(date=exchange.date)
        return super(AccountMoveLine, self).remove_move_reconcile()


# create exchange rate entry for payment partial - Version 11
class AccountMove(models.Model):
    _inherit = 'account.move'

    rate_diff_partial_rec_id = fields.Many2one('account.partial.reconcile')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _set_currency(self):
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        if company and currency:
            if company.currency_id != currency:
                # Modified Code by Sitaram Solutions Start
                if self.invoice_id.active_manual_currency_rate and self.invoice_id.apply_manual_currency_exchange:
                    self.price_unit = float(
                        float_round(self.price_unit * self.invoice_id.exchange_rate_inverse, 4, rounding_method='HALF-UP'))
                else:
                    self.price_unit = self.price_unit * \
                        currency.with_context(
                            dict(self._context or {}, date=self.invoice_id.date_invoice)).rate


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"
    _description = "Partial Reconcile"

    def is_debit_credit_exchange_rate_same(self, debit_move_line=False, credit_move_line=False):
        if not debit_move_line:
            debit_move_line = self.debit_move_id
        if not credit_move_line:
            credit_move_line = self.credit_move_id
        debit_line_exchange_rate,credit_line_exchange_rate = 0, 0
        if debit_move_line.invoice_id:
            debit_line_exchange_rate = debit_move_line.invoice_id.exchange_rate_inverse
        elif debit_move_line.payment_id:
            debit_line_exchange_rate = debit_move_line.payment_id.exchange_rate_inverse
        if credit_move_line.invoice_id:
            credit_line_exchange_rate = credit_move_line.invoice_id.exchange_rate_inverse
        elif credit_move_line.payment_id:
            credit_line_exchange_rate = credit_move_line.payment_id.exchange_rate_inverse
        return debit_line_exchange_rate == credit_line_exchange_rate

    @api.model
    def create(self, vals):
        res = super(AccountPartialReconcile, self).create(vals)
        # eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
        if res.debit_move_id.amount_currency != 0 and res.credit_move_id.amount_currency != 0 and abs(res.debit_move_id.amount_currency) - abs(res.credit_move_id.amount_currency) != 0:
            rate_diff = (res.debit_move_id.debit / res.debit_move_id.amount_currency) - \
                (res.credit_move_id.credit / -res.credit_move_id.amount_currency)
            if res.amount_currency and res.company_id.currency_id.round(res.amount_currency * rate_diff) \
                    and not res.is_debit_credit_exchange_rate_same():
                if not res.company_id.currency_exchange_journal_id:
                    raise UserError(
                        _("You should configure the 'Exchange Rate Journal' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
                #Nihal 23/5/2023 - Fix bug for USD partial reconc. (undo By Rajeel @ 7 sep 2023)
                if 'create_contra_exch_entry' in self._context and not self._context.get('create_contra_exch_entry'):
                    return res
                # res.with_context(partial_pay=True).create_exchange_rate_entry(
                #     aml_to_fix=False, move=False)
        return res

    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        if 'partial_pay' in self._context and self._context.get('partial_pay'):
            rate_diff = self.debit_move_id.debit / self.debit_move_id.amount_currency - \
                self.credit_move_id.credit / -self.credit_move_id.amount_currency
            amount_diff = self.company_id.currency_id.round(
                self.amount_currency * rate_diff)
            if self.credit_move_id.credit == self.amount and self.credit_move_id.credit < self.debit_move_id.debit:
                self.amount -= abs(amount_diff)
            elif self.debit_move_id.debit == self.amount and self.credit_move_id.credit > self.debit_move_id.debit:
                self.amount -= abs(amount_diff)
            date = fields.Date.today()
            if self.credit_move_id.invoice_id and self.credit_move_id.invoice_id.type in ['in_refund', 'out_refund']:
                date = self.credit_move_id.invoice_id.date_invoice
            if self.debit_move_id.invoice_id and self.debit_move_id.invoice_id.type in ['in_refund', 'out_refund']:
                date = self.debit_move_id.invoice_id.date_invoice
            move = self.env['account.move'].create(
                {'journal_id': self.company_id.currency_exchange_journal_id.id, 'rate_diff_partial_rec_id': self.id, 'date': date})
            line_to_reconcile = self.env['account.move.line'].with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': amount_diff < 0 and -amount_diff or 0.0,
                'credit': amount_diff > 0 and amount_diff or 0.0,
                'account_id': self.debit_move_id.account_id.id,
                'move_id': move.id,
                'currency_id': self.currency_id.id,
                'partner_id': self.debit_move_id.partner_id.id
            })
            self.env['account.move.line'].create({
                'name': _('Currency exchange rate difference'),
                'debit': amount_diff > 0 and amount_diff or 0.0,
                'credit': amount_diff < 0 and -amount_diff or 0.0,
                'account_id': amount_diff > 0 and self.company_id.currency_exchange_journal_id.default_debit_account_id.id or self.company_id.currency_exchange_journal_id.default_credit_account_id.id,
                'move_id': move.id,
                'currency_id': self.currency_id.id,
                'partner_id': self.debit_move_id.partner_id.id
            })
            self.env['account.partial.reconcile'].create({
                'debit_move_id': amount_diff < 0 and line_to_reconcile.id or self.debit_move_id.id,
                'credit_move_id': amount_diff > 0 and line_to_reconcile.id or self.credit_move_id.id,
                'amount': abs(amount_diff),
                'amount_currency': 0.0,
                'currency_id': self.debit_move_id.currency_id.id,
            })
            move.post()
        else:
            return super(AccountPartialReconcile, self).create_exchange_rate_entry(aml_to_fix, move)
