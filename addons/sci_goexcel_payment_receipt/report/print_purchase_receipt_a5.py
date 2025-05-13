# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class PrintSaleReceipt(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_av_pr_details_a5'
    _description = "Print Purchase Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        pay_ids = data['form'] if 'form' in data else docids or []
        docs = self.env['account.voucher'].browse(pay_ids)
        payment_docs = []

        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            company = self.env['res.company'].browse(doc.company_id.id)
            company_info = {
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
            for payment_line in doc.line_ids:
                serial_no += 1
                if doc.voucher_type == 'sale':
                    payment_docs.append({
                        'serial_no': serial_no,
                        'description': payment_line.name,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                    })
                elif doc.voucher_type == 'purchase':
                    payment_docs.append({
                        'serial_no': serial_no,
                        'description': payment_line.name,
                        'account': payment_line.account_id.name,
                        'invoice_date': doc.date,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                    })

        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].voucher_type, total_en,
                                                             total_amount, docs[0].currency_id)
        partner_info = self.get_partner_info(partner)
        bank_info = self.get_bank_info(docs[0])
        return {
            'doc_ids': data['ids'] if 'ids' in data else docids or [],
            'doc_model': data['model'] if 'model' in data else 'account.voucher',
            'docs': payment_docs,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
            'company_info': company_info,
            'bank_info': bank_info,
        }

    @api.multi
    def get_partner_info(self, o):
        # get the vendor bank info
        account_number = ''
        bank_name = ''
        company = self.env['res.company'].browse(o.company_id)
        if company:
            bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', o.id)
            ], limit=1)
            if bank:
                account_number = bank.acc_number
                bank_name = bank.bank_id.name

        partner_info = {
            'name': o.name,
            'street': o.street,
            'street2': o.street2,
            'zip': o.zip,
            'city': o.city,
            'state': o.state_id.name,
            'country': o.country_id.name,
            'phone': o.phone,
            'fax': o.fax,
            'account_number': account_number,
            'bank': bank_name,
        }
        return partner_info

    @api.multi
    def get_bank_info(self, o):
        # get the journal bank info
        account_number = ''
        bank = ''
        if o.journal_id:
            journal = self.env['account.journal'].browse(o.journal_id.id)
            if journal:
                if journal.bank_id:
                    print('bank=' + str(journal.bank_id.name))
                    bank = journal.bank_id.name
                if journal.bank_account_id:
                    print('acct_number=' + str(journal.bank_account_id.acc_number))
                    account_number = journal.bank_account_id.acc_number

        bank_info = {
            'account_number': account_number,
            'bank': bank,
        }

        return bank_info

    @api.multi
    def get_payment_receipt_info(self, o, voucher_type, total_en, total_amount, currency_id):
        payment_receipt_info = {
            'payment_receipt_no': o.number,
            'payment_receipt_date': o.date,
            'voucher_type': voucher_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
            'payment_ref': o.name,
            'cheque_no': o.cheque_no,
            'cheque_date': '',
        }
        return payment_receipt_info
