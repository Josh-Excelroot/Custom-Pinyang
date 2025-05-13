from odoo import api, fields, models, exceptions,_
import logging
from datetime import date
from odoo.tools import float_round


class RFTInvoice(models.Model):

    _inherit = 'account.invoice'

    rft_id = fields.Many2one('transport.rft', string='RFT No', readonly=True)


    @api.model
    def create(self, vals):
        if vals.get('type') == 'in_refund' or vals.get('type') == 'out_refund' or vals.get('type') == 'in_invoice' or \
                (vals.get('type') == 'out_invoice' and vals.get('customer_debit_note')):
            if self.rft_id:
                vals.update({'rft_id': self.rft_id.id})
        if self.company_id.currency_id != self.currency_id:
            vals.update({'comment': self.env.user.company_id.invoice_note_foreign_currency})
        else:
            vals.update({'comment': self.env.user.company_id.invoice_note})
        res = super(RFTInvoice, self).create(vals)
        return res


    # @api.multi
    # def write(self, vals):
    #     currency = self.env['res.currency'].browse(vals.get('currency_id'))
    #
    #     #Refund
    #     for record in self:
    #         if vals.get('state') == 'open' and (record.type == 'in_refund' or record.type == 'out_refund'):
    #             for invoice_line in record.invoice_line_ids:
    #                 price_unit = 0.000000
    #                 freight_currency_rate = 1.000000
    #                 currency_id = 0
    #                 if record.company_id.currency_id != record.currency_id:
    #                     if record.exchange_rate_inverse:
    #                         price_unit = invoice_line.price_unit
    #                         freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
    #                         currency_id = invoice_line.invoice_id.currency_id
    #                     else:
    #                         raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
    #
    #                 else:  # invoice is in company currency
    #                     # Bug- VCN total amount change upon validated
    #
    #                     if invoice_line.freight_currency_rate != 1:
    #                         price_unit = float_round(
    #                             invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
    #                             2,
    #                             rounding_method='HALF-UP')
    #                     freight_currency_rate = invoice_line.freight_currency_rate
    #                     currency_id = invoice_line.freight_currency
    #                 if not invoice_line.rft_line_id:
    #                     #print('>>>>>>> write rft_line_id ==0')
    #                     cost_profit = self.env['rft.cost.profit']
    #                     if record.type == 'out_refund' and invoice_line.invoice_id.rft_id and price_unit > 0:
    #                         sale_line = cost_profit.create({
    #                             'product_id': invoice_line.product_id.id,
    #                             'product_name': invoice_line.name,
    #                             'sales_qty': invoice_line.quantity,
    #                             'unit_price': -(price_unit),
    #                             'added_to_invoice': True,
    #                             'sale_currency_rate': freight_currency_rate,
    #                             'sales_currency': currency_id.id,
    #                             'rft_id': invoice_line.invoice_id.rft_id.id or False,
    #                         })
    #
    #                         invoice_line.rft_line_id = sale_line
    #                     elif record.type == 'in_refund':
    #                         rft_id = False
    #                         if invoice_line.invoice_id.rft_id:
    #                             rft_id = invoice_line.invoice_id.rft_id.id
    #                         elif invoice_line.rft_id:
    #                             rft_id = invoice_line.rft_id.id
    #                         if rft_id and price_unit>0:
    #                             cost_line = cost_profit.create({
    #                                 'product_id': invoice_line.product_id.id,
    #                                 'product_name': invoice_line.name,
    #                                 'cost_price': -(price_unit) or 0,
    #                                 'cost_qty': invoice_line.quantity or False,
    #                                 'cost_currency': currency_id.id,
    #                                 'cost_currency_rate': freight_currency_rate,
    #                                 'invoiced': True,
    #                                 'vendor_id': invoice_line.invoice_id.partner_id.id,
    #                                 'rft_id': rft_id or False,
    #                             })
    #                             invoice_line.rft_line_id = cost_line
    #                 if invoice_line.invoice_id.rft_id:
    #                     rft = self.env['transport.rft'].browse(invoice_line.invoice_id.rft_id.id)
    #                     if not rft.analytic_account_id:
    #                         # print('>>>> onchange_rft_id no analytic account')
    #                         values = {
    #                             'partner_id': rft.customer_name.id,
    #                             'name': '%s' % rft.rft_no,
    #                             'company_id': self.env.user.company_id.id,
    #                         }
    #                         analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #                         rft.write({'analytic_account_id': analytic_account.id,
    #                                        })
    #                         invoice_line.account_analytic_id = analytic_account.id,
    #                     else:
    #                         # print('>>>> onchange_rft_id with AA')
    #                         invoice_line.account_analytic_id = rft.analytic_account_id.id
    #
    #         #TS - fix the Debit Note not update/wrong issue 11/5/22
    #         if vals.get('state') == 'open' and record.type == 'out_invoice' and record.customer_debit_note == True:
    #             #print('>>>>>>>> Debit Note Open 1')
    #             for invoice_line in record.invoice_line_ids:
    #                 if invoice_line.product_id:
    #                     price_unit = 0.000000
    #                     freight_currency_rate = 1.000000
    #                     currency_id = 0
    #                     if record.company_id.currency_id != record.currency_id:
    #                         if record.exchange_rate_inverse:
    #                             price_unit = invoice_line.price_unit
    #                             freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
    #                             currency_id = invoice_line.invoice_id.currency_id
    #                         else:
    #                             raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
    #                     else:  # invoice is in company currency
    #                         if invoice_line.freight_currency_rate != 1:
    #                             price_unit = float_round(
    #                                 invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
    #                                 2,
    #                                 rounding_method='HALF-UP')
    #                         freight_currency_rate = invoice_line.freight_currency_rate
    #                         currency_id = invoice_line.freight_currency
    #                     if not invoice_line.rft_line_id:
    #                         #alway insert a new cost_profit line for Debit note
    #                         cost_profit = self.env['rft.cost.profit']
    #                         sale_line = cost_profit.create({
    #                             'product_id': invoice_line.product_id.id,
    #                             'product_name': invoice_line.name,
    #                             'sales_qty': invoice_line.quantity,
    #                             'unit_price': -(price_unit),
    #                             'added_to_invoice': True,
    #                             'sale_currency_rate': freight_currency_rate,
    #                             'sales_currency': currency_id.id,
    #                             'rft_id': invoice_line.invoice_id.rft_id.id or False,
    #                         })
    #                         invoice_line.rft_line_id = sale_line
    #         if vals.get('state') == 'paid':
    #             for operation in self:
    #                 if operation.rft_id:
    #                     if operation.type == 'out_invoice':
    #                         rfts = self.env['transport.rft'].search([
    #                             ('id', '=', operation.rft_id.id),
    #                         ])
    #                         # print('invoice len=' + str(len(rfts)))
    #                         if rfts:
    #                             #rfts[0].shipment_rft_status = '11'
    #                             invoice_cost_profit_ids = self.env['rft.cost.profit'].search([('invoice_id', '=', self.id), ])
    #                             #print(invoice_cost_profit_ids)
    #                             for cost_profit_id in invoice_cost_profit_ids:
    #                                 cost_profit_id.invoice_paid = True
    #                                 rfts[0].invoice_paid_status = '02'
    #                             check_all_paid = True
    #                             for check_line in rfts[0].cost_profit_ids:
    #                                 if not check_line.invoice_paid:
    #                                     check_all_paid = False
    #                             if check_all_paid:
    #                                 rfts[0].invoice_paid_status = '03'
    #
    #                     elif operation.type == 'in_invoice':
    #                         rfts = self.env['transport.rft'].search([
    #                             ('id', '=', operation.rft_id.id),
    #                         ])
    #                         #print('rft len=' + str(len(rfts)))
    #                         if rfts:
    #                             vendor_cost_profit_ids = rfts[0].cost_profit_ids.filtered(
    #                                 lambda r: r.vendor_id.id == operation.partner_id.id)
    #                             print('vendor_cost_profit_ids len=' + str(len(vendor_cost_profit_ids)))
    #                             for cost_profit_id in vendor_cost_profit_ids:
    #                                 cost_profit_id.paid = True
    #                 else:
    #                     # assign cost
    #                     if operation.type == 'in_invoice':
    #                         for line in operation.invoice_line_ids:
    #                             if line.rft_id:
    #                                 freight_cost_profit_lines = self.env['rft.cost.profit'].search([
    #                                     ('bill_line_id', '=', line.id),
    #                                 ])
    #                                 if freight_cost_profit_lines:
    #                                     for cost_line in freight_cost_profit_lines:
    #                                         cost_line.paid = True
    #
    #
    #     res = super(RFTInvoice, self).write(vals)
    #     return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    rft_id = fields.Many2one('transport.rft', string='RFT No')
    rft_line_id = fields.Many2one('rft.cost.profit', copy=False)
