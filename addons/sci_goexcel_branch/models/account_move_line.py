# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class accountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def update_branch_on_JE(self, year):
        date_from = datetime.strptime(str(year) + '-01-01', DF)
        date_to = datetime.strptime(str(year) + '-12-31', DF)

        data = self.search([('date', '>=', date_from.date()), ('date', '<=', date_to.date())])
        for rec in data:
            move_id = rec.move_id
            if move_id.branch and not rec.analytic_tag_ids:
                rec.analytic_tag_ids = [(6, 0, [rec.move_id.branch.id])]
                continue
            source_branch = rec.get_source_branch()
            if not move_id.branch or not rec.analytic_tag_ids:
                if not source_branch:
                    reconcile_entries_domain = move_id.line_ids.open_reconcile_view()['domain']
                    reconcile_entries = self.search(reconcile_entries_domain)
                    source_branch = reconcile_entries.mapped(lambda l: l.payment_id.branch or l.invoice_id.branch)
                if source_branch:
                    rec.move_id.branch = source_branch.id
                    rec.analytic_tag_ids = [(6, 0, [source_branch.id])]
        #print('update_branch_on_JE')
        customer_wo_ref = self.env["res.partner"].search(
            [('customer', '=', True), ('active', '=', True), ('ref', '=', False)])
        # if customer_wo_ref:
        #    print('customer_wo_ref=', len(customer_wo_ref))
        for cus in customer_wo_ref:
            print('cus=', cus.name, ', id=', str(cus.id))
            cus.customer = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(accountMoveLine, self).create(vals_list)
        for rec in res:
            if not rec.analytic_tag_ids:
                if rec.move_id.branch:
                    rec.analytic_tag_ids = [(6, 0, [rec.move_id.branch.id])]
                else:
                    source_branch = rec.get_source_branch()
                    if source_branch:
                        rec.move_id.branch = source_branch.id
                        rec.analytic_tag_ids = [(6, 0, [source_branch.id])]
        return res

    def get_source_branch(self):
        if self.invoice_id:
            return self.invoice_id.branch
        if self.payment_id:
            return self.payment_id.branch
        return False


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

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
            branch_id = False
            if self.credit_move_id.invoice_id.branch:
                branch_id = self.credit_move_id.invoice_id.branch.id
            if self.debit_move_id.invoice_id.branch:
                branch_id = self.debit_move_id.invoice_id.branch.id
            move = self.env['account.move'].create(
                {'journal_id': self.company_id.currency_exchange_journal_id.id, 'rate_diff_partial_rec_id': self.id,
                 'date': date, 'branch': branch_id})
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
            return True
        # kashif 27may23 : get the branch record from aml to fix
        branch = False
        # kashif 9jun23 : update code to handel multiple lines
        if len(aml_to_fix) > 1:
            move_line_branch = aml_to_fix[0]
        else:
            move_line_branch = aml_to_fix
        if move_line_branch:
            if move_line_branch.analytic_tag_ids:
                if move_line_branch.analytic_tag_ids or move_line_branch.move_id.branch:
                    branch = move_line_branch.analytic_tag_ids or move_line_branch.move_id.branch
            if not branch:
                branch = move_line_branch.get_source_branch()
        # end
        res = super(AccountPartialReconcile, self).create_exchange_rate_entry(aml_to_fix, move)
        # kashif 27may23 : for Exchange JE update the branch on JE and JE items
        if branch:
            # kashif 10june23 : update below code so it will handel multiple move lines comming is res
            if len(res[0]) > 1:
                move_exc = res[0][0]
                move_exc = move_exc.move_id
            else:
                move_exc = res[0].move_id
            # end
            if not move_exc.branch:
                move_exc.branch = branch.id
            for rec in move_exc.line_ids:
                if not rec.analytic_tag_ids:
                    rec.analytic_tag_ids = [(6, 0, [branch.id])]

        return res
# end
