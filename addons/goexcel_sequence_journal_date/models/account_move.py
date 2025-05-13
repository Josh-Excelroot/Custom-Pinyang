from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self, invoice=False):
        self._post_validate()
        # Only create analytic lines if it has not been created.
        # 12.0.4 fix bug of create_analytic_lines triggered more than once because of function override
        # 12.0.5 singleton bug fix by using mapping
        # analytic_lines = self.env['account.analytic.line'].search([('move_id', 'in', self.line_ids.ids)])
        all_line_ids = self.mapped('line_ids').ids
        analytic_lines = self.env['account.analytic.line'].search([('move_id', 'in', all_line_ids)])
        if not analytic_lines:
            self.mapped('line_ids').create_analytic_lines()

        # self.mapped("line_ids").create_analytic_lines()


        def raise_sequence_not_found_error(journal_id, sequence_name):
            raise UserError(f'Please define a {sequence_name} on Journal {journal_id.name}')

        for move in self:
            if move.name != "/" or not invoice:
                continue

            journal = move.journal_id

            new_name = False
            if invoice.move_name and invoice.move_name != "/":
                new_name = invoice.move_name
            else:
                invoice_type = invoice.type
                customer_debit_note = invoice.customer_debit_note

                if invoice_type in ['out_invoice', 'in_invoice']:
                    if not customer_debit_note:
                        if journal.sequence_id:
                            sequence = journal.sequence_id
                        else:
                            raise_sequence_not_found_error(journal, 'Sequence')

                    else:
                        if journal.debitnote_sequence_id:
                            sequence = journal.debitnote_sequence_id
                        else:
                            raise_sequence_not_found_error(journal, 'Debitnote Sequence')

                else:
                    if journal.refund_sequence_id:
                        sequence = journal.refund_sequence_id
                    else:
                        raise_sequence_not_found_error(journal, 'Refund Sequence')

                if sequence.based_on_document_date:
                    new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                else:
                    new_name = sequence.next_by_id()

            if new_name:
                move.name = new_name

        return super(AccountMove, self).post(invoice=invoice)
