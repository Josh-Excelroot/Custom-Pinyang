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
    _inherit = 'report.sci_goexcel_payment_receipt.report_sr_details'
    #_description = "Print Sale Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.voucher'].browse(data['form'])
        payment_docs = []
        #Canon - add for branch
        docs1 = docs
        #End*****
        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            for payment_line in doc.line_ids:
                serial_no += 1
                if doc.voucher_type == 'sale':
                    payment_docs.append({
                        'serial_no': serial_no,
                        'description': payment_line.name,
                        'account': payment_line.account_id.name,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                        'branch': doc.branch,
                    })
                elif doc.voucher_type == 'purchase':
                    payment_docs.append({
                        'serial_no': serial_no,
                        'description': payment_line.name,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                        'branch': doc.branch,
                    })

        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].voucher_type, total_en,
                                                             total_amount, docs[0].currency_id)
        partner_info = self.get_partner_info(partner)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': payment_docs,
            'docs1': docs1,  #Canon - add for branch
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
        }

    @api.multi
    def get_partner_info(self, o):
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
        }
        return partner_info

    @api.multi
    def get_payment_receipt_info(self, o, voucher_type, total_en, total_amount, currency_id):
        print("testing123")
        payment_receipt_info = {
            'payment_receipt_no': o.number,
            'payment_receipt_date': o.date,
            'voucher_type': voucher_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
            'payment_ref': o.name,
            'cheque_no': o.cheque_no,
            # 'branch': o.branch,

        }
        return payment_receipt_info
