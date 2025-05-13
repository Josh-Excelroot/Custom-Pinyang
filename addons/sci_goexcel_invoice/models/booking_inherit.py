from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    #invoices_no = fields.Char(string='Invoices No', compute="_compute_invoices_no", store=True)
    #invoices_number = fields.Char(string='Invoices Number', compute="_compute_invoices_number", store=True)
    # invoices_numbers = fields.Char(string='Invoices Number', compute="_compute_invoices_numbers", store=True)
    # booking_invoice_lines_ids = fields.One2many('booking.invoice.line', 'booking_id', string="Booking Invoices",
    #                                      copy=True, auto_join=True, track_visibility='always')
    #
    # @api.one
    # @api.depends('pivot_sale_total', 'pivot_cost_total')
    # def _compute_invoices_numbers(self):
    #     for operation in self:
    #         #Get the invoices
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', 'in', ['out_invoice', 'out_refund']),
    #             ('state', '!=', 'cancel'),
    #         ])
    #         if invoices:
    #             operation.invoices_numbers = ''
    #             for invoice in invoices:
    #                 self.action_create_invoice_line(invoice)
    #                 if operation.invoices_numbers and len(operation.invoices_numbers) > 1:
    #                     if invoice.number:
    #                         operation.invoices_numbers = operation.invoices_numbers + ' ' + str(invoice.number)
    #                 else:
    #                     if invoice.number:
    #                         operation.invoices_numbers = str(invoice.number)
    #         vendor_bill_list = []
    #         # Get the vendor bills
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type == 'in_invoice':
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         unique_vendor_bill_list = []
    #         for i in vendor_bill_list:
    #             if i not in unique_vendor_bill_list:
    #                 unique_vendor_bill_list.append(i)
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', 'in', ['in_invoice', 'in_refund']),
    #             ('state', '!=', 'cancel'),
    #         ])
    #         invoice_name_list = []
    #         for x in invoices:
    #             invoice_name_list.append(x.id)
    #             self.action_create_invoice_line(x)
    #             if operation.invoices_numbers and len(operation.invoices_numbers) > 1:
    #                 if x.number:
    #                     operation.invoices_numbers = operation.invoices_numbers + ' ' + str(x.reference)
    #             else:
    #                 if x.name:
    #                     operation.invoices_numbers = str(x.reference)
    #         unique_list = []
    #
    #         for y in unique_vendor_bill_list:
    #             if invoice_name_list and len(invoice_name_list) > 0:
    #                 if y not in invoice_name_list:
    #                     unique_list.append(y)
    #                     inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
    #                     if inv:
    #                         self.action_create_invoice_line(inv)
    #                         if operation.invoices_numbers and len(operation.invoices_numbers) > 1:
    #                             if inv.number:
    #                                 operation.invoices_numbers = operation.invoices_numbers + ' ' + str(inv.reference)
    #
    #                         else:
    #                             if inv.name:
    #                                 operation.invoices_numbers = str(inv.reference)
    #             else:
    #                 unique_list.append(y)
    #                 inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
    #                 if inv:
    #                     self.action_create_invoice_line(inv)
    #                     if inv.number:
    #                         if operation.invoices_numbers and len(operation.invoices_numbers) > 1:
    #                             operation.invoices_numbers = operation.invoices_numbers + ' ' + str(inv.reference)
    #                         else:
    #                             operation.invoices_numbers = str(inv.reference)
    #
    #
    # @api.multi
    # def action_create_invoice_line(self, invoice):
    #     invoice_line = self.env['booking.invoice.line']
    #     for operation in self:
    #         if invoice.type in ['out_invoice', 'out_refund']:
    #             invoice_line_1 = invoice_line.create({
    #                 'invoice_no': invoice.number or '',
    #                 'reference': invoice.reference or '',
    #                 'invoice_amount': invoice.amount_total_signed or 0,
    #                 'booking_id': operation.id or False,
    #             })
    #         elif invoice.type in ['in_invoice', 'in_refund']:
    #             if invoice.freight_booking:
    #                 invoice_line_1 = invoice_line.create({
    #                     'invoice_no': invoice.number or '',
    #                     'reference': invoice.reference or '',
    #                     'invoice_amount': invoice.amount_total_signed or 0,
    #                     'booking_id': operation.id or False,
    #                 })
    #             else:
    #                 amt = 0
    #                 for inv_line in invoice.invoice_line_ids:
    #                     if inv_line.freight_booking.id == operation.id:
    #                         amt += inv_line.price_subtotal
    #                 if operation.company_id.currency_id != operation.currency_id:
    #                     if operation.exchange_rate_inverse:
    #                         amt = amt * operation.exchange_rate_inverse
    #                 invoice_line_1 = invoice_line.create({
    #                     'invoice_no': invoice.number or '',
    #                     'reference': invoice.reference or '',
    #                     'invoice_amount': amt or 0,
    #                     'booking_id': operation.id or False,
    #                 })


    # @api.multi
    # def action_calculate_cost_line(self):
    #     for cost_profit_line in self.cost_profit_ids:
    #         total_cost = 0
    #         total_qty = 0
    #         for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #             #print(vendor_bill_line.id)
    #             account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=', vendor_bill_line.id)])
    #             for invoice_line_item in account_invoice_line:
    #                 if invoice_line_item.booking_line_id == cost_profit_line:
    #                     if vendor_bill_line.type == 'in_invoice':
    #                         total_cost = total_cost + invoice_line_item.price_subtotal
    #                         total_qty = total_qty + 1
    #                     if vendor_bill_line.type == 'in_refund':
    #                         total_cost = total_cost - invoice_line_item.price_subtotal
    #                     cost_profit_line.write({
    #                         'cost_price': total_cost,
    #                         'cost_qty': 1,
    #                     })

    # @api.multi
    # def action_calculate_cost(self):
    #     for cost_profit_line in self.cost_profit_ids:
    #         total_cost = 0
    #         total_qty = 0
    #         for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #             print(vendor_bill_line.id)
    #             account_invoice_line = self.env['account.invoice.line'].search(
    #                 [('invoice_id', '=', vendor_bill_line.id)])
    #             for invoice_line_item in account_invoice_line:
    #                 if invoice_line_item.booking_line_id == cost_profit_line:
    #                     if vendor_bill_line.type == 'in_invoice':
    #                         total_cost = total_cost + invoice_line_item.price_subtotal
    #                         total_qty = total_qty + 1
    #                     if vendor_bill_line.type == 'in_refund':
    #                         total_cost = total_cost - invoice_line_item.price_subtotal
    #         cost_profit_line.write({
    #             'cost_price': total_cost,
    #             'cost_qty': 1,
    #         })

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        vendor_po = vendor_po.filtered(lambda c: c.invoiced == False)
        # print('vendor_po=' + str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.customer_name.id,
                'name': '%s' % self.booking_no,
                # 'partner_id': self.customer_name.id,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            if len(line.vendor_bill_ids) > 0 and not line.invoiced:
                raise exceptions.ValidationError(
                    'Some items are already billed. Please tick on "Billed" column for the items that are already billed.')
            if not line.invoiced:
                # print(line.vendor_bill_id)
                # print('line.vendor_id=' + line.vendor_id.name)
                if line.vendor_id != vendor_id:
                    # print('not same partner')
                    vb = self.env['account.invoice']
                    # vb_line_obj = self.env['account.invoice.line']
                    # if line.vendor_id:
                    vendor_count = True
                    vendor_id = line.vendor_id
                    # print('vendor_id=' + vendor_id.name)
                    # combine multiple cost lines from same vendor
                    value = []
                    vendor_bill_created = []
                    filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                    for vb_line in filtered_vb_lines:
                        # print('combine lines')
                        if not vb_line.invoiced:
                            account_id = False
                            # price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                            price_after_converted = round(vb_line.cost_price * vb_line.cost_currency_rate, 6)
                            if vb_line.product_id.property_account_expense_id:
                                account_id = vb_line.product_id.property_account_expense_id
                            elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                                account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                            # print(vb_line)
                            value.append([0, 0, {
                                # 'invoice_id': vendor_bill.id or False,
                                'account_id': account_id.id or False,
                                'name': vb_line.product_id.name or '',
                                'product_id': vb_line.product_id.id or False,
                                'quantity': vb_line.cost_qty or 0.0,
                                'uom_id': vb_line.uom_id.id or False,
                                'price_unit': price_after_converted or 0.0,
                                'account_analytic_id': self.analytic_account_id.id,
                                'freight_booking': self.id,
                                'booking_line_id': vb_line.id,
                                'freight_currency': vb_line.cost_currency.id or False,
                                'freight_foreign_price': vb_line.cost_price or 0.0,
                                'freight_currency_rate': round(vb_line.cost_currency_rate, 6) or 1.000000,
                            }])
                            vendor_bill_created.append(vb_line)
                            vb_line.invoiced = True

                    vendor_bill_list = []
                    if value:
                        vendor_bill_id = vb.create({
                            'type': 'in_invoice',
                            'invoice_line_ids': value,
                            #  'default_purchase_id': self.booking_no,
                            'default_currency_id': self.env.user.company_id.currency_id.id,
                            'company_id': self.company_id.id,
                            'date_invoice': fields.Date.context_today(self),
                            'origin': self.booking_no,
                            'partner_id': vendor_id.id,
                            'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                            'freight_booking': self.id,
                        })
                        vendor_bill_list.append(vendor_bill_id.id)
                    for vb_line in filtered_vb_lines:
                        if vb_line.invoiced:
                            vendor_bill_ids_list = []
                            if vendor_bill_list:
                                vendor_bill_ids_list.append(vendor_bill_list[0])
                                vb_line.write({
                                    # 'vendor_id_ids': [(6, 0, vendor_ids_list)],
                                    'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                })
                    # for new_vendor_bill in vendor_bill_created:
                    #     new_vendor_bill.vendor_bill_id = vendor_bill_id.id
                    #     new_vendor_bill.vendor_bill_ids = [(6, 0, vendor_bill_list)]
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        is_copy = self._context.get('is_copy', False)
        if is_copy or (self.create_date and (
                fields.Datetime.now() - self.create_date).total_seconds() < 60 and not self.get_vendor_bill_ids()):
            self.update({
                'vendor_bill_count': 0,
            })
            return
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            # vendor_bill_list_temp = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)
                        # vendor_bill_list_temp.append(vendor_bill_line.id)
            #print('vendor_bill_list: ', len(vendor_bill_list))
            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            #print('unique_vendor_bill_list: ', len(unique_vendor_bill_list))
            # Get the vendor list (Create the vendor from the job)
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            #print('vendor bills:', len(invoices))
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)
            unique_list = []
            # for x in invoices:
            #     invoice_name_list.append(x.vendor_bill_id.id)
            # unique_list = []
            for y in unique_vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })

            # else:
            #     # self.update({
            #     #     'vendor_bill_count': len(unique_list),
            #     # })
            #     #TS - show vendor bill count for old vendor bills
            #     invoices = self.env['account.invoice'].search([
            #         ('freight_booking', '=', operation.id),
            #         ('type', '=', 'in_invoice'),
            #         ('state', '!=', 'cancel'),
            #     ])
            #     if len(invoices) > 0:
            #         self.update({
            #             'vendor_bill_count': len(invoices),
            #         })

    @api.multi
    def operation_bill(self):
        for operation in self:
            """
            invoices = self.env['account.invoice'].search([
                ('origin', '=', self.booking_no),
                ('type', '=', 'in_invoice'),
            ])
            """
            vendor_bill_list = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)

            unique_list = []
            for y in vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)

        if len(unique_list) > 1:
            views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                     (self.env.ref('account.invoice_supplier_form').id, 'form')]
            return {
                'name': 'Vendor bills',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.invoice',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', unique_list)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(unique_list) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


    # def _get_bill_count(self):
    #     for operation in self:
    #         vendor_bill_list = []
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type == 'in_invoice':
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         unique_list = []
    #         for y in vendor_bill_list:
    #             if y not in unique_list:
    #                 unique_list.append(y)
    #         self.update({
    #             'vendor_bill_count': len(unique_list),
    #         })
    #
    #
    # @api.multi
    # def operation_bill(self):
    #     for operation in self:
    #         """
    #         invoices = self.env['account.invoice'].search([
    #             ('origin', '=', self.booking_no),
    #             ('type', '=', 'in_invoice'),
    #         ])
    #         """
    #         vendor_bill_list = []
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type == 'in_invoice':
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', '=', 'in_invoice'),
    #             ('state', '!=', 'cancel'),
    #         ])
    #         invoice_name_list = []
    #         for x in invoices:
    #             invoice_name_list.append(x.id)
    #
    #         unique_list = []
    #         for y in vendor_bill_list:
    #             if invoice_name_list and len(invoice_name_list) > 0:
    #                 if y not in invoice_name_list:
    #                     unique_list.append(y)
    #             else:
    #                 unique_list.append(y)
    #         for z in invoice_name_list:
    #             # if z not in vendor_bill_list:
    #             unique_list.append(z)
    #
    #     if len(unique_list) > 1:
    #         views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
    #                  (self.env.ref('account.invoice_supplier_form').id, 'form')]
    #         return {
    #             'name': 'Vendor bills',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #             'view_id': False,
    #             'res_model': 'account.invoice',
    #             'views': views,
    #             # 'context': "{'type':'in_invoice'}",
    #             'domain': [('id', 'in', unique_list)],
    #             'type': 'ir.actions.act_window',
    #             # 'target': 'new',
    #         }
    #     elif len(unique_list) == 1:
    #         # print('in vendor bill length =1')
    #         return {
    #             # 'name': self.booking_no,
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'account.invoice',
    #             'res_id': unique_list[0] or False,  # readonly mode
    #             #  'domain': [('id', 'in', purchase_order.ids)],
    #             'type': 'ir.actions.act_window',
    #             'target': 'popup',  # readonly mode
    #         }
    #
    # @api.multi
    # def action_create_vendor_bill(self):
    #     vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
    #     po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
    #     vendor_count = False
    #     vendor_id = False
    #     if not self.analytic_account_id:
    #         values = {
    #             'name': '%s' % self.booking_no,
    #             # 'partner_id': self.customer_name.id,
    #             'company_id': self.company_id.id,
    #         }
    #         analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #         self.write({'analytic_account_id': analytic_account.id})
    #     for line in po_lines:
    #         #print(line.vendor_bill_id)
    #         # print('line.vendor_id=' + line.vendor_id.name)
    #         if line.vendor_id != vendor_id:
    #             #print('not same partner')
    #             vb = self.env['account.invoice']
    #             vendor_count = True
    #             vendor_id = line.vendor_id
    #             value = []
    #             vendor_bill_created = []
    #             filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
    #             for vb_line in filtered_vb_lines:
    #                 if not vb_line.invoiced:
    #                     account_id = False
    #                     price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
    #                     if vb_line.product_id.property_account_expense_id:
    #                         account_id = vb_line.product_id.property_account_expense_id
    #                     elif vb_line.product_id.categ_id.property_account_expense_categ_id:
    #                         account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
    #                     value.append([0, 0, {
    #                         # 'invoice_id': vendor_bill.id or False,
    #                         'account_id': account_id.id or False,
    #                         'name': vb_line.product_id.name or '',
    #                         'product_id': vb_line.product_id.id or False,
    #                         'quantity': vb_line.cost_qty or 0.0,
    #                         'uom_id': vb_line.uom_id.id or False,
    #                         'price_unit': price_after_converted or 0.0,
    #                         'account_analytic_id': self.analytic_account_id.id,
    #                         'freight_booking': self.id,
    #                         'booking_line_id': vb_line.id,
    #                     }])
    #                     vendor_bill_created.append(vb_line)
    #                     vb_line.invoiced = True
    #             vendor_bill_list = []
    #             if value:
    #                 vendor_bill_id = vb.create({
    #                     'type': 'in_invoice',
    #                     'invoice_line_ids': value,
    #                     'default_currency_id': self.env.user.company_id.currency_id.id,
    #                     'company_id': self.company_id.id,
    #                     'date_invoice': fields.Date.context_today(self),
    #                     'partner_id': vendor_id.id,
    #                     'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
    #                     'freight_booking': self.id,
    #                 })
    #                 vendor_bill_list.append(vendor_bill_id.id)
    #             #print(vendor_bill_list)
    #             for new_vendor_bill in vendor_bill_created:
    #                 new_vendor_bill.vendor_bill_id = vendor_bill_id.id
    #                 new_vendor_bill.vendor_bill_ids = [(6, 0, vendor_bill_list)]
    #     if vendor_count is False:
    #         raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')


class CostProfit(models.Model):
    _inherit = "freight.cost_profit"

    vendor_id_ids = fields.Many2many('res.partner', string="Vendor List", copy=False)
    vendor_bill_ids = fields.Many2many('account.invoice', string="Vendor Bill List", copy=False)

#
# class BookingInvoiceLines(models.Model):
#     _name = "booking.invoice.line"
#
#     #invoice_id = fields.Many2one('account.invoice', string="Invoice")
#     invoice_no = fields.Char(string="Invoice No")
#     reference = fields.Char(string="Vendor Invoice/Payment Ref.")
#     invoice_amount = fields.Float(string="Amount", store=True)
#     #type = fields.Char(string='type', help="invoice, vendor bill, customer CN and vendor CN, vendor debit note")
#     booking_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
#                     index=True, copy=False)