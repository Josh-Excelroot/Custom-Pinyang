# coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class AccountPaymentInvoices(models.Model):
    _inherit = 'account.payment.invoice'

    credit_amount = fields.Float('Credit Note Amount')
    paid_credit_amount = fields.Float('Paid Credit Amount', compute="compute_paid_credit_amount")
    credit_note_ids = fields.One2many('payment.invoice.credit.note', 'payment_inv_id')

    @api.depends('credit_note_ids.credit_amount')
    def compute_paid_credit_amount(self):
        for res in self:
            res.paid_credit_amount = sum(line.credit_amount for line in res.credit_note_ids)

    @api.onchange('credit_amount', 'reconcile_amount')
    def onchange_credit_amount(self):
        if self.residual < (self.reconcile_amount + self.credit_amount):
            raise ValidationError(_("The sum of the reconcile amount and credit amount -> %s is not more than the amount due -> %s in %s Invoice.") % (self.reconcile_amount + self.credit_amount, self.residual, self.invoice_id.number))


class PaymentInvoiceCreditNote(models.Model):
    _name = 'payment.invoice.credit.note'

    credit_note_id = fields.Many2one('account.invoice', string='Credit Note',index=True)
    payment_inv_id = fields.Many2one('account.payment.invoice', string='Payment Invoice',index=True)
    credit_amount = fields.Float('Credit Note')


