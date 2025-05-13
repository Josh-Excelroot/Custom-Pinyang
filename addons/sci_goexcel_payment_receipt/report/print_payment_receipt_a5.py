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


class PrintPaymentReceipt(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_pr_a5'
    _description = "Print Payment Receipt for Vendor (vendor bill)"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        # Inbound
        pay_ids = data['form'] if 'form' in data else docids or []
        docs = self.env['account.payment'].browse(pay_ids)
        payment_docs = []
        transfer_docs = []
        journal_docs = []
        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            period = str(doc.payment_date.strftime("%m")) + \
                '/' + str(doc.payment_date.year)
            company = self.env['res.company'].browse(doc.company_id.id)
            company_info = {
                'name': company.name,
                'street': company.street,
                'street2': company.street2,
                'zip': company.zip,
                'city': company.city,
                'state': company.state_id.name.upper(),
                'country': company.country_id.name.upper(),
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
            # if it is invoice payment
            # TS Bug - invoice lines are saved but not reconciled.
            filtered_invoice_ids = doc.payment_invoice_ids.filtered(
                lambda r: r.reconcile_amount != 0)

            if filtered_invoice_ids and len(filtered_invoice_ids) > 0:
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
                                'payment_ref': doc.reference,
                                'period': period,
                                'amount': payment_line.reconcile_amount,
                                'currency_id': doc.currency_id,
                            })
                        elif doc.payment_type == 'outbound':
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
                                'amount': payment_line.reconcile_amount,
                                'currency_id': doc.currency_id,
                            })
            # if doc.payment_move_line_ids:
            #     if doc.payment_type == 'outbound':
            #         for jr in doc.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
            #             serial_no += 1
            #             payment_docs.append({
            #                 'serial_no': serial_no,
            #                 'invoice_date': jr.date,
            #                 'supplier_invoice_no': jr.move_id.name,
            #                 'source_doc': jr.ref,
            #                 'original_amount': jr.balance,
            #                 'amount': jr.allocate_amount,
            #                 'currency_id': doc.currency_id,
            #                 'payment_no': '',
            #                 'payment_ref': '',
            #                 'period': '',
            #             })
            #         # journal_items = self.env['account.move.line'].search([
            #         #     ('payment_id', '=', doc.id)
            #         # ])
            #         # serial_no += 1
            #         # for journal in journal_items:
            #         #     reference = ''
            #         #     amount = ''
            #         #     if journal.debit > 0:
            #         #         if journal.reconciled:
            #         #             amount = journal.debit
            #         #             for reconc_item in journal.full_reconcile_id:
            #         #                 if reconc_item.reconciled_line_ids:
            #         #                     for recon_line in reconc_item.reconciled_line_ids:
            #         #                         if recon_line.credit > 0:
            #         #                             reference = recon_line.move_id.name
            #         #                             # break
            #         #             for reconc_item in journal.matched_debit_ids:
            #         #                 if reconc_item.debit_move_id:
            #         #                     for recon_line in reconc_item.debit_move_id:
            #         #                         if recon_line.debit > 0:
            #         #                             reference = recon_line.move_id.name
            #         #             for reconc_item in journal.matched_credit_ids:
            #         #                 if reconc_item.credit_move_id:
            #         #                     for recon_line in reconc_item.credit_move_id:
            #         #                         if recon_line.credit > 0:
            #         #                             reference = recon_line.move_id.name
            #         #                             # break
            #         #             journal_docs.append({
            #         #                 'serial_no': serial_no,
            #         #                 'journal_no': journal.move_id.name,
            #         #                 'reference': reference,
            #         #                 'journal_date': journal.date,
            #         #                 'amount': amount,
            #         #                 'currency_id': doc.currency_id,
            #         #             })

            # if it is journal payment (only for migrated journal entries)
            elif doc.open_move_line_ids:
                # for journal_line in doc.open_move_line_ids:
                if doc.payment_type == 'outbound' and doc.move_reconciled:
                    journal_items = self.env['account.move.line'].search([
                        ('payment_id', '=', doc.id)
                    ])
                    serial_no += 1
                    # TODO
                    #  Add by Kinjal
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
            # Internal Transfer
            if doc.payment_type == 'transfer':
                internal_transfer_move_lines = self.env['account.move.line'].search(
                    [('payment_id', 'in', doc.ids)])
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

    @api.multi
    def get_partner_info(self, o):
        # get the vendor bank info
        account_number = ''
        bank_name = ''
        company = self.env['res.company'].browse(o.company_id)
        swift_code = ''
        if company:
            bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', o.id)
            ], limit=1)
            if bank:
                account_number = bank.acc_number
                bank_name = bank.bank_id.name
                swift_code = bank.swift_code

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
            'swift_code': swift_code,
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
                    bank = journal.bank_id.name
                if journal.bank_account_id:
                    account_number = journal.bank_account_id.acc_number

        bank_info = {
            'account_number': account_number,
            'bank': bank,
        }

        return bank_info

    @api.multi
    def get_payment_receipt_info(self, o, payment_type, total_en, total_amount, currency_id):
        payment_receipt_info = {
            'payment_receipt_no': o.name,
            'payment_receipt_date': o.payment_date,
            'payment_type': payment_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
            'cheque_no': o.cheque_no,
            'payment_ref': o.reference,
            'cheque_date': o.bank_date,
            'transfer_from_bank': o.journal_id.name,
            'transfer_to_bank': o.destination_journal_id.name,
            'payment_by': o.journal_id.name,
        }
        return payment_receipt_info
