from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Kinjal _prepare_debitnote  version 12.0.2- 12.0.3


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    customer_debit_note = fields.Boolean(string='Customer Debit Note')

    @api.model
    def create(self, value):
        return super(AccountInvoice, self).create(value)

    @api.model
    def _prepare_debitnote(self, invoice, date_invoice=None,
                           date=None, description=None, journal_id=None):
        vals = super(AccountInvoice, self)._prepare_debitnote(invoice, date_invoice=date_invoice, date=date, description=description, journal_id=journal_id)
        vals['customer_debit_note'] = True
        return vals


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        self._post_validate()
        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(
                                    _('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        # Custom Code
                        if invoice and invoice.type in ['out_invoice'] and invoice.customer_debit_note and journal.debitnote_sequence_id:
                            if not journal.debitnote_sequence_id:
                                raise UserError(
                                    _('Please define a sequence for the debit notes'))
                            sequence = journal.debitnote_sequence_id
                        # code for vendor debit note done by shivam
                        if invoice and invoice.type == 'in_invoice' and invoice.customer_debit_note and journal.debitnote_sequence_id:
                            sequence = journal.debitnote_sequence_id
                        new_name = sequence.with_context(
                            ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(
                            _('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        return self.write({'state': 'posted'})
