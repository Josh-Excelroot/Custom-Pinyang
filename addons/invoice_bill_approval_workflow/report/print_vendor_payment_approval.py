# -*- coding: utf-8 -*-
from odoo.tools import float_is_zero
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PrintVendorPayment(models.AbstractModel):
    _name = 'report.invoice_bill_approval_workflow.report_vendor_payment'
    _description = "Print Vendor Payment Approval"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        #print('>>>>>>>>>>>>>> Vendor Payment Approval')
        docs = self.env['account.payment'].browse(docids)
        payment_docs = []
        serial_no = 0
        if docs:
            company = self.env['res.company'].browse(docs[0].company_id.id)
            company_info = {
                'name': company.name,
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
        for doc in docs:
            reference = ''
            if doc.payment_type == 'outbound':
                serial_no += 1
                for inv in doc.payment_invoice_ids:
                    if inv.reconcile_amount > 0 and inv.reference:
                        reference += inv.reference + ' '
                payment_docs.append({
                    'serial_no': serial_no,
                    'pv_no': doc.name,
                    'partner': doc.partner_id.name,
                    'date': doc.payment_date,
                    'reference': reference,
                    'amount': doc.amount,
                    'currency_id': doc.currency_id,
                })

        #print('>>>>>>>>>>>>>> Vendor Payment Approval 2 len=', len(payment_docs))
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payment_docs,
            'company_info': company_info,
        }

