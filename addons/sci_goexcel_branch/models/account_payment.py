from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class AccountPayment(models.Model):
    _inherit = "account.payment"

    branch = fields.Many2one(
        "account.analytic.tag",
        string="Branch",
        default=lambda self: self.env.user.default_branch.id,
    )

    @api.model
    def create(self, vals):
        branch_id = vals.get('branch', False)
        if branch_id:
            branch = self.env['account.analytic.tag'].browse(branch_id)
        else:
            branch = self.env.user.default_branch
            if not branch:
                raise UserError('Neither branch is selected in record\n'
                                'Nor you do not have any default branch selected')
            branch_id = branch.id
            vals['branch'] = branch_id

        date = datetime.strptime(vals.get('payment_date'), '%Y-%m-%d').date()

        journal_id = vals.get('journal_id')
        journal = self.env['account.journal'].browse(journal_id)

        if vals["payment_type"] == "transfer":
            sequence = self.env.ref(f'sci_goexcel_branch.seq_internal_payment_transfer_branch_{branch_id}')

        else:
            if vals["payment_type"] == "inbound":
                search_string = journal.customer_payment_sequence_id.name
            else:  # vals["payment_type"] == "outbound"
                search_string = journal.vendor_payment_sequence_id.name

            if not search_string:
                raise UserError('Journal has no sequence selected for specified record type')

            sequence = self.env["ir.sequence"].search([
                ("name", "=", search_string), ("branch", "=", branch_id),
            ], limit=1)

            if not sequence:
                raise UserError(f'Branch "{branch.name}" has not any sequence for "{search_string}" in the system')

        vals["name"] = sequence.with_context(ir_sequence_date=date).next_by_id()

        return super(AccountPayment, self).create(vals)


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    branch = fields.Many2one(
        "account.analytic.tag",
        string="Branch",
        default=lambda self: self.env.user.default_branch.id,
    )

    @api.model
    def create(self, vals):
        branch_id = vals.get('branch', False)
        if branch_id:
            branch = self.env['account.analytic.tag'].browse(branch_id)
        else:
            branch = self.env.user.default_branch
            if not branch:
                raise UserError('Neither branch is selected in record\n'
                                'Nor you do not have any default branch selected')
            branch_id = branch.id
            vals['branch'] = branch_id

        date = vals.get('date', False)
        if date:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            date = datetime.now().date()
            vals['date'] = date

        journal_id = vals.get('journal_id')
        journal = self.env['account.journal'].browse(journal_id)
        if vals["voucher_type"] == "sale":
            search_string = journal.customer_payment_sequence_id.name
        else:  # vals["voucher_type"] == "purchase":
            search_string = journal.vendor_payment_sequence_id.name

        if not search_string:
            raise UserError('Journal has no sequence selected for specified record type')

        sequence = self.env["ir.sequence"].search([
            ("name", "=", search_string), ("branch", "=", branch_id),
        ], limit=1)

        if not sequence:
            raise UserError(f'Branch "{branch.name}" has not any sequence for "{search_string}" in the system')

        vals["number"] = sequence.with_context(ir_sequence_date=date).next_by_id()

        return super(AccountVoucher, self).create(vals)
