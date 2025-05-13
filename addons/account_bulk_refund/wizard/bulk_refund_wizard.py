# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BulkRefund(models.TransientModel):
    _name = "account.bulk.refund"
    _description = "Bulk Credit Note/Debit note from invoice"

    partner_id = fields.Many2one('res.partner', string='Partner', required=True,
                                 domain=['|', ('customer', '=', True), ('supplier', '=', True)])
    date = fields.Date(string='Invoice Date From',
                       required=True, default=fields.Date.today())
    type = fields.Selection([
        ('Debit Note', 'Debit Note'),
        ('Credit Note', 'Credit Note')],
        default='Credit Note', required=True)
    description = fields.Char(string='Extra notes if any')
    refund_line_ids = fields.One2many(
        'account.bulk.refund.line', 'bulk_refund_id')

    @api.onchange('partner_id', 'date', 'type')
    def onchange_partner_id(self):
        op_list = []
        self.refund_line_ids = False
        if self.partner_id and self.date:
            search_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('date_invoice', '>=', self.date),
                ('state', '=', 'open'),
                ('currency_id', '=', self.env.user.company_id.currency_id.id)
            ]
            if self.type == 'Credit Note':
                search_domain.append(('type', '=', 'out_invoice'))
            else:
                search_domain.append(('type', '=', 'in_invoice'))

            for invoice in self.env['account.invoice'].search(search_domain):
                op_list.append((0, 0, {
                    'invoice_id': invoice.id,
                }))
        if op_list:
            self.refund_line_ids = op_list
        else:
            self.refund_line_ids = False

    @api.multi
    def create_debit_credit_note(self):
        invoice_lines = []
        for line in self.refund_line_ids.filtered(lambda x: x.reconcile_amount):
            if line.reconcile_amount > line.residual and line.residual:
                raise UserError(_('You cannot create debit/credit note for more than the '
                                  'balance amount in invoice - %s') % (line.invoice_id.number))
            if line.reconcile_amount:
                # Prepare invoice lines
                name = 'Credit Note - %s' % (line.invoice_id.number) if self.type == 'Credit Note' else \
                    'Debit Note - %s' % (line.invoice_id.number)
                invoice_lines.append((0, 0, {
                    'name': (name or '') + ' - ' + (self.description or ''),
                    'account_id': line.account_id and line.account_id.id or self.account_id.id,
                    'price_unit': line.reconcile_amount,
                    'invoice_line_tax_ids': [(6, 0, line.tax_ids.ids)],
                    'quantity': 1.0
                }))
        # Prepare Invoice
        invoice_dict = {
            'partner_id': self.partner_id and self.partner_id.id,
            'journal_id': self.refund_line_ids[0].invoice_id.journal_id.id,
            'invoice_line_ids': invoice_lines,
            'type': 'out_refund' if self.type == 'Credit Note' else 'in_refund',
            'date_invoice': self.date,
        }
        refund_invoice_id = self.env['account.invoice'].create(
            invoice_dict)
        refund_invoice_id.action_invoice_open()
        inv_reconcile = sum(inv.reconcile_amount for inv in self.refund_line_ids.filtered(lambda x: x.reconcile_amount))
        partial_reconcile_ids = []
        if refund_invoice_id.residual < inv_reconcile:
            raise ValidationError(_("The sum of the reconcile amount -> %s of listed Invoices are not equivalent to the payment's amount -> %s.") % (inv_reconcile, refund_invoice_id.residual))
        for inv in self.refund_line_ids.filtered(lambda x: x.reconcile_amount):
            inv_credit_amount = inv.reconcile_amount
            amount = inv_credit_amount
            debit_move_id = inv.invoice_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            credit_move_id = refund_invoice_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            if refund_invoice_id.type == 'out_refund':
                vals = {
                    'debit_move_id': debit_move_id.id,
                    'credit_move_id': credit_move_id.id,
                    }
            if refund_invoice_id.type == 'in_refund':
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
        action = self.env.ref('account.action_invoice_out_refund').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = refund_invoice_id.id
        return action


class BulkRefundLine(models.TransientModel):
    _name = "account.bulk.refund.line"
    _description = "Bulk Credit Note/Debit note line"

    bulk_refund_id = fields.Many2one(
        'account.bulk.refund', string='Bulk Refund')

    invoice_id = fields.Many2one(
        'account.invoice', string='Invoice', required=True)
    date = fields.Date(string='Invoice Date',
                       related='invoice_id.date_invoice')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', related='invoice_id.partner_id')
    date_due = fields.Date(string='Due Date', related='invoice_id.date_due')
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', related='invoice_id.move_id')
    reconcile_amount = fields.Monetary(
        string='Reconcile Amount', currency_field='company_currency_id')
    amount_total = fields.Monetary(
        related="invoice_id.amount_total", currency_field='company_currency_id')
    residual = fields.Monetary(
        related="invoice_id.residual", currency_field='company_currency_id')
    company_currency_id = fields.Many2one(
        'res.currency', related="invoice_id.company_currency_id")
    tax_ids = fields.Many2many('account.tax', string='Tax/VAT')
    account_id = fields.Many2one('account.account', string='Account',
                                 required=False,
                                 domain=[('user_type_id.type', 'not in', ['receivable', 'payable', 'liquidity'])])
