from odoo import api, fields, models, exceptions, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    bank_id = fields.Many2one('res.bank', string='Bank')
    update_posted = fields.Boolean(string='Allow Cancelling Entries', default=True,
                                   help="Check this box if you want to allow the cancellation the entries related to this journal or of the invoice related to this journal")

    @api.model
    def _get_customer_payment_sequence_id(self):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'so.payment.receipts'),
                                                      ('company_id', '=', self.env.user.company_id.id)], limit=1)
        # print('>>>>>>>>>>> _get_customer_payment_sequence_id=', sequence_id)
        if sequence_id:
            return sequence_id.id

    @api.model
    def _get_vendor_payment_sequence_id(self):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'po.payment.receipts'),
                                                      ('company_id', '=', self.env.user.company_id.id)], limit=1)
        # print('>>>>>>>>>>> _get_customer_payment_sequence_id', sequence_id)
        if sequence_id:
            return sequence_id.id

    @api.model
    def _get_contra_sequence_id(self):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'cotra.payment.receipts'),
                                                      ('company_id', '=', self.env.user.company_id.id)], limit=1)
        # print('>>>>>>>>>>> _get_customer_payment_sequence_id', sequence_id)
        if sequence_id:
            return sequence_id.id

    customer_payment_sequence_id = fields.Many2one('ir.sequence', string='Customer Payment Sequence',
                                                   help="This field contains the information related to the numbering of the journal entries of this journal.",
                                                   copy=False, default=_get_customer_payment_sequence_id)
    vendor_payment_sequence_id = fields.Many2one('ir.sequence', string='Vendor Payment Sequence',
                                                 help="This field contains the information related to the numbering of the journal entries of this journal.",
                                                 copy=False, default=_get_vendor_payment_sequence_id)
    contra_sequence_id = fields.Many2one('ir.sequence', string='Contra Sequence',
                                         help="This field contains the information related to the numbering of the journal entries of this journal.",
                                         copy=False, default=_get_contra_sequence_id)


    @api.model
    def create(self, vals):
        if vals.get('type') == 'bank':
            if vals.get('bank_account_id'):
                return super(AccountJournal, self).create(vals)
            else:
                if not (vals.get('bank_acc_number') and vals.get('bank_id') and vals.get('currency_id') and
                        vals.get('default_debit_account_id') and vals.get('default_credit_account_id')):
                    raise exceptions.ValidationError(_('You must fill in all the fields - Acct Number, Currency, Bank, Default Debit Acct & Credit Acct!'))
                else:
                    # Create res.partner.bank and assign to journal
                    res_partner_obj = self.env['res.partner.bank']
                    res_partner_bank = res_partner_obj.create({
                        'acc_number': vals.get('bank_acc_number'),
                        'bank_id': vals.get('bank_id') or False,
                        'company_id': self.env.user.company_id.id or False,
                        'currency_id': vals.get('currency_id') or False,
                        'partner_id': self.env.user.company_id.partner_id.id or False,
                    })
                    vals['bank_account_id'] = res_partner_bank.id
        return super(AccountJournal, self).create(vals)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account", ondelete='restrict', copy=False,
                                      domain="[('partner_id','=', company_partner_id)]")
    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade', index=True,
                                 domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], required=True)
