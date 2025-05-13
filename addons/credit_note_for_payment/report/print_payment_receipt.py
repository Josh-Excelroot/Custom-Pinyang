# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class PrintPaymentReceipt(models.AbstractModel):
    _inherit = 'report.sci_goexcel_payment_receipt.report_pr_details'
    _description = "Print Payment Receipt for Vendor (vendor bill)"

    @api.model
    def _get_report_values(self, docids, data=None):
        # Inbound
        pay_ids = data['form'] if 'form' in data else docids or []
        docs = self.env['account.payment'].browse(pay_ids)
        payment_docs = []
        payment_docs = []
        transfer_docs = []
        journal_docs = []
        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount + sum(d.credit_amount for d in doc.payment_invoice_ids)
            #print('>>>>>>>>>>>> CN print_payment_receipt _get_report_values total_amount=', total_amount)
            period = str(doc.payment_date.strftime("%m")) + '/' + str(doc.payment_date.year)
            company = self.env['res.company'].browse(doc.company_id.id)
            company_info = {
                'name': company.name,
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
            filtered_invoice_ids = doc.payment_invoice_ids.filtered(lambda r: r.reconcile_amount != 0)

            if filtered_invoice_ids and len(filtered_invoice_ids) > 0:
                sorted_payment_lines = doc.payment_invoice_ids.sorted(key=lambda t: t.date_invoice, reverse=False)
                # if doc.payment_type == 'outbound':
                #     total_amount = doc.amount
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
                                 'payment_ref': doc.reference,
                                 'period': period,
                                 # 'type': 'INV',
                                 'amount': (payment_line.reconcile_amount + payment_line.credit_amount),
                                 'currency_id': doc.currency_id,
                            })
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
                                     # 'type': 'CN',
                                     'amount': -abs(credit.credit_amount),
                                     'currency_id': doc.currency_id,
                                })
                                total_amount += credit.credit_amount * -1
                        elif doc.payment_type == 'outbound':
                            #print('>>>>>>>>>>>>>>> outbound >>>>>>')
                            payment_docs.append({
                                'serial_no': serial_no,
                                'supplier_invoice_no': payment_line.reference,
                                'description': payment_line.description,
                                'payment_no': doc.name,
                                'source_doc': payment_line.origin,
                                'invoice_date': payment_line.date_invoice,
                                'original_amount': payment_line.invoice_id.amount_total,
                                'payment_no': doc.name,
                                'payment_ref': doc.reference,
                                'period': period,
                                # 'type': 'VB',
                                'amount': (payment_line.reconcile_amount + payment_line.credit_amount),
                                'currency_id': doc.currency_id,
                            })
                            for credit in payment_line.credit_note_ids:
                                serial_no += 1
                                payment_docs.append({
                                    'serial_no': serial_no,
                                    # Ahmad Zaman - 24/01/24 - Vendor Credit Note Reference Fix
                                    'supplier_invoice_no': credit.credit_note_id.reference or payment_line.reference,
                                    # end
                                    'description': payment_line.description,
                                    'payment_no': doc.name,
                                    'source_doc': credit.credit_note_id.number,
                                    'invoice_date': payment_line.date_invoice,
                                    'original_amount': -abs(credit.credit_note_id.amount_total),
                                    'payment_no': doc.name,
                                    'payment_ref': doc.reference,
                                    'period': period,
                                    # 'type': 'CN',
                                    'amount': -abs(credit.credit_amount),
                                    'currency_id': doc.currency_id,
                                })
                                total_amount += credit.credit_amount * -1
                                #print('>>>>>>>>>>>>>>> credit note Total=', total_amount)
            elif doc.open_move_line_ids:
                if doc.payment_type == 'outbound' and doc.move_reconciled:
                    journal_items = self.env['account.move.line'].search([
                        ('payment_id', '=', doc.id)
                    ])
                    serial_no += 1
                    for journal in journal_items:
                        if journal.debit > 0 and journal.reconciled:
                            for recon_line in journal.full_reconcile_id.reconciled_line_ids.filtered(lambda x: x.invoice_id):
                                journal_docs.append({
                                        'serial_no': serial_no,
                                        'journal_no': recon_line.move_id.name,
                                        'reference': recon_line.invoice_id.number,
                                        'journal_date': recon_line.date,
                                        'amount': abs(recon_line.balance),
                                        'currency_id': doc.currency_id,
                                    })
                                serial_no += 1
            if doc.payment_move_line_ids:
                if doc.payment_type == 'outbound':
                    for jr in doc.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
                        serial_no += 1
                        payment_docs.append({
                            'serial_no': serial_no,
                            'invoice_date': jr.date,
                            'supplier_invoice_no': jr.move_id.name,
                            'source_doc': jr.ref,
                            'original_amount': jr.balance,
                            'amount': jr.allocate_amount,
                            'currency_id': doc.currency_id,
                            'payment_no': '',
                            'payment_ref': '',
                            'period': '',
                        })
            # Internal Transfer
            if doc.payment_type == 'transfer':
                internal_transfer_move_lines = self.env['account.move.line'].search([('payment_id', 'in', doc.ids)])
                if internal_transfer_move_lines:
                    transfer_from_account = ''
                    transfer_to_account = ''
                    description = ''
                    amount = 0.00
                    for move_line in internal_transfer_move_lines:
                        if not move_line.full_reconcile_id:
                            if move_line.credit > 0:
                                transfer_from_account = move_line.account_id.code + ' ' + move_line.account_id.name
                                amount = move_line.credit
                                description = move_line.name
                            if move_line.debit > 0:
                                transfer_to_account = move_line.account_id.code + ' ' + move_line.account_id.name
                    transfer_docs.append({
                        'transfer_from_account': transfer_from_account,
                        'transfer_to_account': transfer_to_account,
                        'description': description,
                        'amount': amount,
                        'currency_id': doc.currency_id,
                    })
        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].payment_type, total_en,
                                                             total_amount, docs[0].currency_id)
        partner_info = self.get_partner_info(partner)
        bank_info = self.get_bank_info(docs[0])
        #print('>>>>>>>>>>>>>>> credit note payment docs=', len(payment_docs))
        return {
            'doc_ids': data['ids'] if 'ids' in data else docids or [],
            'doc_model': data['model'] if 'model' in data else 'account.payment',
            'docs': payment_docs,
            'journal_docs': journal_docs,
            'transfer_docs': transfer_docs,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
            'company_info': company_info,
            'bank_info': bank_info,

        }
