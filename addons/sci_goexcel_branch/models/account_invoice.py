from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
import re


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    branch = fields.Many2one("account.analytic.tag", string="Branch")
    running_id = fields.Integer(string="Running Id")

    @api.model
    def create(self, vals):
        if not vals.get('branch'):
            vals["branch"] = self.env.user.default_branch.id
        res = super(AccountInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        for operation in self:
            branch = False
            branch_list = []
            if vals.get("branch"):
                branch = vals.get("branch")
            elif operation.branch:
                branch = operation.branch.id

            if branch:
                branch_list.append(branch)
                for line in operation.invoice_line_ids:
                    line.analytic_tag_ids = [(6, 0, branch_list)]

        return res


class AccountMove1(models.Model):
    _inherit = "account.move"

    branch = fields.Many2one("account.analytic.tag", string="Branch")
    running_id = fields.Integer(string="Running Id")

    def post(self, invoice=False):
        self._post_validate()
        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped("line_ids").create_analytic_lines()

        for move in self:
            if move.name == "/" and invoice:
                new_name = False

                if invoice.move_name and invoice.move_name != "/":
                    new_name = invoice.move_name
                else:
                    branch = invoice.branch
                    if not branch:
                        branch = self.env.user.default_branch
                        invoice.branch = branch.id
                    if not branch:
                        raise UserError('Neither branch is selected in record\n'
                                        'Nor you do not have any default branch selected')
                    self.branch = branch.id

                    search_string = False
                    journal = move.journal_id

                    if invoice.type in ["out_invoice", "in_invoice"]:
                        if not invoice.customer_debit_note:
                            # Customer Invoice or Vendor Bill
                            search_string = journal.sequence_id.name
                        else:
                            # Customer Debit Note or Vendor Debit Note
                            search_string = journal.debitnote_sequence_id.name

                    elif invoice.type in ["out_refund", "in_refund"]:
                        # Customer Credit Note or Vendor Refund
                        search_string = journal.refund_sequence_id.name

                    if not search_string:
                        raise UserError('Journal has no sequence selected for specified record type')

                    sequence = self.env['ir.sequence'].search([
                        ("name", "=", search_string), ("branch", "=", branch.id)
                    ], limit=1)

                    if not sequence:
                        raise UserError(f'Branch "{branch.name}" has not any sequence for "{search_string}" in the system')

                    new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()

                if new_name:
                    move.name = new_name

        return super(AccountMove1, self).post()

