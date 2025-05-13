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


class PrintOfficialReceipt(models.AbstractModel):
    _inherit = 'report.sci_goexcel_payment_receipt.report_or_details'
    _description = "Print Official Receipt"

    @api.model
    def _get_report_values(self, docids, data=None):
        pay_ids = data['form'] if 'form' in data else docids or []
        docs = self.env['account.payment'].browse(pay_ids)
        payment_docs = []
        payment_docs = []
        journal_docs = []
        total_amount = 0.00
        unreconciled_amount = 0.0
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            unreconciled_amount = doc.unreconciled_amount
            # total_amount = doc.amount + sum(d.credit_amount for d in doc.payment_invoice_ids)
            period = str(doc.payment_date.strftime("%m")) + \
                '/' + str(doc.payment_date.year)
            sorted_payment_lines = doc.payment_invoice_ids.sorted(
                key=lambda t: t.date_invoice, reverse=False)
            for payment_line in sorted_payment_lines:
                if payment_line.reconcile_amount != 0:
                    serial_no += 1
                    if doc.payment_type == 'inbound':
                        payment_docs.append({
                            'serial_no': serial_no,
                            'invoice_no': payment_line.invoice_id.number,
                            'payment_no': doc.name,
                            'source_doc': payment_line.origin,
                            'invoice_date': payment_line.date_invoice,
                            'original_amount': payment_line.invoice_id.amount_total,
                            'payment_ref': doc.reference,
                            'period': period,
                            'amount': payment_line.reconcile_amount,
                            'currency_id': doc.currency_id,
                        })
                        total_amount += payment_line.reconcile_amount + payment_line.credit_amount
                        for credit in payment_line.credit_note_ids:
                            serial_no += 1
                            payment_docs.append({
                                'serial_no': serial_no,
                                'invoice_no': payment_line.invoice_id.number,
                                'payment_no': doc.name,
                                'source_doc': credit.credit_note_id.number,
                                'invoice_date': payment_line.date_invoice,
                                'original_amount': payment_line.invoice_id.amount_total,
                                'payment_ref': doc.reference,
                                'period': period,
                                'amount': credit.credit_amount,
                                'currency_id': doc.currency_id,
                            })
                            total_amount += credit.credit_amount * -1

                    elif doc.payment_type == 'outbound':
                        payment_docs.append({
                            'serial_no': serial_no,
                            'supplier_invoice_no': payment_line.invoice_id.number,
                            'payment_no': doc.name,
                            'source_doc': payment_line.origin,
                            'invoice_date': payment_line.date_invoice,
                            'original_amount': payment_line.invoice_id.amount_total,
                            'payment_no': doc.name,
                            'payment_ref': doc.reference,
                            'period': period,
                            'amount': payment_line.reconcile_amount,
                            'currency_id': doc.currency_id,
                        })
                        total_amount += payment_line.reconcile_amount + payment_line.credit_amount
                        for credit in payment_line.credit_note_ids:
                            serial_no += 1
                            payment_docs.append({
                                'serial_no': serial_no,
                                'supplier_invoice_no': payment_line.invoice_id.number,
                                'payment_no': doc.name,
                                'source_doc': credit.credit_note_id.number,
                                'invoice_date': payment_line.date_invoice,
                                'original_amount': payment_line.invoice_id.amount_total,
                                'payment_no': doc.name,
                                'payment_ref': doc.reference,
                                'period': period,
                                'amount': credit.credit_amount,
                                'currency_id': doc.currency_id,
                            })
                            total_amount += credit.credit_amount * -1
            if doc.payment_move_line_ids:
                if doc.payment_type == 'inbound':
                    for jr in doc.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
                        serial_no += 1
                        payment_docs.append({
                            'serial_no': serial_no,
                            'invoice_date': jr.date,
                            'invoice_no': jr.move_id.name,
                            'source_doc': jr.ref,
                            'original_amount': jr.balance,
                            'amount': jr.allocate_amount,
                            'currency_id': doc.currency_id,
                            'payment_no': '',
                            'payment_ref': '',
                            'period': '',
                        })
                        total_amount += jr.allocate_amount
        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].payment_type, total_en,
                                                             total_amount, docs[0].currency_id, unreconciled_amount)
        partner_info = self.get_partner_info(partner)

        return {
            'doc_ids': data['ids'] if 'ids' in data else docids or [],
            'doc_model': data['model'] if 'model' in data else 'account.payment',
            'docs': payment_docs,
            'journal_docs': journal_docs,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
        }
