# -*- coding: utf-8 -*-
from odoo.tools import float_is_zero
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PrintCN(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_cn'
    _description = "Print Payment Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.invoice'].browse(docids)
        payment_docs = []
        for doc in docs:
            payment_docs = self._get_payment_lines(doc)
        return {
            'docs': docs,
            'payment_lines': payment_docs,
        }

    @api.model
    def _get_payment_lines(self, inv):
        if not inv.payment_move_line_ids:
            return []
        payment_vals = []
        currency_id = inv.currency_id
        for payment in inv.payment_move_line_ids:
            payment_currency_id = False
            if inv.type in ('out_invoice', 'in_refund'):
                amount = sum(
                    [p.amount for p in payment.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
                amount_currency = sum(
                    [p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
                if payment.matched_debit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in
                                               payment.matched_debit_ids]) and payment.matched_debit_ids[
                        0].currency_id or False
            elif inv.type in ('in_invoice', 'out_refund'):
                amount = sum(
                    [p.amount for p in payment.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if
                                       p.credit_move_id in inv.move_id.line_ids])
                if payment.matched_credit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in
                                               payment.matched_credit_ids]) and payment.matched_credit_ids[
                        0].currency_id or False
            # get the payment value in invoice currency
            if payment_currency_id and payment_currency_id == inv.currency_id:
                amount_to_show = amount_currency
            else:
                currency = payment.company_id.currency_id
                amount_to_show = currency._convert(amount, inv.currency_id, payment.company_id,
                                                   payment.date or fields.Date.today())
            if float_is_zero(amount_to_show, precision_rounding=inv.currency_id.rounding):
                continue
            payment_ref = payment.move_id.name
            if payment.move_id.ref:
                payment_ref += ' (' + payment.move_id.ref + ')'
            payment_vals.append({
                'payment_date': payment.date,
                'inv_date': payment.invoice_id.date_invoice,
                'inv_no': payment.invoice_id.number,
                'ref': payment_ref,
                'inv_amount': payment.invoice_id.amount_total,
                'amount_paid': amount_to_show,
                'balance': payment.invoice_id.residual,
                'currency_id': currency_id,
            })
        return payment_vals