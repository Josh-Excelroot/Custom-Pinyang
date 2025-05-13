# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import dateutil.relativedelta
from datetime import timedelta, date
import calendar
import math
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.misc import formatLang
from odoo.tools import float_round

class PrintJobSheet(models.AbstractModel):
    _name = 'report.sci_goexcel_job_sheet.report_job_sheet_details'
    _description = "Print Job Sheet"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['freight.booking'].browse(docids)
        cost_profit_ids = []
        invoice_ids = []
        info_ids = []
        for doc in docs:
            sale_total = 0
            cost_total = 0
            bol = self.env['freight.bol'].search([('booking_ref', '=', doc.id)])
            #invoices = self.env['account.invoice'].search([('freight_booking', '=', doc.id)])
            # Yulia 02042025 comment this part to prevent duplicate data
            # for bol_line in bol:
            #     for bol_cost_profit_line in bol_line.cost_profit_ids:
            #         cost_total = cost_total + bol_cost_profit_line.cost_total
            #         sale_total = sale_total + bol_cost_profit_line.sale_total
            #         cost_profit_ids.append({
            #             'product_id': bol_cost_profit_line.product_id.id,
            #             'product_name': bol_cost_profit_line.product_name,
            #             'costing': bol_cost_profit_line.cost_total,
            #             'billing': bol_cost_profit_line.sale_total,
            #         })
            for booking_cost_profit_line in doc.cost_profit_ids:
                # for pinyang, testing
                # if booking_cost_profit_line.cost_currency.name == 'MYR' and booking_cost_profit_line.profit_currency.name == 'USD':
                #     cost_total = cost_total + booking_cost_profit_line.cost_total
                #     sale_total = sale_total + (booking_cost_profit_line.sale_total * booking_cost_profit_line.profit_currency_rate)
                #     cost_profit_ids.append({
                #         'product_id': booking_cost_profit_line.product_id.id,
                #         'product_name': booking_cost_profit_line.product_name,
                #         'costing': booking_cost_profit_line.cost_total,
                #         'billing': (booking_cost_profit_line.sale_total * booking_cost_profit_line.profit_currency_rate),
                #     })
                # elif booking_cost_profit_line.cost_currency.name == 'USD' and booking_cost_profit_line.profit_currency.name == 'MYR':
                #     cost_total = cost_total + (booking_cost_profit_line.cost_total * booking_cost_profit_line.cost_currency_rate)
                #     sale_total = sale_total + booking_cost_profit_line.sale_total
                #     cost_profit_ids.append({
                #         'product_id': booking_cost_profit_line.product_id.id,
                #         'product_name': booking_cost_profit_line.product_name,
                #         'costing': (booking_cost_profit_line.cost_total * booking_cost_profit_line.cost_currency_rate),
                #         'billing': booking_cost_profit_line.sale_total,
                #     })
                # else:
                #     cost_total = cost_total + booking_cost_profit_line.cost_total
                #     sale_total = sale_total + booking_cost_profit_line.sale_total
                #     cost_profit_ids.append({
                #         'product_id': booking_cost_profit_line.product_id.id,
                #         'product_name': booking_cost_profit_line.product_name,
                #         'costing': booking_cost_profit_line.cost_total,
                #         'billing': booking_cost_profit_line.sale_total,
                #     })
                cost_total = cost_total + booking_cost_profit_line.cost_total
                sale_total = sale_total + booking_cost_profit_line.sale_total
                cost_profit_ids.append({
                    'product_id': booking_cost_profit_line.product_id.id,
                    'product_name': booking_cost_profit_line.product_name,
                    'costing': booking_cost_profit_line.cost_total,
                    'billing': booking_cost_profit_line.sale_total,
                })
                # print('>>>>>>> product_name: ', booking_cost_profit_line.product_name, ' , costing',
                #        booking_cost_profit_line.cost_total, ' , billing=',  booking_cost_profit_line.sale_total)
                # print('>>>>>>> cost_total=', cost_total, ' , sale_total=',  sale_total)
            for invoice in doc.booking_invoice_lines_ids:
                #for invoice in invoices:
                #print('>>>>>>>>> invoice_no=', invoice.invoice_no)
                if invoice.type == 'out_invoice' or invoice.type == 'in_invoice' or invoice.type == 'in_refund' or \
                        invoice.type == 'out_refund':
                    inv = self.env['account.invoice'].search([('number', '=', invoice.invoice_no),
                                                          ('state', '!=', 'cancel')], limit=1)
                elif invoice.type == 'purchase_receipt':
                    inv = self.env['account.voucher'].search([('number', '=', invoice.invoice_no),
                                                              ('state', '!=', 'cancel')], limit=1)
                type = ''
                term = ''
                if invoice.type == 'in_invoice':
                    type = 'Vendor Bill'
                    if inv.payment_term_id:
                        term = inv.payment_term_id.name
                    #check for back to back receipt, eg, custom duty, and update its costing
                    #for cost_profit in cost_profit_ids:


                        #if float_round(cost_profit['costing'], 2, rounding_method='HALF-UP') == \
                        #        float_round(invoice.invoice_amount, 2, rounding_method='HALF-UP'):
                            #print('>>>>>>>>> invoice no=', invoice.invoice_no, ' , cost_profit billing= ',
                            #      cost_profit['billing'], ' VS invoice amt=', invoice.invoice_amount)
                            #print('>>>>>>>>> cost_profit costing= ', cost_profit['costing'], ' VS invoice amt=',
                            #      invoice.invoice_amount)
                            #print('>>>>>>>>> cost_profit billing= ', cost_profit['billing'])
                            #if float_round(cost_profit['billing'], 2, rounding_method='HALF-UP') == 0.00:
                            #    cost_profit['billing'] = invoice.invoice_amount
                            #    sale_total += invoice.invoice_amount
                if invoice.type == 'out_invoice' and inv:
                    if inv.payment_term_id:
                        term = inv.payment_term_id.name
                    if inv.customer_debit_note == True:  # Customer Debit Note (freight booking job on the header)
                        #print('>>>>>>>>> invoice_no=', invoice.invoice_no)
                        type = 'Debit note'
                        line_ids = inv.invoice_line_ids
                        count = 0
                        #dn_subtotal = 0.00
                        skip=True
                        new_cost_profit_ids = []
                        sorted_cost_profit_ids = sorted(cost_profit_ids, key=lambda d: d['product_id'])
                        previous_ids = False
                        #previous_billing = 0.00
                        count = 0
                        index_count = 0
                        # for sorted_cost_profit in sorted_cost_profit_ids:
                        #     # print('product_id ', sorted_cost_profit['product_name'], ' , id=', sorted_cost_profit['product_id'],
                        #     #      ' VS previous_ids=', previous_ids)
                        #     if sorted_cost_profit['product_id'] == previous_ids and previous_ids is not False:
                        #         skip=True
                        #         #print('product_id ', sorted_cost_profit['product_name'], ' , billing=', sorted_cost_profit['billing'])
                        #         index_count +=1
                        #         # print('count=', str(count), ' vs index_count=', str(index_count), ', len new_profit_ids=',
                        #         #       str(len(new_cost_profit_ids)))
                        #         new_cost_profit_ids[count - index_count]['billing'] += sorted_cost_profit['billing']
                        #         #print('>>>DN Skip new cost profit=', new_cost_profit_ids[count-1]['billing'])
                        #     else:
                        #         previous_ids = sorted_cost_profit['product_id']
                        #         #previous_billing = sorted_cost_profit['billing']
                        #         new_cost_profit_ids.append(sorted_cost_profit)
                        #     count += 1
                        # # for new_cost_profit in new_cost_profit_ids:
                        #     for line_id in line_ids:
                        #         print('>>>>>>>Debit note 1 product=', new_cost_profit['product_name'])
                        #         if line_id.product_id.id == new_cost_profit['product_id']:
                        #             print('>>>>>>>Debit note 2 product=', line_id.product_id.name)
                        #             subtotal = new_cost_profit['billing']
                        #             print('>>>>>>>Debit note 3 subtotal=', subtotal, ' VS price_subtotal=', line_id.price_subtotal)
                        #             if subtotal != line_id.price_subtotal:
                        #                 print('>>>>>>>>> DN subtotal=', subtotal, ' , line total=', line_id.price_subtotal)
                        #                 new_cost_profit['billing'] = subtotal + line_id.price_subtotal
                        #                 #sale_total = sale_total + line_id.price_subtotal
                        #                 count = count+1
                        #                 break;
                        #     if count >0:
                        #         break;
                        if skip:
                            cost_profit_ids = new_cost_profit_ids
                        # for cost_profit in cost_profit_ids:
                        #     for line_id in line_ids:
                        #         if line_id and line_id.product_id:
                        #             print('>>>>>>>Debit note product=', cost_profit['product_name'])
                        #             if line_id.product_id.id == cost_profit['product_id']:
                        #                 if cost_profit['billing'] == line_id.price_subtotal:
                        #                     dn_subtotal += cost_profit['billing']
                        #                 print('>>>>>>> product=', cost_profit['product_name'])
                        #                 #subtotal = cost_profit['billing']
                        #                 #print('subtotal=', subtotal, ' , line total=', line_id.price_subtotal)
                        #                 #subtotal += line_id.price_subtotal
                        #                 cost_profit['billing'] = subtotal + line_id.price_subtotal
                        #                 sale_total = sale_total + line_id.price_subtotal
                        #             elif line_id.product_id.id != cost_profit['product_id']:
                        #
                        #                 count = count + 1
                        #                 break
                        #     if count == 1:
                        #         break
                        # if count == 1:  #If more than one, means there is a new row for CN
                        #     count=0
                        #     for cost_profit in cost_profit_ids:
                        #         for line_id in line_ids:
                        #             if line_id and line_id.product_id:
                        #                 if line_id.product_id.id == cost_profit['product_id']:
                        #                     subtotal = cost_profit['billing']
                        #                     subtotal += line_id.price_subtotal
                        #                     cost_profit['billing'] = subtotal
                        #                     sale_total = sale_total + line_id.price_subtotal
                        #                     #sale_total = sale_total + subtotal
                        #                     print('>>>>>>>>>>>>>DN sales_total=', sale_total, ' , subtotal=', subtotal)
                        #                     count = count+1
                        #                     break
                        #         if count ==1:
                        #             break

                    else:
                        type = 'Customer Invoice'
                        line_ids = inv.invoice_line_ids
                        # for cost_profit in cost_profit_ids:
                        #     for line_id in line_ids:
                        #         if line_id and line_id.product_id:
                        #             if line_id.product_id.id == cost_profit['product_id'] and cost_profit['billing'] == 0:
                        #                 #print('>>>>>>>>>>>>>Inv no=', inv.number)
                        #                 subtotal = cost_profit['billing']
                        #                 #print('>>>>>>>>>>>>>subtotal=', subtotal)
                        #                 if inv.currency_id.id != doc.company_id.currency_id.id and inv.exchange_rate_inverse:
                        #                     # Convert invoice line amount to company currency
                        #                     converted_subtotal = line_id.price_subtotal * inv.exchange_rate_inverse
                        #                     subtotal += converted_subtotal
                        #                     cost_profit['billing'] = subtotal
                        #                     sale_total = sale_total + converted_subtotal
                        #                 else:
                        #                     subtotal += line_id.price_subtotal
                        #                     #print('>>>>>>>>>>>>>product 1=', line_id.product_id.name, ' , subtotal=', subtotal,
                        #                     #      ' , line_id.price_subtotal=' , line_id.price_subtotal)
                        #                     cost_profit['billing'] = subtotal
                        #                     #sale_total += -line_id.price_subtotal
                        #                     sale_total = sale_total + line_id.price_subtotal
                        #                     # print('>>>>>>>>>>>>>Inv sales_total=', sale_total, ' , product=',
                        #                     #       line_id.product_id.name)
                        #                 break
                if invoice.type == 'in_refund':
                    type = 'Vendor CN'
                    if inv.payment_term_id:
                        term = inv.payment_term_id.name
                if invoice.type == 'out_refund':
                    if inv.payment_term_id:
                        term = inv.payment_term_id.name
                    type = 'Customer CN'
                    #line_ids = inv.invoice_line_ids
                    #count = 0
                    #TODO - TS 28/7/2022 fix Customer CN double entry
                    skip=True
                    new_cost_profit_ids = []
                    sorted_cost_profit_ids = sorted(cost_profit_ids, key=lambda d: d['product_id'])
                    previous_ids = False
                    count = 0
                    index_count = 0
                    # for sorted_cost_profit in sorted_cost_profit_ids:
                    #     if sorted_cost_profit['product_id'] == previous_ids and previous_ids is not False:
                    #         skip=True
                    #         # print('product_id ', sorted_cost_profit['product_name'], ' , billing=',
                    #         #       sorted_cost_profit['billing'])
                    #         index_count +=1
                    #         # print('count=', str(count), ' vs index_count=', str(index_count), ', len new_profit_ids=',
                    #         #       str(len(new_cost_profit_ids)))
                    #         new_cost_profit_ids[count - index_count]['billing'] += sorted_cost_profit['billing']
                    #         #print('>>>CN Skip new cost profit=', new_cost_profit_ids[count-1]['billing'])
                    #     else:
                    #         previous_ids = sorted_cost_profit['product_id']
                    #         #previous_billing = sorted_cost_profit['billing']
                    #         new_cost_profit_ids.append(sorted_cost_profit)
                    #     count += 1
                    # if skip:
                    #     cost_profit_ids = new_cost_profit_ids

                    # for cost_profit in cost_profit_ids:
                    #     for line_id in line_ids:
                    #         if line_id and line_id.name:
                    #             if line_id.name == cost_profit['product_name']:
                    #                 count = count + 1
                    # if count == 1:  #If more than one, means there is a new row for CN
                    #     for cost_profit in cost_profit_ids:
                    #         for line_id in line_ids:
                    #             if line_id and line_id.name:
                    #                 if line_id.name == cost_profit['product_name']:
                    #                     subtotal = cost_profit['billing']
                    #                     subtotal += -line_id.price_subtotal
                    #                     cost_profit['billing'] = subtotal
                    #                     sale_total += -line_id.price_subtotal
                    #                     break
                if invoice.type == 'out_refund':
                    type = 'Customer CN'
                    if inv.payment_term_id:
                        term = inv.payment_term_id.name
                if invoice.type == 'purchase_receipt' and inv:
                    type = 'Purchase Receipt'

                    #for line in inv.line_ids:
                    #    print('>>>>>>>>line.freight_booking.id=', line.freight_booking.id)
                    line_id = inv.line_ids.filtered(lambda r: r.freight_booking.id == doc.id)
                    #print('>>>>>>>> Purchase Receipt=', line_id.product_id)
                    #check for back to back receipt, eg, custom duty, and update its costing
                    # for cost_profit in cost_profit_ids:
                    #     if line_id and line_id.product_id:
                    #         #print('>>>>>>>> Purchase Receipt product_id=', line_id.product_id.id, ' VS ',
                    #         #        cost_profit['product_id'])
                    #         if line_id.product_id.id == cost_profit['product_id'] and \
                    #                 float_round(cost_profit['costing'], 2, rounding_method='HALF-UP') == 0:
                    #             cost_profit['costing'] = line_id.price_subtotal
                    #             cost_total += line_id.price_subtotal
                    #             break
                    #     elif float_round(cost_profit['billing'], 2, rounding_method='HALF-UP') == \
                    #             float_round(invoice.invoice_amount, 2, rounding_method='HALF-UP'):
                    #         cost_profit['costing'] = invoice.invoice_amount
                    #         cost_total += invoice.invoice_amount
                    #         break
                if inv: # added this, josh
                    original_amount = inv.amount_total
                    
                    invoice_ids.append({
                        'type': type,
                        'partner_id': inv.partner_id.name,
                        'number': invoice.invoice_no,
                        'term': term,
                        'currency_id': inv.currency_id.name,
                        'amount_total': original_amount,
                    })
            # for invoice in invoices:
            #     if invoice.type == 'in_invoice':
            #         type = 'Vendor Bill'
            #     if invoice.type == 'out_invoice':
            #         type = 'Customer Invoice'
            #     invoice_ids.append({
            #         'type': type,
            #         'partner_id': invoice.partner_id.name,
            #         'number': invoice.number,
            #         'currency_id': invoice.currency_id.name,
            #         'amount_total': float(invoice.amount_total),
            #     })
            margin = 0
            if cost_total == 0:
                margin = sale_total*100
            if cost_total > 0:
                #print('>>>>>>>> Margin Cost_total=', cost_total, ' sale_total=', sale_total)
                if sale_total>0:
                    margin = (sale_total-cost_total)/sale_total*100
                #print('>>>>>>>> Margin =', margin)
            profit = sale_total - cost_total

            info_ids.append({
                'cost_total': cost_total,
                'sale_total': sale_total,
                'margin': margin,
                'profit': profit,
            })
            #print(cost_profit_ids)
            #print(invoice_ids)
            #print(docs)
        return{
            'doc_ids': docs.ids,
            'doc_model': 'freight.booking',
            'docs': docs,
            'cost_profit_ids1': cost_profit_ids,
            'invoice_ids1': invoice_ids,
            'info_ids1': info_ids,
        }
