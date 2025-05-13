# coding: utf-8
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentInvoices(models.Model):
    _name = 'account.payment.invoice'

    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id',store=True)
    origin = fields.Char(related='invoice_id.origin',store=True)
    date_invoice = fields.Date(related='invoice_id.date_invoice',store=True)
    date_due = fields.Date(related='invoice_id.date_due',store=True)
    payment_state = fields.Selection(related='payment_id.state', store=True)
    reconcile_amount = fields.Monetary(
        string='Reconcile Amount', default=0.000, digits=(16, 3))
    amount_total = fields.Monetary(related="invoice_id.amount_total",store=True)
    residual = fields.Monetary(related="invoice_id.residual",store=True)
    # TS add
    reference = fields.Char(related='invoice_id.reference',store=True)
    fully_reconcile = fields.Boolean('Fully Reconciled?')

    @api.onchange('fully_reconcile')
    def onchange_fully_reconcile(self):
        if self.fully_reconcile:
            # cents = Decimal('.001')
            # residual = self.residual.quantize(cents, ROUND_HALF_UP)
            self.reconcile_amount = self.residual
        if not self.fully_reconcile:
            self.reconcile_amount = 0.00
    # TS add


class AccountPaymentMoveLine(models.Model):
    _name = 'account.payment.move.line'

    date = fields.Date(string='Date')
    move_id = fields.Many2one('account.move', string='journal Entry')
    journal_id = fields.Many2one('account.journal', string='Journal')
    name = fields.Char(string='Label')
    ref = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    # analytic_tag_ids = fields.Manymany(related="invoice_id.amount_total")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    amount_currency = fields.Monetary(string="Amount Currency")
    date_maturity = fields.Date(string='Due Date')
    currency_id = fields.Many2one('res.currency')

    payment_id = fields.Many2one('account.payment', string='Payment')
