from odoo import api, fields, models, _
from dateutil.parser import parse


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def create(self, vals):
        if not vals.get('number') and vals.get('journal_id'):
            voucher_date = vals.get('date') or fields.date.today()
            if isinstance(voucher_date, str):
                voucher_date = parse(voucher_date)

            journal = self.env['account.journal'].browse(vals.get('journal_id'))
            company_id = vals.get('company_id')
            context = {}

            if company_id:
                context.update({'force_company': vals['company_id']})

            sequence = journal.sequence_id
            if journal.type in ['cash', 'bank']:
                voucher_type = vals.get('voucher_type')
                if voucher_type == 'sale' and journal.inbound_sequence_id:
                    sequence = journal.inbound_sequence_id
                elif voucher_type == 'purchase' and journal.outbound_sequence_id:
                    sequence = journal.outbound_sequence_id

            if sequence.based_on_document_date:
                context.update({'ir_sequence_date': voucher_date})

            vals['number'] = sequence.with_context(**context).next_by_id()
        return super(AccountVoucher, self).create(vals)
