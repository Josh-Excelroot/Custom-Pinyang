# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from lxml import etree
import logging

from odoo import api, models , fields
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import UserError
import datetime
from decimal import Decimal


logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'base.ubl']

    @api.multi
    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        now_utc = fields.Datetime.to_string(fields.Datetime.now())
        date = now_utc[:10]
        time = now_utc[11:]
        # ubl_version = etree.SubElement(
        #     parent_node, ns['cbc'] + 'UBLVersionID')
        # ubl_version.text = version
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        doc_id.text = self.number
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        if self.date_invoice and self.date_invoice > datetime.date.today():
            raise UserError("E-Invoice prohibits the invoice date in the future. Please Correct it!")
        # issue_date.text = self.date_invoice.strftime('%Y-%m-%d')
        issue_date.text = datetime.datetime.utcnow().strftime('%Y-%m-%d')

        issue_time = etree.SubElement(parent_node, ns['cbc'] + 'IssueTime')
        # issue_time.text = self.create_date.strftime('%H:%M:%SZ')
        issue_time.text = datetime.datetime.utcnow().strftime('%H:%M:%SZ')


        type_code = etree.SubElement(
            parent_node, ns['cbc'] + 'InvoiceTypeCode' , listVersionID="1.0")
        if self.type == 'out_invoice':
            type_code.text = '01'
        if self.type == 'out_refund':
            type_code.text = '02'
        if self.type == 'out_invoice' and self.journal_id.type == 'sale'and self.customer_debit_note and self.debit_invoice_id !=False:
            type_code.text = '03'
        if self.type == 'out_refund' and self.e_invoice_refund_note:
            type_code.text = '04'
        if self.type == 'in_invoice':
            type_code.text = '11'
        if self.type == 'in_invoice' and self.journal_id.type == 'purchase' and self.customer_debit_note and self.debit_invoice_id !=False:
            type_code.text = '13'
        if self.type == 'in_refund':
            type_code.text = '12'
        if self.type == 'in_refund' and self.e_invoice_refund_note:
            type_code.text = '14'
        if self.comment:
            note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note.text = self.comment
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name

    @api.multi
    def _ubl_add_order_reference(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        if self.name:
            order_ref = etree.SubElement(
                parent_node, ns['cac'] + 'OrderReference')
            order_ref_id = etree.SubElement(
                order_ref, ns['cbc'] + 'ID')
            order_ref_id.text = self.name

    @api.multi
    def _ubl_add_billing_reference(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        if self.type == 'out_refund':
            if self.refund_invoice_id:
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                if self.refund_invoice_id.move_name:
                    ref_id.text = self.refund_invoice_id.move_name
                else:
                    ref_id.text = 'NA'
                if self.refund_invoice_id.uuid:
                    ref_uuid.text = self.refund_invoice_id.uuid
                else:
                    ref_uuid.text = 'NA'
                    # raise UserError("Please first, send the invoice to the e-invoice portal.")
            else:
                # /////////////////////////////////
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                ref_id.text = 'NA'
                ref_uuid.text = 'NA'
                # raise UserError("This credit note (CN) will not be sent to the e-invoice portal because it is not linked to any invoice")
                # /////////////////////////////////

        if self.type == 'out_invoice' and self.journal_id.type == 'sale' and self.customer_debit_note and self.debit_invoice_id != False :
            if self.debit_invoice_id:
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                if self.debit_invoice_id.move_name:
                    ref_id.text = self.debit_invoice_id.move_name
                else:
                    ref_id.text = 'NA'
                if self.debit_invoice_id.uuid:
                    ref_uuid.text = self.debit_invoice_id.uuid
                else:
                    ref_uuid.text = 'NA'
                    # raise UserError("Please first, send the invoice to the e-invoice portal.")
            else:
                # /////////////////////////////////
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                ref_id.text = 'NA'
                ref_uuid.text = 'NA'

                # raise UserError(
                #     "This debit note (DN) will not be sent to the e-invoice portal because it is not linked to any invoice")
                # /////////////////////////////////

        if self.type == 'in_invoice' and self.journal_id.type == 'purchase' and self.customer_debit_note and self.debit_invoice_id != False:
            if self.debit_invoice_id:
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                if self.debit_invoice_id.move_name:
                    ref_id.text = self.debit_invoice_id.move_name
                else:
                    ref_id.text = 'NA'
                if self.debit_invoice_id.uuid:
                    ref_uuid.text = self.debit_invoice_id.uuid
                else:
                    ref_uuid.text = 'NA'
                    # raise UserError("Please first, send the bill to the e-invoice portal.")
            else:
                # /////////////////////////////////
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                ref_id.text = 'NA'
                ref_uuid.text = 'NA'

                # raise UserError(
                #     "This debit note (DN) will not be sent to the e-invoice portal because it is not linked to any bill")
                # /////////////////////////////////
        if self.type == 'in_refund':
            if self.refund_invoice_id:
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                if self.refund_invoice_id.move_name:
                    ref_id.text = self.refund_invoice_id.move_name
                else:
                    ref_id.text = 'NA'
                if self.refund_invoice_id.uuid:
                    ref_uuid.text = self.refund_invoice_id.uuid
                else:
                    ref_uuid.text = 'NA'
                    # raise UserError("Please first, send the bill to the e-invoice portal.")
            else:
                # /////////////////////////////////
                billing_ref = etree.SubElement(
                    parent_node, ns['cac'] + 'BillingReference')

                invoice_doc_ref = etree.SubElement(
                    billing_ref, ns['cac'] + 'InvoiceDocumentReference')

                ref_id = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'ID')

                ref_uuid = etree.SubElement(
                    invoice_doc_ref, ns['cbc'] + 'UUID')

                ref_id.text = 'NA'
                ref_uuid.text = 'NA'

                # raise UserError(
                #     "This Refund will not be sent to the e-invoice portal because it is not linked to any bill")
                # /////////////////////////////////
    @api.multi
    def _ubl_get_contract_document_reference_dict(self):
        '''Result: dict with key = Doc Type Code, value = ID'''
        self.ensure_one()
        return {}

    @api.multi
    def _ubl_add_contract_document_reference(
            self, parent_node, ns, version='2.1'):
        self.ensure_one()
        cdr_dict = self._ubl_get_contract_document_reference_dict()
        for doc_type_code, doc_id in cdr_dict.items():
            cdr = etree.SubElement(
                parent_node, ns['cac'] + 'ContractDocumentReference')
            cdr_id = etree.SubElement(cdr, ns['cbc'] + 'ID')
            cdr_id.text = doc_id
            cdr_type_code = etree.SubElement(
                cdr, ns['cbc'] + 'DocumentTypeCode')
            cdr_type_code.text = doc_type_code

    @api.multi
    def _ubl_add_attachments(self, parent_node, ns, version='2.1'):
        if (
                self.company_id.embed_pdf_in_ubl_xml_invoice and
                not self._context.get('no_embedded_pdf')):
            filename = 'Invoice-' + self.number + '.pdf'
            docu_reference = etree.SubElement(
                parent_node, ns['cac'] + 'AdditionalDocumentReference')
            docu_reference_id = etree.SubElement(
                docu_reference, ns['cbc'] + 'ID')
            docu_reference_id.text = filename
            attach_node = etree.SubElement(
                docu_reference, ns['cac'] + 'Attachment')
            binary_node = etree.SubElement(
                attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
                mimeCode="application/pdf", filename=filename)
            ctx = dict()
            ctx['no_embedded_ubl_xml'] = True
            pdf_inv = self.with_context(ctx).env.ref(
                'account.account_invoices').render_qweb_pdf(self.ids)[0]
            binary_node.text = base64.b64encode(pdf_inv)

    @api.multi
    def _ubl_add_legal_monetary_total(self, parent_node, ns, version='2.1'):
        monetary_total = etree.SubElement(
            parent_node, ns['cac'] + 'LegalMonetaryTotal')
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        prec = prec if prec <= 2 else 2
        line_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_total.text = '%0.*f' % (prec, self.amount_untaxed)
        tax_excl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxExclusiveAmount',
            currencyID=cur_name)
        tax_excl_total.text = '%0.*f' % (prec, self.amount_untaxed)
        tax_incl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxInclusiveAmount',
            currencyID=cur_name)
        tax_incl_total.text = '%0.*f' % (prec, self.amount_total)
        prepaid_amount = etree.SubElement(
            monetary_total, ns['cbc'] + 'PrepaidAmount',
            currencyID=cur_name)
        prepaid_value = self.amount_total - self.residual
        prepaid_amount.text = '%0.*f' % (prec, prepaid_value)
        payable_amount = etree.SubElement(
            monetary_total, ns['cbc'] + 'PayableAmount',
            currencyID=cur_name)
        payable_amount.text = '%0.*f' % (prec, self.residual)

    @api.multi
    def _ubl_add_invoice_line(
            self, parent_node, iline, line_number, ns, version='2.1'):
        cur_name = self.currency_id.name
        line_root = etree.SubElement(
            parent_node, ns['cac'] + 'InvoiceLine')
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        price_precision = dpo.precision_get('Product Price')
        price_precision = price_precision if price_precision <= 2 else 2
        account_precision = self.currency_id.decimal_places
        account_precision = account_precision if account_precision <= 2 else 2
        line_id = etree.SubElement(line_root, ns['cbc'] + 'ID')
        line_id.text = str(line_number)
        uom_unece_code = False

        # uom_id is not a required field on account.invoice.line
        # if iline.uom_id and iline.uom_id.unece_code:
        #     uom_unece_code = iline.uom_id.unece_code
        # if uom_unece_code:
        #     quantity = etree.SubElement(
        #         line_root, ns['cbc'] + 'InvoicedQuantity',
        #         unitCode=uom_unece_code)
        # else:
        #     quantity = etree.SubElement(
        #         line_root, ns['cbc'] + 'InvoicedQuantity')
        qty = iline.quantity
        # quantity.text = '%0.*f' % (qty_precision, qty)

        try:
            if iline.uom_id and iline.uom_id.uom_code:
                quantity = etree.SubElement(
                    line_root, ns['cbc'] + 'InvoicedQuantity', unitCode=iline.uom_id.uom_code.uom_code)
                quantity.text = qty = str(Decimal(iline.quantity).quantize(Decimal('0.00')))
            else:
                quantity = etree.SubElement(
                    line_root, ns['cbc'] + 'InvoicedQuantity', unitCode="XUN")
                quantity.text = qty = str(Decimal(iline.quantity).quantize(Decimal('0.00')))
        except:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + 'InvoicedQuantity', unitCode="XUN")
            quantity.text = qty = str(Decimal(iline.quantity).quantize(Decimal('0.00')))


        line_amount = etree.SubElement(
            line_root, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_amount.text = '%0.*f' % (account_precision, iline.price_subtotal)


        # ////////////////////////////////////////////////////////
        try:
            if iline.discount:
                allowanceCharge = etree.SubElement(
                    line_root, ns['cac'] + 'AllowanceCharge')

                chargeIndicator = etree.SubElement(
                    allowanceCharge, ns['cbc'] + 'ChargeIndicator')
                chargeIndicator.text = "false"

                allowanceChargeReason = etree.SubElement(
                    allowanceCharge, ns['cbc'] + 'AllowanceChargeReason')
                allowanceChargeReason.text = "false"

                multiplierFactorNumeric = etree.SubElement(
                    allowanceCharge, ns['cbc'] + 'MultiplierFactorNumeric')
                multiplierFactorNumeric.text = str(iline.discount / 100)

                amount = etree.SubElement(
                    allowanceCharge, ns['cbc'] + 'Amount', currencyID=cur_name)
                # amount.text = str((iline.discount / 100) * (iline.price_subtotal))
                amount.text = str(round((iline.discount / 100) * (iline.quantity*iline.price_unit), 2))

        except:
            pass

        # ////////////////////////////////////////////////////////

        self._ubl_add_invoice_line_tax_total(
            iline, line_root, ns, version=version)
        self._ubl_add_item(
            iline.name, iline.product_id, line_root, ns, type='sale',
            version=version)
        price_node = etree.SubElement(line_root, ns['cac'] + 'Price')
        price_amount = etree.SubElement(
            price_node, ns['cbc'] + 'PriceAmount', currencyID=cur_name)
        price_unit = 0.0
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        if not float_is_zero(float(qty), precision_digits=qty_precision):
            price_unit = float_round(
                iline.price_subtotal / float(qty),
                precision_digits=price_precision)
        price_amount.text = '%0.*f' % (price_precision, price_unit)

        # //////////////////
        item_price_extension = etree.SubElement(
            line_root, ns['cac'] + 'ItemPriceExtension')
        item_price_extension_amount = etree.SubElement(
            item_price_extension, ns['cbc'] + 'Amount',
            currencyID=cur_name)
        item_price_extension_amount.text = str(Decimal(iline.price_subtotal).quantize(Decimal('0.00')))
        # //////////////////
        # if uom_unece_code:
        #     base_qty = etree.SubElement(
        #         price_node, ns['cbc'] + 'BaseQuantity',
        #         unitCode=uom_unece_code)
        # else:
        #     base_qty = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity')
        # base_qty.text = '%0.*f' % (qty_precision, qty)

    def _ubl_add_invoice_line_tax_total(
            self, iline, parent_node, ns, version='2.1'):
        # /////////////////////
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        prec = prec if prec <= 2 else 2
        tax_total_node = etree.SubElement(parent_node, ns['cac'] + 'TaxTotal')
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        res_taxes = iline.invoice_line_tax_ids.compute_all(
            price, quantity=iline.quantity, product=iline.product_id,
            partner=self.partner_id)
        tax_total = float_round(
            res_taxes['total_included'] - res_taxes['total_excluded'],
            precision_digits=prec)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = '%0.*f' % (prec, tax_total)

        if self.fiscal_position_id and res_taxes['taxes']:
            if res_taxes['taxes'][0]['amount'] == 0:
                for res_tax in res_taxes['taxes']:
                    tax = self.env['account.tax'].browse(res_tax['id'])
                    # we don't have the base amount in res_tax :-(
                    self._ubl_add_tax_subtotal(
                        res_tax['base'], res_tax['amount'], tax, cur_name, tax_total_node,
                        ns, version=version)
            else:
                if not float_is_zero(tax_total, precision_digits=prec):
                    for res_tax in res_taxes['taxes']:
                        tax = self.env['account.tax'].browse(res_tax['id'])
                        # we don't have the base amount in res_tax :-(
                        self._ubl_add_tax_subtotal(
                            res_tax['base'], res_tax['amount'], tax, cur_name, tax_total_node,
                            ns, version=version)
                else:
                    tax = self.env['account.tax'].sudo().search([('name', '=', 'Tax 0 %')])
                    if tax:
                        for index, tline in enumerate(self.invoice_line_ids):
                            if index == 0:
                                self._ubl_add_tax_subtotal(
                                    tax.amount, tax.amount, tax, cur_name,
                                    tax_total_node, ns, version=version)
                            else:
                                break

                    else:
                        # unece = self.env['unece.code.list'].search([('name', '=', 'Tax Exemption')])
                        unece = self.env.ref('account_tax_unece.tax_categ_e')
                        if self.type == 'out_invoice' or self.type == 'out_refund':
                            tax = self.env['account.tax'].sudo().create({
                                'name': 'Tax 0 %',
                                'amount': 0.0,
                                'amount_type': 'percent',
                                'type_tax_use': 'sale',
                                'unece_type_id': unece.id,
                                'unece_categ_id': unece.id
                            })
                        if self.type == 'in_invoice' or self.type == 'in_refund':
                            tax = self.env['account.tax'].sudo().create({
                                'name': 'Tax 0 %',
                                'amount': 0.0,
                                'amount_type': 'percent',
                                'type_tax_use': 'purchase',
                                'unece_type_id': unece.id,
                                'unece_categ_id': unece.id
                            })

                        for index, tline in enumerate(self.invoice_line_ids):
                            if index == 0:
                                self._ubl_add_tax_subtotal(
                                    tax.amount, tax.amount, tax, cur_name,
                                    tax_total_node, ns, version=version)
                            else:
                                break

                # //////////////////////////
        else:
            if not float_is_zero(tax_total, precision_digits=prec):
                for res_tax in res_taxes['taxes']:
                    tax = self.env['account.tax'].browse(res_tax['id'])
                    # we don't have the base amount in res_tax :-(
                    self._ubl_add_tax_subtotal(
                        res_tax['base'], res_tax['amount'], tax, cur_name, tax_total_node,
                        ns, version=version)
            else:
                tax = self.env['account.tax'].sudo().search([('name',  '=',  'Tax 0 %')])
                if tax:
                    for index, tline in enumerate(self.invoice_line_ids):
                        if index == 0:
                            self._ubl_add_tax_subtotal(
                                tax.amount, tax.amount, tax, cur_name,
                                tax_total_node, ns, version=version)
                        else:
                            break

                else:
                    # unece = self.env['unece.code.list'].search([('name', '=', 'Tax Exemption')])
                    unece = self.env.ref('account_tax_unece.tax_categ_e')
                    if self.type == 'out_invoice' or self.type == 'out_refund':
                        tax = self.env['account.tax'].sudo().create({
                            'name': 'Tax 0 %',
                            'amount': 0.0,
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                            'unece_type_id': unece.id,
                            'unece_categ_id': unece.id
                        })
                    if self.type == 'in_invoice' or self.type == 'in_refund':
                        tax = self.env['account.tax'].sudo().create({
                            'name': 'Tax 0 %',
                            'amount': 0.0,
                            'amount_type': 'percent',
                            'type_tax_use': 'purchase',
                            'unece_type_id': unece.id,
                            'unece_categ_id': unece.id
                        })

                    for index, tline in enumerate(self.invoice_line_ids):
                        if index == 0:
                            self._ubl_add_tax_subtotal(
                                tax.amount, tax.amount, tax, cur_name,
                                tax_total_node, ns, version=version)
                        else:
                            break

    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        self.ensure_one()
        cur_name = self.currency_id.name
        tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        prec = self.currency_id.decimal_places
        prec = prec if prec <= 2 else 2
        tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
        if not float_is_zero(self.amount_tax, precision_digits=prec):
            self._ubl_add_tax_subtotal(
                self.amount_tax, self.amount_tax, False, cur_name,
                tax_total_node, ns, version=version)
            # for tline in self.tax_line_ids:
            #     self._ubl_add_tax_subtotal(
            #         tline.base, tline.amount, tline.tax_id, cur_name,
            #         tax_total_node, ns, version=version)
        else:
            tax = self.env['account.tax'].sudo().search([('name',  '=',  'Tax 0 %')])
            if tax:
                for index, tline in enumerate(self.invoice_line_ids):
                    if index == 0:
                        self._ubl_add_tax_subtotal(
                            tax.amount, tax.amount, tax, cur_name,
                            tax_total_node, ns, version=version)
                    else:
                        break

            else:
                # unece  = self.env['unece.code.list'].search([('name' , '=' , 'Tax Exemption')])
                unece = self.env.ref('account_tax_unece.tax_categ_e')

                if self.type == 'out_invoice' or self.type == 'out_refund':
                    tax = self.env['account.tax'].sudo().create({
                        'name': 'Tax 0 %',
                        'amount': 0.0,
                        'amount_type': 'percent',
                        'type_tax_use': 'sale',
                        'unece_type_id': unece.id,
                        'unece_categ_id': unece.id
                    })
                if self.type == 'in_invoice' or self.type == 'in_refund':
                    tax = self.env['account.tax'].sudo().create({
                        'name': 'Tax 0 %',
                        'amount': 0.0,
                        'amount_type': 'percent',
                        'type_tax_use': 'purchase',
                        'unece_type_id': unece.id,
                        'unece_categ_id': unece.id
                    })

                for index, tline in enumerate(self.invoice_line_ids):
                    if index == 0:
                        self._ubl_add_tax_subtotal(
                            tax.amount, tax.amount, tax, cur_name,
                            tax_total_node, ns, version=version)
                    else:
                        break

    # def _ubl_add_invoice_period(self, xml_root, ns, version='2.1'):
    #     self.ensure_one()
    #     cur_name = self.currency_id.name
    #     invoice_period_node = etree.SubElement(xml_root, ns['cac'] + 'InvoicePeriod')
    #     invoice_period_issuedate_node = etree.SubElement(
    #         invoice_period_node, ns['cbc'] + 'IssueDate', currencyID=cur_name)
    #     invoice_period_issuedate_node.text = self.date_invoice.strftime('%Y-%m-%d')
        # invoice_period_enddate_node = etree.SubElement(
        #     invoice_period_node, ns['cbc'] + 'EndDate', currencyID=cur_name)
        # invoice_period_enddate_node.text = self.date_due.strftime('%Y-%m-%d')
        # invoice_period_description_node = etree.SubElement(
        #     invoice_period_node, ns['cbc'] + 'Description', currencyID=cur_name)
        # invoice_period_description_node.text = "Monthly"

    @api.multi
    def _ubl_add_invoice_period(self, parent_node, ns, version='2.1'):
        period_root = etree.SubElement(
            parent_node, ns['cac'] + 'InvoicePeriod')
        issue_date = etree.SubElement(period_root, ns['cbc'] + 'StartDate')
        if self.date_invoice and self.date_invoice > datetime.date.today():
            raise UserError("E-Invoice prohibits the invoice date in the future. Please Correct it!")
        issue_date.text = self.date_invoice.strftime('%Y-%m-%d')
        end_date = etree.SubElement(period_root, ns['cbc'] + 'EndDate')
        end_date.text = self.date_due.strftime('%Y-%m-%d')

    @api.multi
    def _ubl_tax_exchange_rate(self, parent_node, ns, version='2.1'):

        if self.currency_id.name != 'MYR':
            taxexchangerate_root = etree.SubElement(
                parent_node, ns['cac'] + 'TaxExchangeRate')
            sourcecurrencycode = etree.SubElement(
                taxexchangerate_root, ns['cbc'] + 'SourceCurrencyCode')
            sourcecurrencycode.text = self.currency_id.name
            targetcurrencycode = etree.SubElement(
                taxexchangerate_root, ns['cbc'] + 'TargetCurrencyCode')
            targetcurrencycode.text = 'MYR'
            calculation_rate = etree.SubElement(
                taxexchangerate_root, ns['cbc'] + 'CalculationRate')
            calculation_rate.text = str(self.exchange_rate_inverse) if self.exchange_rate_inverse else '0.0'


    @api.multi
    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        # ////////////////////////// default
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        self._ubl_add_header(xml_root, ns, version=version)
        # self._ubl_tax_exchange_rate(xml_root, ns, version=version)
        self._ubl_add_invoice_period(xml_root, ns, version=version)
        self._ubl_add_order_reference(xml_root, ns, version=version)
        self._ubl_add_billing_reference(xml_root, ns, version=version)
        self._ubl_add_contract_document_reference(
            xml_root, ns, version=version)
        self._ubl_add_attachments(xml_root, ns, version=version)
        self._ubl_add_supplier_party(
            False, self.company_id, 'AccountingSupplierParty', xml_root, ns,
            version=version)
        self._ubl_add_customer_party(
            self.partner_id, False, 'AccountingCustomerParty', xml_root, ns,
            version=version)
        # the field 'partner_shipping_id' is defined in the 'sale' module
        if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
            self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
        # Put paymentmeans block even when invoice is paid ?
        payment_identifier = self.get_payment_identifier()
        self._ubl_add_payment_means(
            self.partner_bank_id, self.payment_mode_id, self.date_due,
            xml_root, ns, payment_identifier=payment_identifier,
            version=version)
        if self.payment_term_id:
            self._ubl_add_payment_terms(
                self.payment_term_id, xml_root, ns, version=version)

        self._ubl_tax_exchange_rate(xml_root, ns, version=version)

        self._ubl_add_tax_total(xml_root, ns, version=version)
        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        for iline in self.invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(
                xml_root, iline, line_number, ns, version=version)
        return xml_root

    @api.multi
    def generate_ubl_xml_string(self, version='2.1'):
        # ////////////////// default
        self.ensure_one()
        # assert self.state in ('open', 'paid')
        # assert self.type in ('out_invoice', 'out_refund')
        logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        xml_root = self.with_context(lang=lang).\
            generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8')
        self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID %d '
            '(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string

    @api.multi
    def get_ubl_filename(self, version='2.1'):
        """This method is designed to be inherited"""
        return 'UBL-Invoice-%s.xml' % version

    @api.multi
    def get_ubl_version(self):
        version = self._context.get('ubl_version') or '2.1'
        return version

    @api.multi
    def get_ubl_lang(self):
        return self.partner_id.lang or 'en_US'

    @api.multi
    def embed_ubl_xml_in_pdf(self, pdf_content=None, pdf_file=None):
        self.ensure_one()
        if (
                self.type in ('out_invoice', 'out_refund' , 'in_invoice') and
                self.state in ('open', 'paid')):
            version = self.get_ubl_version()
            ubl_filename = self.get_ubl_filename(version=version)
            xml_string = self. generate_ubl_xml_string(version=version)
            pdf_content = self.embed_xml_in_pdf(
                xml_string, ubl_filename,
                pdf_content=pdf_content, pdf_file=pdf_file)
        return pdf_content

    @api.multi
    def attach_ubl_xml_file_button(self):
        self.ensure_one()
        # assert self.type in ('out_invoice', 'out_refund')
        # assert self.state in ('open', 'paid')
        if self.state not in ('open', 'paid'):
            raise UserError("Invoice must be in open or paid state")
        version = self.get_ubl_version()
        xml_string = self.generate_ubl_xml_string(version=version)
        filename = self.get_ubl_filename(version=version)
        ctx = {}
        attach = self.env['ir.attachment'].with_context(ctx).sudo().create({
            'name': filename,
            'res_id': self.id,
            'res_model': str(self._name),
            'datas': base64.b64encode(xml_string),
            'datas_fname': filename,
            # I have default_type = 'out_invoice' in context, so 'type'
            # would take 'out_invoice' value by default !
            'type': 'binary',
            })
        action = self.env['ir.actions.act_window'].for_xml_id(
            'base', 'action_attachment')
        action.update({
            'res_id': attach.id,
            'views': False,
            'view_mode': 'form,tree'
            })
        return action
