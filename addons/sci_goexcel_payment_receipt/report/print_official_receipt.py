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
    _name = 'report.sci_goexcel_payment_receipt.report_or_details'
    _description = "Print Official Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        # Outbound
        pay_ids = data['form'] if 'form' in data else docids or []
        docs = self.env['account.payment'].browse(pay_ids)
        journal_docs = []
        payment_docs = []
        total_amount = 0.00
        unreconciled_amount = 0.0
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            unreconciled_amount = doc.unreconciled_amount
            # total_amount = doc.amount
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
                        total_amount += payment_line.reconcile_amount
                        for credit in payment_line.credit_note_ids:
                            serial_no += 1
                            payment_docs.append({
                                'serial_no': serial_no,
                                'invoice_no': payment_line.invoice_id.number,
                                'payment_no': doc.name,
                                'source_doc': credit.credit_note_id.number,
                                'invoice_date': payment_line.date_invoice,
                                'payment_ref': doc.reference,
                                'period': period,
                                'amount': credit.credit_amount * -1,
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
                        total_amount += payment_line.reconcile_amount
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
                    # journal_items = self.env['account.move.line'].search([
                    #     ('payment_id', '=', doc.id)
                    # ])
                    # serial_no += 1
                    # for journal in journal_items:
                    #     reference = ''
                    #     amount = ''
                    #     if journal.debit > 0:
                    #         if journal.reconciled:
                    #             amount = journal.debit
                    #             for reconc_item in journal.full_reconcile_id:
                    #                 if reconc_item.reconciled_line_ids:
                    #                     for recon_line in reconc_item.reconciled_line_ids:
                    #                         if recon_line.credit > 0:
                    #                             reference = recon_line.move_id.name
                    #                             # break
                    #             for reconc_item in journal.matched_debit_ids:
                    #                 if reconc_item.debit_move_id:
                    #                     for recon_line in reconc_item.debit_move_id:
                    #                         if recon_line.debit > 0:
                    #                             reference = recon_line.move_id.name
                    #             for reconc_item in journal.matched_credit_ids:
                    #                 if reconc_item.credit_move_id:
                    #                     for recon_line in reconc_item.credit_move_id:
                    #                         if recon_line.credit > 0:
                    #                             reference = recon_line.move_id.name
                    #                             # break
                    #             journal_docs.append({
                    #                 'serial_no': serial_no,
                    #                 'journal_no': journal.move_id.name,
                    #                 'reference': reference,
                    #                 'journal_date': journal.date,
                    #                 'amount': amount,
                    #                 'currency_id': doc.currency_id,
                    #             })

        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].payment_type, total_en,
                                                             total_amount, docs[0].currency_id, unreconciled_amount)
        partner_info = self.get_partner_info(partner)
        #print ("journal_docs", journal_docs, doc.payment_move_line_ids.filtered(lambda x: x.allocate_amount))
        return {
            'doc_ids': data['ids'] if 'ids' in data else docids or [],
            'doc_model': data['model'] if 'model' in data else 'account.payment',
            'journal_docs': journal_docs,
            'docs': payment_docs,
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
    def get_payment_receipt_info(self, o, payment_type, total_en, total_amount, currency_id, unreconciled_amount):
        payment_receipt_info = {
            'payment_receipt_no': o.name,
            'payment_receipt_date': o.payment_date,
            'payment_type': payment_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'unreconciled_amount': abs(unreconciled_amount),
            'currency_id': currency_id,
            'cheque_no': o.cheque_no,
            'payment_ref': o.reference,
        }
        return payment_receipt_info
