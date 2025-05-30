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
from itertools import groupby
from datetime import datetime
from odoo.tools import float_round

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    apply_manual_currency_exchange = fields.Boolean(
        string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(
        string='Manual Currency Exchange Rate', digits=(8, 12))
    # TS
    exchange_rate_inverse = fields.Float(
        string='Exchange Rate', help='Eg, USD to MYR (eg 4.21)', copy=False, digits=(8, 6))
    active_manual_currency_rate = fields.Boolean(
        'active Manual Currency', default=True)

    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True)
    amount_in_cc = fields.Monetary(string='Amount in CC', compute='_compute_payment_amount_in_cc',
                                   currency_field='company_currency_id', store=True)
    balance_in_cc = fields.Monetary(string='Balance in CC', compute='_get_balance_amount',
                                    help='Balance of Unmatched Payment',
                                    currency_field='company_currency_id', store=True)
    receive_date = fields.Date('Receive Date')

    @api.multi
    @api.depends('move_line_ids.reconciled')
    def _get_balance_amount(self):
        for payment in self:
            balance = 0.0
            for aml in payment.move_line_ids.filtered(lambda x: x.account_id.reconcile):
                balance += aml.amount_residual
            payment.balance_in_cc = abs(balance)

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayments, self)._onchange_journal()
        # Custom Code by Sitaram Solutions Start
        if self.invoice_ids:
            self.currency_id = self.invoice_ids and self.invoice_ids[0].currency_id.id
        # Custom Code by Sitaram Solutions end
        return res

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        # Custom method by Sitaram Solutions
        if self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

    @api.onchange('currency_id')
    def _get_current_rate(self):
        print('>>>>>>>>>>>>>>>>  _get_current_rate >>>>>>>>>>')
        if self.company_id or self.currency_id:
            print('>>>>>>>>>>>>>>>>  _get_current_rate 2 >>>>>>>>>>')
            if self.company_id.currency_id != self.currency_id:
                print('>>>>>>>>>>>>>>>>  _get_current_rate 3 >>>>>>>>>>')
                self.apply_manual_currency_exchange = True
                self.active_manual_currency_rate = True
                # fc = self.env['res.currency'].search([('name', '=', self.currency_id.name)], limit=1)
                # for rate_id in fc.rate_ids:
                #kashif 2aug23: get exchange rate according to payment date
                payment_date = self.payment_date
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.currency_id.id),
                                                                 ('company_id', '=',
                                                                  self.company_id.id),
                                                                 ('name', '<=', payment_date),
                                                                 ('date_to', '>=', payment_date)], limit=1)
                #end
                if rate_rec:
                    self.exchange_rate_inverse = rate_rec.rate
                    self.manual_currency_exchange_rate = float(
                        float_round(1 / (self.exchange_rate_inverse or 1), 16, rounding_method='HALF-UP'))
                else:
                    self.manual_currency_exchange_rate = float(
                        float_round(1 / (self.exchange_rate_inverse or 1), 16, rounding_method='HALF-UP'))
            else:
                self.exchange_rate_inverse = 1
                self.manual_currency_exchange_rate = 1
                self.apply_manual_currency_exchange = False
                self.active_manual_currency_rate = False

    @api.onchange('exchange_rate_inverse')
    def _update_exchange_rate(self):
        if self.exchange_rate_inverse:
            self.manual_currency_exchange_rate = float(
                float_round(1 / self.exchange_rate_inverse, 16, rounding_method='HALF-UP'))
            self.manual_converted_amount = float_round(self.amount * self.exchange_rate_inverse,
                                                       2, rounding_method='HALF-UP')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayments, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands(
            'invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in (
                'out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = invoice['residual']
            # Custom Code by Sitaram Solutions Start
            rec['active_manual_currency_rate'] = invoice['active_manual_currency_rate']
            rec['apply_manual_currency_exchange'] = invoice['apply_manual_currency_exchange']
            rec['manual_currency_exchange_rate'] = invoice['manual_currency_exchange_rate']
            # Custom Code by Sitaram Solutions End
        return rec

    @api.multi
    def _compute_payment_amount(self, invoices=None, currency=None):
        '''Compute the total amount for the payment wizard.

        :param invoices: If not specified, pick all the invoices.
        :param currency: If not specified, search a default currency on wizard/journal.
        :return: The total amount to pay the invoices.
        '''
        # Get the payment invoices
        if not invoices:
            invoices = self.invoice_ids

        # Get the payment currency
        if not currency:
            currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or invoices and invoices[
                0].currency_id
        # Avoid currency rounding issues by summing the amounts according to the company_currency_id before
        total = 0.00
        groups = groupby(invoices, lambda i: i.currency_id)
        for payment_currency, payment_invoices in groups:
            amount_total = sum([MAP_INVOICE_TYPE_PAYMENT_SIGN[i.type] * i.residual_signed for i in payment_invoices])
            if payment_currency == currency:
                total += amount_total
            else:
                # Custom code by sitaram solution start
                if self.active_manual_currency_rate and self.apply_manual_currency_exchange:
                    # total += amount_total / self.manual_currency_exchange_rate
                    total += float_round(amount_total * self.exchange_rate_inverse,
                                         3, rounding_method='HALF-UP')
                # Custom code by sitaram solution end
                else:
                    total += payment_currency._convert(
                        amount_total, currency, self.env.user.company_id, self.payment_date or fields.Date.today())

        return float_round(total, 2, rounding_method='HALF-UP')

    @api.multi
    @api.depends('amount', 'currency_id', 'company_currency_id', 'manual_currency_exchange_rate')
    def _compute_payment_amount_in_cc(self):
        for rec in self:
            aml_obj = self.env['account.move.line'].with_context(
                check_move_validity=False)
            debit, credit, amount_currency, currency_id = \
                aml_obj.with_context(date=rec.payment_date,
                                     manual_rate=rec.manual_currency_exchange_rate,
                                     active_manual_currency=rec.apply_manual_currency_exchange, ).\
                _compute_amount_fields(
                    rec.amount, rec.currency_id, rec.company_id.currency_id)
            rec.amount_in_cc = float_round(debit, 2, rounding_method='HALF-UP') or float_round(credit, 2, rounding_method='HALF-UP') or 0.0

    # for transfer payment currency amount changed based on manual rate

    def _create_transfer_entry(self, amount):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer, return the reconcilable move line
        """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date, manual_rate=self.manual_currency_exchange_rate,
                                                                     active_manual_currency=self.apply_manual_currency_exchange)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id._convert(
            amount, self.destination_journal_id.currency_id, self.company_id, self.payment_date or fields.Date.today()) or 0

        dst_move = self.env['account.move'].create(
            self._get_move_vals(self.destination_journal_id))

        dst_liquidity_aml_dict = self._get_shared_move_line_vals(
            debit, credit, amount_currency, dst_move.id)
        if self.currency_id.id != self.destination_journal_id.currency_id.id:
            amount_currency = float_round(
                amount_currency / self.manual_currency_exchange_rate, 2, rounding_method='HALF-UP')
        dst_liquidity_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id': self.destination_journal_id.default_credit_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'journal_id': self.destination_journal_id.id,
            'amount_currency': amount_currency,
            'date': self.receive_date
        })
        aml_obj.create(dst_liquidity_aml_dict)

        transfer_debit_aml_dict = self._get_shared_move_line_vals(
            credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': self.name,
            'account_id': self.company_id.transfer_account_id.id,
            'date': self.receive_date,
            'journal_id': self.destination_journal_id.id})
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
            })
        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        if not self.destination_journal_id.post_at_bank_rec:
            dst_move.post()
        return transfer_debit_aml

    #Nihal 8/6/2023 - Fix bug for USD currency missing in payment uniship.
    def _get_liquidity_move_line_vals(self, amount):
        name = self.name
        if self.payment_type == 'transfer':
            name = _('Transfer to %s') % self.destination_journal_id.name
        vals = {
            'name': name,
            'account_id': self.payment_type in ('outbound','transfer') and self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }

        # If the journal has a currency specified, the journal item need to be expressed in this currency
        if self.journal_id.currency_id and self.currency_id != self.journal_id.currency_id:
            amount = self.currency_id._convert(amount, self.journal_id.currency_id, self.company_id, self.payment_date or fields.Date.today())
            # debit, credit, amount_currency, dummy = self.env['account.move.line'].with_context(date=self.payment_date)._compute_amount_fields(amount, self.journal_id.currency_id, self.company_id.currency_id)
            debit, credit, amount_currency, dummy = self.env['account.move.line'].with_context(
                date=self.payment_date)._compute_amount_fields(amount, self.currency_id,
                                                               self.company_id.currency_id)
            vals.update({
                'amount_currency': amount_currency,
                # 'currency_id': self.journal_id.currency_id.id,
                'currency_id': self.currency_id.id,
            })

        return vals
