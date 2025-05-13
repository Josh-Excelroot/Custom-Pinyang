from odoo import api, fields, models, exceptions, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def create(self, vals):
        # refuse to validate a vendor bill/credit note if there already exists one with the same reference for the same partner,
        # because it's probably a double encoding of the same bill/credit note
        if vals.get('type') == 'in_invoice' and vals.get('reference'):
            ref = ''
            if vals.get('reference'):
                ref = vals.get('reference')
        res = super(AccountInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        #print('Testing for save function in invoice. 1')
        res = super(AccountInvoice, self).write(vals)
        #print('Testing for save function in invoice. 2')
        for rec in self:
            #print('Testing for save function in invoice. type=', rec.type)
            if (vals.get('type') == 'in_invoice' or rec.type == 'in_invoice') and (
                    vals.get('reference') or rec.reference):
                #print('Testing for save function in invoice. ref=', rec.reference)
                ref = ''
                if vals.get('reference'):
                    ref = vals.get('reference')
                elif rec.reference:
                    ref = rec.reference
                same_vendor_reference = False
                vendor_list = []
                for vendor_bill in self.search([('type', '=', 'in_invoice'), ('reference', '=', ref),
                                                ('company_id', '=', self.env.user.company_id.id),
                                                ('commercial_partner_id', '=', rec.commercial_partner_id.id),
                                                ('id', '!=', rec.id)]):
                    vendor_list.append(vendor_bill.partner_id.id)
                if vendor_list and len(vendor_list) == len(set(vendor_list)):
                    same_vendor_reference = True

                if same_vendor_reference and rec.state == 'draft':
                    raise UserError(
                        _("Duplicated vendor reference detected. You probably encoded twice the same vendor bill."))

            # Raise warning message if the user select the currency that is not equal to company currency
            # check if there is a currency filled by user, then check if it is same as company currency
            # if not same, and exc. rate is equal to 1, then raise error.
            # print('Testing for save function2 in invoice. type=', rec.currency_id,
            #       ' , rec.exchange_rate_inverse=', str(rec.exchange_rate_inverse))
            # if rec.company_id.currency_id != rec.currency_id and rec.exchange_rate_inverse == 1.000000:
            #     raise exceptions.Warning('The Currency Exchange Rate Should Not Equal to 1.000!!')
            #
            # else:
            #     continue

        return res

    @api.multi
    def _check_duplicate_supplier_reference(self):
        for invoice in self:
            # refuse to validate a vendor bill/credit note if there already exists one with the same reference for the same partner,
            # because it's probably a double encoding of the same bill/credit note
            same_vendor_reference = False
            vendor_list = []
            if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
                for vendor_bill in self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference),
                                                ('company_id', '=', invoice.company_id.id),
                                                ('commercial_partner_id', '=', invoice.commercial_partner_id.id),
                                                ('id', '!=', invoice.id)]):
                    vendor_list.append(vendor_bill.partner_id.id)
                if vendor_list and len(vendor_list) == len(set(vendor_list)):
                    same_vendor_reference = True

            if same_vendor_reference:
                raise UserError(
                    _("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/credit note."))

    #Dennis 22-11-2022 Raise Warning when Salesperson Try to Validate With Different currency but exchange rate = 1
    # @api.multi
    def action_invoice_open_ip(self):
        for rec in self:
            if rec.company_id.currency_id != rec.currency_id and rec.exchange_rate_inverse == 1.000000:
            # if rec.currency_id != company_id.currency_id and rec.exchange_rate_inverse == 1.000000:
                raise exceptions.Warning('The Currency Exchange Rate Should Not Equal to 1.000!!')
        #print('type:' + str(self.type))
        res = super(AccountInvoice, self).action_invoice_open_ip()
        return res
        # print("Validate in progress")


