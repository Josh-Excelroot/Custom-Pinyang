# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from dateutil.parser import parse


class AccountPayment(models.Model):
    _inherit = "account.payment"

    internal_transfer_sequence_external_id = 'account.sequence_payment_transfer'

    @api.model
    def create(self, vals):
        # all sequence creation moved from def create to confirm button
        # if not vals.get('number') and vals.get('journal_id') and not vals.get('netting'):
        #     payment_date = vals.get('payment_date') or fields.date.today()
        #     if isinstance(payment_date, str):
        #         payment_date = parse(payment_date)
        #
        #     journal = self.env['account.journal'].browse(vals.get('journal_id'))
        #     company_id = vals.get('company_id')
        #     context = {}
        #
        #     if company_id:
        #         context.update({'force_company': vals['company_id']})
        #
        #     if vals.get('payment_type') == 'transfer':
        #         sequence = self.sudo().env.ref(self.internal_transfer_sequence_external_id)
        #     else:
        #         sequence = journal.sequence_id
        #         if journal.type in ['cash', 'bank']:
        #             payment_type = vals.get('payment_type')
        #             if payment_type == 'inbound' and journal.inbound_sequence_id:
        #                 sequence = journal.inbound_sequence_id
        #             elif payment_type == 'outbound' and journal.outbound_sequence_id:
        #                 sequence = journal.outbound_sequence_id
        #
        #     if sequence.based_on_document_date:
        #         context.update({'ir_sequence_date': payment_date})
        #
        #     vals['name'] = sequence.with_context(**context).next_by_id()
        return super(AccountPayment, self).create(vals)

    def post_vendor_payment(self):
        res = super().post_vendor_payment()
        for rec in self:
            if (not rec.name or rec.name == 'New') and rec.journal_id and not rec.netting:
                payment_date = rec.payment_date or fields.date.today()
                if isinstance(payment_date, str):
                    payment_date = parse(payment_date)

                journal = self.env['account.journal'].browse(rec.company_id)
                company_id = rec.company_id
                context = {}

                if company_id:
                    context.update({'force_company': rec.company_id.id})

                if rec.payment_type == 'transfer':
                    sequence = self.sudo().env.ref(self.internal_transfer_sequence_external_id)
                else:
                    sequence = journal.sequence_id
                    if journal.type in ['cash', 'bank']:
                        payment_type = rec.payment_type
                        if payment_type == 'inbound' and journal.inbound_sequence_id:
                            sequence = journal.inbound_sequence_id
                        elif payment_type == 'outbound' and journal.outbound_sequence_id:
                            sequence = journal.outbound_sequence_id

                if sequence.based_on_document_date:
                    context.update({'ir_sequence_date': payment_date})

                rec.name = sequence.with_context(**context).next_by_id()
        return res

    def _get_move_vals(self, journal=None):
        res = super(AccountPayment, self)._get_move_vals(journal=journal)
        if self.journal_id and self.journal_id.type == 'bank':
            if self.payment_type == 'inbound' and self.journal_id.inbound_sequence_id:
                res.update({'name': self.name})
            if self.payment_type == 'outbound' and self.journal_id.outbound_sequence_id:
                res.update({'name': self.name})
        return res
