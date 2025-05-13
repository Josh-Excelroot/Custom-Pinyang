# coding: utf-8
from odoo import api, fields, models


class AccountPaymentInvoices(models.Model):
    # Payment Invoice Line
    _name = 'account.payment.invoice'

    invoice_id = fields.Many2one('account.invoice', string='Invoice',index=True)
    payment_id = fields.Many2one('account.payment', string='Payment',index=True)
    currency_id = fields.Many2one(related='invoice_id.currency_id', )
    origin = fields.Char(related='invoice_id.origin', )
    date_invoice = fields.Date(related='invoice_id.date_invoice', )
    date_due = fields.Date(related='invoice_id.date_due', )
    payment_state = fields.Selection(related='payment_id.state', store=True)
    reconcile_amount = fields.Monetary(string='Reconcile Amount', default=0.000, digits=(16, 3))
    amount_total = fields.Monetary(related="invoice_id.amount_total", )
    residual = fields.Monetary(related="invoice_id.residual", )
    reference = fields.Char(related='invoice_id.reference', )
    fully_reconcile = fields.Boolean('Fully Reconciled?')

    @api.onchange('fully_reconcile')
    def onchange_fully_reconcile(self):
        if self.fully_reconcile:
            self.reconcile_amount = self.residual
        if not self.fully_reconcile:
            self.reconcile_amount = 0.00


class AccountPaymentMoveLine(models.Model):
    # Payment Journal Items Line
    _name = 'account.payment.move.line'

    date = fields.Date(string='Date')
    move_id = fields.Many2one('account.move', string='journal Entry')
    journal_id = fields.Many2one('account.journal', string='Journal')
    name = fields.Char(string='Label')
    ref = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    amount_currency = fields.Monetary(string="Amount Currency")
    date_maturity = fields.Date(string='Due Date')
    currency_id = fields.Many2one('res.currency')
    payment_id = fields.Many2one('account.payment', string='Payment')


# Kinjal's Update ---
class PaymentMoveLine(models.Model):
    # Other Payment  Move Line
    _name = 'payment.move.line'
    _description = "Payment Move Line"

    ref = fields.Char(related='move_line_id.ref', readonly=True, store=True)
    name = fields.Char(related='move_line_id.name', readonly=True, store=True)
    date_maturity = fields.Date(related='move_line_id.date_maturity', readonly=True, store=True)
    date = fields.Date(related='move_line_id.date', readonly=True, store=True)
    balance = fields.Monetary(compute='_calc_balance', currency_field='move_currency_id')
    allocate = fields.Boolean(string="Fully Reconciled?")
    allocate_amount = fields.Monetary(currency_field='allocation_currency_id', string="Reconcile Amount")
    company_currency_id = fields.Many2one(related='move_line_id.company_currency_id', store=True)
    payment_id = fields.Many2one('account.payment', required=True, ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='move_line_id.partner_id', store=True)
    move_currency_id = fields.Many2one('res.currency', compute='_calc_move_currency_id')
    allocation_currency_id = fields.Many2one(related='payment_id.currency_id', store=True)
    move_id = fields.Many2one(related='move_line_id.move_id', readonly=True, store=True)
    amount_residual_display = fields.Monetary(compute='_calc_amount_residual_display', string='Unreconciled Amount', currency_field='allocation_currency_id')
    sign = fields.Integer(compute="_calc_sign")
    amount_residual = fields.Monetary(compute='_calc_amount_residual', currency_field='allocation_currency_id')

    @api.depends('move_line_id')
    def _calc_move_currency_id(self):
        for record in self:
            record.move_currency_id = record.move_line_id.currency_id or record.move_line_id.company_currency_id

    @api.onchange('allocate', 'amount_residual_display')
    def _calc_allocate_amount(self):
        line_ids = self.payment_id.payment_move_line_ids
        other_lines = line_ids.filtered(lambda line: line != self and line.allocate)
        total = 0
        for line in other_lines:
            total += line.allocate_amount * line.sign
        total = total * self.sign

        if total < 0:
            total = abs(total)
        else:
            total = 0
        if not self.allocate:
            self.allocate_amount = 0
        elif total:
            self.allocate_amount = min(self.amount_residual_display, total)
        else:
            self.allocate_amount = self.amount_residual_display

    @api.depends('payment_id')
    def _calc_sign(self):
        for record in self:
            sign = -1 or 1 * (record.payment_id.destination_account_id.user_type_id.type == 'payable' and 1 or -1)
            record.sign = sign

    @api.depends('move_line_id')
    def _calc_balance(self):
        for record in self:
            record.balance = abs(record.move_line_id.currency_id and record.move_line_id.amount_currency or record.move_line_id.balance)

    @api.onchange('allocate_amount')
    def _onchange_allocate_amount(self):
        self.payment_id._calc_balance()

    @api.depends('amount_residual', 'sign')
    def _calc_amount_residual_display(self):
        for record in self:
            record.amount_residual_display = abs(record.amount_residual)

    @api.depends('move_line_id', 'allocation_currency_id', 'payment_id.payment_move_line_ids.allocate')
    def _calc_amount_residual(self):

        manual_currency_rate = self._context.get('manual_currency_rate') or {}

        if 'currency_rate' in self.env['account.payment'] and self._context.get("active_model") == 'account.payment':
            payment_ids = self.env['account.payment'].browse(self._context.get('active_ids'))
            for payment in payment_ids:
                if payment.currency_rate:
                    manual_currency_rate[payment.currency_id.id] = payment.currency_rate
        for record in self:
            max_date = max(record.payment_id.payment_move_line_ids.filtered('allocate').mapped('move_line_id.date') or [fields.Date.today()])

            if record.allocation_currency_id == record.company_currency_id:
                record.amount_residual = record.move_line_id.amount_residual
            elif record.allocation_currency_id == record.move_currency_id:
                record.amount_residual = record.move_line_id.amount_residual_currency
            elif record.move_line_id.currency_id:
                record.amount_residual = record.move_currency_id.with_context(manual_currency_rate=manual_currency_rate)._convert(record.move_line_id.amount_residual_currency, record.allocation_currency_id, record.move_line_id.company_id, max_date)
            else:
                record.amount_residual = record.company_currency_id.with_context(manual_currency_rate=manual_currency_rate)._convert(record.move_line_id.amount_residual, record.allocation_currency_id, record.move_line_id.company_id, max_date)