class AccountPaymentCreditNoteInvoices(models.Model):
    _name = 'account.payment.cn.invoice'

    invoice_id = fields.Many2one('account.invoice', string='Credit Note',index=True)
    payment_id = fields.Many2one('account.payment', string='Payment',index=True)
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    origin = fields.Char(related='invoice_id.origin')
    date_invoice = fields.Date(related='invoice_id.date_invoice')
    date_due = fields.Date(related='invoice_id.date_due')
    payment_state = fields.Selection(related='payment_id.state')
    reconcile_amount = fields.Monetary(string='Reconcile Amount', default=0.000, digits=(16, 3))
    paid_amt = fields.Float("Paid Amount")
    amount_total = fields.Monetary(related="invoice_id.amount_total")
    residual = fields.Monetary(related="invoice_id.residual")
    reference = fields.Char(related='invoice_id.reference')
    fully_reconcile = fields.Boolean('Fully Reconciled?')

    @api.onchange('fully_reconcile')
    def onchange_fully_reconcile(self):
        if self.fully_reconcile:
            self.reconcile_amount = self.residual
        if not self.fully_reconcile:
            self.reconcile_amount = 0.00


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    credit_invoice_ids = fields.One2many('account.payment.cn.invoice', 'payment_id', string="Credit Note")

    @api.onchange('partner_id', 'state', 'partner_type', 'payment_type')
    def _get_open_journal_entries(self):
        if self.open_move_line_ids:
            self.open_move_line_ids = False
        return super(AccountPayment, self)._get_open_journal_entries()

    @api.onchange('payment_type', 'partner_type', 'partner_id', 'currency_id')
    def _onchange_to_get_credit_lines(self):
        if self._context.get('no_insert_line'):
            # no need to insert any line when comes from register payment of CN/invoice
            return
        invoice_type = False
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id:
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_refund'

            invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
                'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = [(5, 0, 0)]
            for invoice_rec in invoice_recs:
                payment_invoice_values.append(
                    [0, 0, {'invoice_id': invoice_rec.id}])
            self.credit_invoice_ids = payment_invoice_values

    def get_latest_invoices(self):
        super(AccountPayment, self).get_latest_invoices()
        self._onchange_to_get_credit_lines()

    def action_refresh(self):
        super(AccountPayment, self).action_refresh()
        self._onchange_to_get_credit_lines()

    @api.multi
    def post(self):
        for rec in self:
            inv_reconcile = round(sum(inv.reconcile_amount for inv in rec.payment_invoice_ids.filtered(lambda x: x.reconcile_amount)),3)
            inv_credit_amount = round(sum(inv.credit_amount for inv in rec.payment_invoice_ids.filtered(lambda x: x.credit_amount)), 3)
            cn_credit_amount = round(sum(credit.reconcile_amount for credit in rec.credit_invoice_ids.filtered(lambda x: x.reconcile_amount)), 3)
            #if rec.payment_invoice_ids and rec.amount != inv_reconcile:
            #    raise UserError(_("The sum of the reconcile amount -> %s of listed Invoices are not equivalent to the payment's amount -> %s.") % (inv_reconcile, self.amount))
            if inv_credit_amount != cn_credit_amount:
                raise UserError(_("The sum of the Credit note amount -> %s of listed Invoices are not equivalent to sum of the reconcile amount of listed Credit Notes -> %s.") % (inv_credit_amount, cn_credit_amount))
        res = super(AccountPayment, self).post()
        for rec in self:
            rec.credit_note_payment()
        return res

    def credit_note_payment(self):
        partial_reconcile_ids = self.env["account.partial.reconcile"]
        for inv in self.payment_invoice_ids.filtered(lambda x: x.credit_amount):
            for credit in self.credit_invoice_ids.filtered(lambda y: y.reconcile_amount - y.paid_amt):
                if inv.paid_credit_amount != inv.credit_amount:
                    credit_amount = credit.reconcile_amount - credit.paid_amt
                    inv_credit_amount = inv.credit_amount - inv.paid_credit_amount
                    amount = 0.0
                    if inv_credit_amount > credit_amount:
                        credit.paid_amt += credit_amount
                        amount = credit_amount
                    else:
                        credit.paid_amt += inv_credit_amount
                        amount = inv_credit_amount
                    self.env['payment.invoice.credit.note'].create({
                            'credit_note_id': credit.invoice_id.id,
                            'payment_inv_id': inv.id,
                            'credit_amount': amount
                        })
                    debit_move_id = inv.invoice_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                    credit_move_id = credit.invoice_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                    if self.payment_type == 'inbound':
                        vals = {
                            'debit_move_id': debit_move_id.id,
                            'credit_move_id': credit_move_id.id,
                            }
                    if self.payment_type == 'outbound':
                        vals = {
                            'credit_move_id': debit_move_id.id,
                            'debit_move_id': credit_move_id.id,
                            }
                    vals.update({
                        'amount': amount
                        })
                    if debit_move_id.amount_currency and credit_move_id.amount_currency and debit_move_id.currency_id == credit_move_id.currency_id and 'amount_currency' not in vals:
                        company_id = debit_move_id.company_id
                        vals.update({
                            'currency_id': debit_move_id.currency_id.id,
                            'amount_currency': company_id.currency_id._convert(amount, debit_move_id.currency_id, company_id, fields.Date.today())
                            })
                    partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)
        return True

    @api.multi
    def cancel(self):
        res = super(AccountPayment, self).cancel()
        # Ahmad Zaman - 7/3/25 - Using uniship cancel method to avoid issues with partially paid invoices
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
                if rec.invoice_ids:
                    move.line_ids.remove_move_reconcile()
                if move.state != 'draft':
                    move.button_cancel()
                move.unlink()
            rec.write({
                'state': 'cancelled',
            })

        # old method
        # moves = self.env['account.move']
        # for inv in self.payment_invoice_ids.filtered(lambda x: x.reconcile_amount or x.credit_amount):
        #     if inv.invoice_id.move_id:
        #         moves += inv.invoice_id.move_id
        #     inv.invoice_id.move_id.line_ids.filtered(lambda x: x.account_id.reconcile).remove_move_reconcile()
        #     inv.invoice_id.move_id = False
        #     inv.invoice_id.action_invoice_approve()
        #     inv.credit_note_ids = False
        # if moves:
        #     moves.button_cancel()
        #     moves.unlink()
        # self.credit_invoice_ids.filtered(lambda y: y.reconcile_amount).write({'paid_amt': 0.0})

        return res
