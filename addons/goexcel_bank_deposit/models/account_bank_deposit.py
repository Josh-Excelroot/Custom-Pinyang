import dateutil.utils

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import date


class BankDeposit(models.Model):
    _name = 'account.bank.deposit'
    _description = 'Bank Deposit/Withdrawal'
    _rec_name = "deposit_name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _compute_account_balance(self):
        for record in self:
            journal = record.journal_id
            credit_records = self.env['account.move.line'].search([
                ('account_id', '=', journal.default_credit_account_id.id),
                ('move_id.state', '=', 'posted'),
                ('debit', '=', 0.0)
            ])

            debit_records = self.env['account.move.line'].search([
                ('account_id', '=', journal.default_debit_account_id.id),
                ('move_id.state', '=', 'posted'),
                ('credit', '=', 0.0)
            ])

            total_credit = sum(credit_records.mapped('credit'))
            total_debit = sum(debit_records.mapped('debit'))
            balance = total_debit - total_credit
            record.current_account_balance = balance

    deposit_name = fields.Char(string="Name", readonly=True, track_visibility='always', copy=False)
    bank_deposit_date = fields.Date(string="Date", default=fields.Date.today, track_visibility='always')
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True, domain="[('type', '=', 'bank')]", track_visibility='always')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', track_visibility='always')
    deposit_move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True, track_visibility='always', copy=False)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id,
                                 track_visibility='always')
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, track_visibility='always')
    current_account_balance = fields.Float(string="Balance", compute='_compute_account_balance', store=True, copy=False)
    type = fields.Selection([('deposit', 'Deposit'), ('withdrawal', 'Withdrawal')], string="Type", default='deposit',
                            track_visibility='always')
    deposit_line_ids = fields.One2many(
        'account.bank.deposit.line', 'bank_deposit_id', string='Deposits')
    bank_deposit_account = fields.Many2one('account.account', string='Bank Account', track_visibility='always')
    deposit_state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancelled', 'Cancelled')],
                                     string='State', default='draft', track_visibility='always')
    deposit_exchange_rate = fields.Float(string="Exchange Rate", track_visibility='always')
    converted_amount = fields.Monetary('Converted Amount', currency_field='company_currency_id')
    company_currency_id = fields.Many2one(
        'res.currency', string="Company Currency", related='company_id.currency_id', store=True)
    is_foreign_currency = fields.Boolean(string="Is Foreign Currency", default=False)
    reference = fields.Char(string="Reference", help="Reference for the Journal Entry", track_visibility='always')
    amount_total = fields.Float(string="Amount Total")
    counter_account = fields.Many2one('account.account', string='Account', related='deposit_line_ids.deposit_account',
                                      track_visibility='always')

    @api.onchange('deposit_exchange_rate', 'deposit_line_ids')
    def onchange_deposit_exchange_rate(self):
        self.converted_amount = self.amount_total * self.deposit_exchange_rate

    @api.onchange('converted_amount')
    def onchange_converted_amount(self):
        if self.amount_total != 0:
            self.deposit_exchange_rate = self.converted_amount / self.amount_total

    @api.onchange('deposit_line_ids')
    def calculate_amount_total(self):
        total = sum(line.deposit_amount for line in self.deposit_line_ids)
        self.amount_total = total

    @api.model
    def update_amount_total_for_unset_records(self):
        unset_records = self.search([])
        for record in unset_records:
            total = sum(line.deposit_amount for line in record.deposit_line_ids)
            record.amount_total = total

    @api.model
    def create(self, vals):
        res = super(BankDeposit, self).create(vals)
        if res.journal_id:
            res._compute_account_balance()
        res.is_foreign_currency = (res.currency_id.id != res.company_id.currency_id.id)
        if res.is_foreign_currency and not res.deposit_exchange_rate:
            raise ValidationError("Please set exchange rate for the foreign currency.")
        return res

    @api.multi
    def copy(self, default=None):
        default = {}
        copied_deposit_line_ids = []
        for line in self.deposit_line_ids:
            deposit_lines = {
                'deposit_account': line.deposit_account.id,
                'deposit_amount': line.deposit_amount,
                'deposit_label': line.deposit_label,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
            }
            copied_deposit_line_ids.append((0, 0, deposit_lines))
        default.update({
            'deposit_state': 'draft',
            'deposit_line_ids': copied_deposit_line_ids,
        })
        return super(BankDeposit, self).copy(default)

    # @api.multi
    # def write(self, vals):
    #     data = {}
    #     content = ''
    #     count = 0
    #     for record in self.deposit_line_ids:
    #         data = {
    #             "deposit_account": record.deposit_account.name,
    #             "deposit_amount": record.deposit_amount,
    #             "deposit_label": record.deposit_label or False,
    #             "analytic_tag_ids": [(6, 0, record.analytic_tag_ids.ids)] or False,
    #         }
    #         if vals.get("deposit_line_ids", False):
    #             if 'deposit_account' in vals.get("deposit_line_ids")[count][2] and vals.get("deposit_line_ids")[count][2][
    #                 'deposit_account']:
    #                 account_id = vals.get("deposit_line_ids")[count][2]['deposit_account']
    #                 account_name = self.env['account.account'].sudo().search([('id', '=', 1156)], limit=1).name
    #                 content += f"  \u2022  Account: {data['deposit_account'] or ''} -> {account_name}<br/>"
    #             if 'deposit_amount' in vals.get("deposit_line_ids")[count][2] and vals.get("deposit_line_ids")[count][2][
    #                 'deposit_amount']:
    #                 dep_amt = vals.get("deposit_line_ids")[count][2]['deposit_amount']
    #                 content += f"  \u2022  Amount: {data['deposit_amount']} -> {dep_amt}<br/>"
    #             if 'deposit_label' in vals.get("deposit_line_ids")[count][2] and vals.get("deposit_line_ids")[count][2][
    #                 'deposit_label']:
    #                 dep_label = vals.get("deposit_line_ids")[count][2]['deposit_label']
    #                 content += f"  \u2022  Label: {data['deposit_label']} -> {dep_label}<br/>"
    #             if content != '':
    #                 self.message_post(body=content)
    #             count += 1
    #     res = super(BankDeposit, self).write(vals)
    #     return res

    @api.multi
    def unlink(self):
        for record in self:
            if record.deposit_state == 'posted':
                raise ValidationError("Posted records cannot be deleted.")
        return super(BankDeposit, self).unlink()

    # @api.model
    # @api.depends('journal_id')
    # def _compute_account_balance(self, journal_id):
    #     credit_records = self.env['account.move.line'].search([
    #         ('account_id', '=', journal_id.default_credit_account_id.id),
    #         ('move_id.state', '=', 'posted'),
    #         ('debit', '=', 0.0)
    #     ])
    #
    #     debit_records = self.env['account.move.line'].search([
    #         ('account_id', '=', journal_id.default_debit_account_id.id),
    #         ('move_id.state', '=', 'posted'),
    #         ('credit', '=', 0.0)
    #     ])
    #
    #     total_credit = sum(credit_records.mapped('credit'))
    #     total_debit = sum(debit_records.mapped('debit'))
    #     balance = total_debit - total_credit
    #     return balance

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        for rec in self:
            if rec.journal_id:
                rec._compute_account_balance()

    @api.onchange('currency_id')
    def set_currency_rate(self):
        if self.currency_id and self.currency_id.id != self.company_id.currency_id.id:
            self.is_foreign_currency = True
            company_rate = self.currency_id.rate
            if company_rate and company_rate != 1:
                self.deposit_exchange_rate = company_rate
        else:
            self.is_foreign_currency = False
            self.deposit_exchange_rate = 1.0

    @api.onchange('type')
    def set_reference(self):
        if self.type == 'deposit':
            self.reference = "Bank Deposit"
        else:
            self.reference = "Bank Withdrawal"

    @api.onchange('journal_id')
    def set_deposit_account(self):
        if self.type == 'deposit' and self.journal_id:
            if not self.journal_id.default_debit_account_id.id:
                raise ValidationError("The selected journal has no default debit account")
            else:
                self.bank_deposit_account = self.journal_id.default_debit_account_id.id

        elif self.type == 'withdrawal' and self.journal_id:
            if not self.journal_id.default_credit_account_id.id:
                raise ValidationError("The selected journal has no default credit account")
            else:
                self.bank_deposit_account = self.journal_id.default_credit_account_id.id
        self.currency_id = self.bank_deposit_account.currency_id.id or self.company_id.currency_id.id

    @api.model
    def _get_account_move(self, deposit):
        if not deposit.deposit_move_id:
            move = {
                'journal_id': deposit.journal_id.id,
                'date': deposit.bank_deposit_date,
                'ref': deposit.reference,
                'company_id': deposit.company_id.id,
                'line_ids': [],
            }
            return move
        else:
            return deposit.deposit_move_id

    @api.model
    def _get_account_move_line(self, deposit):
        created_moves = []
        credit = 0.0
        debit = 0.0
        amount_currency = 0.0
        for move_line in deposit.deposit_line_ids:
            if deposit.is_foreign_currency:
                if deposit.type == 'deposit':
                    debit = move_line.deposit_amount * deposit.deposit_exchange_rate
                    amount_currency = move_line.deposit_amount
                elif deposit.type == 'withdrawal':
                    credit = move_line.deposit_amount * deposit.deposit_exchange_rate
                    amount_currency = -move_line.deposit_amount
            else:
                if deposit.type == 'deposit':
                    debit = move_line.deposit_amount
                elif deposit.type == 'withdrawal':
                    credit = move_line.deposit_amount

            current_move_line = {
                'move_id': deposit.deposit_move_id.id,
                'account_id': deposit.journal_id.default_debit_account_id.id,
                'partner_id': deposit.partner_id.id,
                'name': move_line.deposit_label,
                'currency_id': deposit.currency_id.id,
                'analytic_tag_ids': [(6, 0, move_line.mapped('analytic_tag_ids').ids)],
                'amount_currency': amount_currency,
                'journal_currency_rate': deposit.deposit_exchange_rate,
                'debit': debit,
                'credit': credit,
            }
            created_moves.append(current_move_line)
        return created_moves

    @api.model
    def _get_counter_move_lines(self, deposit):
        created_moves = []
        credit = 0.0
        debit = 0.0
        amount_currency = 0.0
        for counter_line in deposit.deposit_line_ids:
            if deposit.is_foreign_currency:
                if deposit.type == 'deposit':
                    credit = counter_line.deposit_amount * deposit.deposit_exchange_rate
                    amount_currency = -counter_line.deposit_amount
                elif deposit.type == 'withdrawal':
                    debit = counter_line.deposit_amount * deposit.deposit_exchange_rate
                    amount_currency = counter_line.deposit_amount
            else:
                if deposit.type == 'deposit':
                    credit = counter_line.deposit_amount
                elif deposit.type == 'withdrawal':
                    debit = counter_line.deposit_amount

            counter_move_line = {
                'move_id': deposit.deposit_move_id.id,
                'account_id': counter_line.deposit_account.id,
                'partner_id': deposit.partner_id.id,
                'name': counter_line.deposit_label,
                'currency_id': deposit.currency_id.id,
                'analytic_tag_ids': [(6, 0, counter_line.mapped('analytic_tag_ids').ids)],
                'amount_currency': amount_currency,
                'journal_currency_rate': deposit.deposit_exchange_rate,
                'debit': debit,
                'credit': credit,
            }
            created_moves.append(counter_move_line)
        return created_moves

    @api.multi
    def validate_deposit(self):
        for deposit in self:
            if not deposit.deposit_line_ids:
                raise ValidationError('Please create deposit account lines.')
            move_obj = self.env['account.move']
            move_line_obj = self.env['account.move.line']
            created_move = move_obj.sudo().create(self._get_account_move(deposit))
            deposit.write({'deposit_move_id': created_move.id, 'deposit_state': 'posted'})
            for record in deposit:
                line_rec = deposit._get_account_move_line(record)
                counter_line_rec = deposit._get_counter_move_lines(record)
                created_move_lines = []
                for lines in line_rec:
                    created_move_lines.append(lines)
                for counter_lines in counter_line_rec:
                    created_move_lines.append(counter_lines)
                move_line_obj.sudo().create(created_move_lines)
                created_move.action_post()
            if not deposit.deposit_name or deposit.deposit_name == '/':
                if deposit.type == 'deposit':
                    deposit.deposit_name = self.env['ir.sequence'].next_by_code('bank.deposit.sequence')
                else:
                    deposit.deposit_name = self.env['ir.sequence'].next_by_code('bank.withdrawal.sequence')

    @api.multi
    def action_cancel_deposit(self):
        for deposit in self:
            deposit.deposit_state = 'cancelled'
            deposit.deposit_name = '/'
            if deposit.deposit_move_id:
                deposit.deposit_move_id.button_cancel()
                deposit.deposit_move_id.unlink()

    @api.multi
    def action_set_to_draft(self):
        for deposit in self:
            deposit.deposit_state = 'draft'


class BankDepositLines(models.Model):
    _name = 'account.bank.deposit.line'
    _description = 'Bank Deposit/Withdrawal Line'

    deposit_account = fields.Many2one('account.account', string='Account')
    deposit_amount = fields.Float(string='Amount')
    deposit_label = fields.Char(string='Label')
    bank_deposit_id = fields.Many2one('account.bank.deposit')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
