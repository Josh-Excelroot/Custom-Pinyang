# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools import float_is_zero, format_date
from odoo.exceptions import UserError

import json
from dateutil.relativedelta import relativedelta


class UnrealizedForexRevaluation(models.TransientModel):
    _name = 'unrealized.forex.revaluation'
    _description = 'Unrealized Forex Revaluation'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    date = fields.Date(required=True)
    reverse_date = fields.Date(required=True)
    journal_id = fields.Many2one('account.journal', compute_sudo=True, domain=[('type', '=', 'general')], required=True)
    expense_account_id = fields.Many2one('account.account', compute_sudo=True, required=True)
    income_account_id = fields.Many2one('account.account', compute_sudo=True, required=True)
    ref = fields.Char('Reference', required=True)
    show_warning_move_id = fields.Many2one('account.move', compute='_compute_show_warning')
    report_wizard_id = fields.Many2one('unrealized.forex.report')
    line_ids = fields.One2many('unrealized.forex.revaluation.line', 'parent_id')

    @api.model
    def create(self, vals):
        if not vals.get('report_wizard_id'):
            vals['report_wizard_id'] = 52
        if vals.get('report_wizard_id'):
            report_wizard = self.report_wizard_id.browse(vals.get('report_wizard_id'))
            company = report_wizard.company_id
            vals.update({
                'date': report_wizard.date_to,
                'ref': 'Foreign currencies adjustment entry as of %s' % format_date(self.env, report_wizard.date_to),
                'reverse_date': report_wizard.date_to + relativedelta(day=1),
                'expense_account_id': company.unrealized_forex_loss_account_id.id,
                'income_account_id': company.unrealized_forex_gain_account_id.id,
                'journal_id': company.currency_exchange_journal_id.id
            })
            res = super(UnrealizedForexRevaluation, self).create(vals)
            res.line_ids = res._prepare_revaluation_lines(report_wizard.process_data())
            return res

    @api.depends('expense_account_id', 'income_account_id', 'reverse_date')
    def _compute_show_warning(self):
        for record in self:
            last_move = self.env['account.move.line'].search([
                ('account_id', 'in', (record.expense_account_id + record.income_account_id).ids),
                ('date', '<', record.reverse_date),
            ], order='date desc', limit=1).move_id
            record.show_warning_move_id = False if last_move.id else last_move

    @api.depends('expense_account_id', 'income_account_id', 'date', 'journal_id')
    def _compute_preview_data(self):
        ...

    def _prepare_revaluation_lines(self, data):
        revaluation_lines = []
        company_currency_id = self.company_id.currency_id.id
        for currency_id, currency_data in data.items():
            currency_display = currency_data['currency_display']
            for account_id, account_data in currency_data['lines'].items():
                adjustment = account_data['report_adjustment']
                revaluation_lines.append((0, 0, {
                    'name': f'Provision for {currency_display})',
                    'debit': adjustment if adjustment > 0 else 0,
                    'credit': -adjustment if adjustment < 0 else 0,
                    'type': 'gain_provision' if adjustment > 0 else 'loss_provision',
                    'currency_id': company_currency_id,
                    'account_id': account_id,
                }))
                revaluation_lines.append((0, 0, {
                    'name': f"{'Expense' if adjustment < 0 else 'Income'} Provision for {currency_data['currency_name']} {account_data['account_name']}",
                    'debit': -adjustment if adjustment < 0 else 0,
                    'credit': adjustment if adjustment > 0 else 0,
                    'type': 'loss' if adjustment < 0 else 'gain',
                    'currency_id': company_currency_id,
                    'account_id': self.expense_account_id.id if adjustment < 0 else self.income_account_id.id,
                }))
        return revaluation_lines

    def _replace_account_in_lines(self, line_type, new_account):
        self.line_ids.filtered(lambda l: l.type == line_type).update({'account_id': new_account.id})

    @api.onchange('expense_account_id')
    def _onchange_expense_account(self):
        self._replace_account_in_lines('loss', self.expense_account_id)

    @api.onchange('income_account_id')
    def _onchange_income_account(self):
        self._replace_account_in_lines('gain', self.income_account_id)

    @api.onchange('line_ids')
    def _onchange_lines(self):
        removed_lines = self._origin.line_ids
        for removed_line in removed_lines:
            to_remove = False
            if removed_line not in self.line_ids:
                removed_line_type = removed_line.type
                if removed_line_type.find('provision') != -1:
                    to_remove = self.line_ids.filtered(lambda l: l.id == removed_line.id + 1).id
                else:
                    to_remove = self.line_ids.filtered(lambda l: l.id == removed_line.id - 1).id
                if to_remove:
                    self.line_ids = [(2, to_remove, False)]

    @api.model
    def _prepare_move_vals(self):
        return {
            'ref': self.ref,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'line_ids': [(0, 0, {
                'name': line.name,
                'debit': line.debit,
                'credit': line.credit,
                'currency_id': line.currency_id.id,
                'account_id': line.account_id.id
            }) for line in self.line_ids],
        }

    def create_entries(self):
        self.ensure_one()
        move_vals = self._prepare_move_vals()
        if move_vals['line_ids']:
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            if self.reverse_date:
                reverse_move = move.reverse_moves(date=self.reverse_date)
            form = self.env.ref('account.view_move_form', False)
            ctx = self.env.context.copy()
            ctx.pop('id', '')
            return {
                'type': 'ir.actions.act_window',
                'res_model': "account.move",
                'res_id': move.id,
                'view_mode': "form",
                'view_id': form.id,
                'views': [(form.id, 'form')],
                'context': ctx,
            }
        raise UserError(_("No provision needed was found."))


class UnrealizedForexRevaluationLine(models.TransientModel):
    _name = 'unrealized.forex.revaluation.line'
    _description = 'Unrealized Forex Revaluation Line'

    parent_id = fields.Many2one('unrealized.forex.revaluation')
    account_id = fields.Many2one('account.account')
    currency_id = fields.Many2one('res.currency')
    type = fields.Selection([('gain', 'Gain'), ('loss', 'Loss'), ('gain_provision', 'Gain Provision'), ('loss_provision', 'Loss Provision')])
    name = fields.Char('Label')
    debit = fields.Monetary(currency_field='currency_id')
    credit = fields.Monetary(currency_field='currency_id')
