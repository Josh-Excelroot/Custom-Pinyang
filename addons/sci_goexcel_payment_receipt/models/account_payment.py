# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    journal_type = fields.Selection(related='journal_id.type', string="Type")
    check_no = fields.Char(string='Check No.')
    cheque_no = fields.Char(string='Cheque No.')
    bank_date = fields.Date(string='Cheque Date')
    reference = fields.Char(string='Payment Ref', track_visibility='always')
    add_to_receipt = fields.Boolean(string='Add to Receipt', default=False)
    unreconcile_amount = fields.Float('Unreconcile Amount', compute="compute_unreconcile_amount", track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')],
                             readonly=True, default='draft', copy=False, string="Status",  track_visibility='always')
    amount = fields.Monetary(string='Payment Amount', required=True, track_visibility='always')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))],
                    track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='always')
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True,
                               copy=False, track_visibility='always')

    @api.depends('amount')
    def compute_unreconcile_amount(self):
        for res in self:
            je_ids = self.env['account.move.line'].search(
                [('payment_id', '=', res.id), ('credit', '>', 0), ('reconciled', '=', False)])
            # Ahmad Zaman - 3/12/24 - using residual amount instead of credit for more accurate results
            res.unreconcile_amount = abs(sum(je.amount_residual for je in je_ids))

    def get_amount(self, amount):
        amt_en = self.currency_id.amount_to_text(amount)
        return amt_en

    def action_print_receipt(self):
        self.ensure_one()
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }
        if self.payment_type == 'inbound':
            return self.env.ref('sci_goexcel_payment_receipt.report_official_receipt_action').report_action(self, data=data)
        else:
            return self.env.ref('sci_goexcel_payment_receipt.report_payment_receipt_action').report_action(self,
                                                                                                           data=data)

    # Done by Laxicon Solution - Shivam
    @api.model
    def create(self, vals):
        # add neeting condition for Netting Sequence Version - 3.0.1 -> 3.0.2
        if not vals.get('name') and vals.get('payment_type') == 'inbound' and ('netting' not in vals or ('netting' in vals and not vals.get('netting'))):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('so.payment.receipts') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'so.payment.receipts') or _('New')
        if not vals.get('name') and vals.get('payment_type') == 'outbound' and ('netting' not in vals or ('netting' in vals and not vals.get('netting'))):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('po.payment.receipts') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'po.payment.receipts') or _('New')
        return super(AccountPayment, self).create(vals)


    @api.multi
    def write(self, vals):

        return super(AccountPayment, self).write(vals)


class AccountPaymentInvoices(models.Model):
    _inherit = 'account.payment.invoice'

    description = fields.Char(string='Description')
