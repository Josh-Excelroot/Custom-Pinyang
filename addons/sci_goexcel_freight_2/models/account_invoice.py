from odoo import api, fields, models, exceptions
import logging
from datetime import date

_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    running_id = fields.Integer(string="Running ID")
    include_signature = fields.Boolean(string="Include Signature", default=True)
    booking_date = fields.Date(string='ETA/ETD Date', copy=False, store=True)

    #Josh 16052025, add lcl consolidation field and bl reference
    lcl_consolidation = fields.Boolean(string='LCL Consolidation', compute="_bol_is_lcl")
    freight_bol = fields.Many2one('freight.bol', string='Freight BOL')

    @api.model('freight_booking.lcl_consolidation')
    def _bol_is_lcl(self):
        # we know the booking is a lcl consolidation job, so invoice created from bl should also be lcl consolidation
        for record in self:
            record.lcl_consolidation = record.freight_booking.lcl_consolidation if record.freight_booking else False


    def _get_package_weight(self):
        pkgs = []
        weight = []
        container = []
        # Yulia 26112024 change operation_line_ids into  operation_line_ids2
        if self.freight_booking.cargo_type == 'lcl':
            for dt in self.freight_booking.operation_line_ids2:
                pkgs.append(str(dt.packages_no) + " " + str(dt.packages_no_uom.display_name))
                weight.append('{:.2f} M3 / {:.2f} KG'.format(float(dt.exp_vol), float(dt.exp_gross_weight)))
        else:
            # fcl
            for dt in self.freight_booking.operation_line_ids:
                pkgs.append(str(dt.packages_no) + " " + str(dt.packages_no_uom.display_name))
                weight.append('{:.2f} M3 / {:.2f} KG'.format(float(dt.exp_vol), float(dt.exp_gross_weight)))

            # weight.append({"exp_vol":dt.exp_vol,"exp_gross_weight":dt.exp_gross_weight})
        return {
            "packages": ", ".join(pkgs),
            "weight": ", ".join(weight)
        }

    # Yulia 08102024 merge from ion
    def total_containers(self):
        total_containers = 0
        if self.freight_booking.service_type != 'air':
            if self.freight_booking.cargo_type == 'lcl':
                total_containers = len(self.freight_booking.operation_line_ids2)
            elif self.freight_booking.cargo_type == 'fcl':
                total_containers = len(self.freight_booking.operation_line_ids)
        return total_containers

    # Yulia 08102024 merge from ion
    def should_containers_list_on_every_page(self):
        containers_in_one_line = 8
        lines_limit = 3
        return self.total_containers() <= (containers_in_one_line * lines_limit)

    @api.model
    def create(self, vals):
        if vals.get("freight_booking") is not None:
            term = self.env['sale.letter.template'].search([('name', '=', 'Invoice')], limit=1)
            vals['sale_term'] = term.template

        if vals.get("freight_booking") is not None:
            booking_id = vals.get("freight_booking")
            if booking_id:
                booking = self.env['freight.booking'].browse(booking_id)
                vals['booking_date'] = booking.booking_date_time

        if vals.get('type') == 'in_refund' or vals.get('type') == 'out_refund' or vals.get('type') == 'in_invoice':
            if self.freight_booking:
                vals.update({'booking_date': self.freight_booking.booking_date_time})

        res = super(AccountInvoice, self).create(vals)

        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        state = vals.get("state")
        # print('>>>>>>>>>>>>>>> Write')
        if state == 'open':
            for operation in self:
                if operation.freight_booking:
                    # print('>>>>>>>>>>>>>> Write Open')
                    booking = self.env['freight.booking'].search([
                        ('id', '=', operation.freight_booking.id)], limit=1)
                    # if self.reference and booking:
                    if booking:
                        booking.action_reupdate_booking_invoice_one()
                else:  # without freight_booking, ie, vendor bill
                    sorted_recordset = operation.invoice_line_ids.sorted(key=lambda r: r.freight_booking)
                    booking_id = False
                    for line in sorted_recordset:
                        if line.freight_booking and line.freight_booking.id != booking_id:
                            booking = self.env['freight.booking'].search([
                                ('id', '=', line.freight_booking.id)], limit=1)
                            if booking:
                                booking.action_reupdate_booking_invoice_one()
                                booking_id = line.freight_booking.id
                if operation.type == 'in_invoice':  # update bill status
                    if operation.freight_booking:
                        booking = self.env['freight.booking'].search([
                            ('id', '=', operation.freight_booking.id),
                        ], limit=1)
                        if booking:
                            booking.bill_status = '02'
                        check_all_bill = True
                        for check_line in booking.cost_profit_ids:
                            if not check_line.invoiced and check_line.product_id.is_billable:
                                check_all_bill = False
                                break
                        if check_all_bill:
                            booking.bill_status = '03'
                    else:
                        for line in operation.invoice_line_ids:
                            if line.freight_booking:
                                line.freight_booking.bill_status = '02'
                                # update bill paid status
                                check_all_bill = True
                                for check_line in line.freight_booking.cost_profit_ids:
                                    if not check_line.invoiced and check_line.product_id.is_billable:
                                        check_all_bill = False
                                        break
                                if check_all_bill:
                                    line.freight_booking.bill_status = '03'

        if state == 'paid':
            for operation in self:
                if operation.freight_booking:
                    if operation.type == 'out_invoice':  # invoice
                        booking = self.env['freight.booking'].search([
                            ('id', '=', operation.freight_booking.id),
                        ], limit=1)
                        # print('invoice len=' + str(len(bookings)))
                        if booking:
                            booking.shipment_booking_status = '11'
                        invoice_cost_profit_ids = self.env['freight.cost_profit'].search(
                            [('invoice_id', '=', operation.id), ])
                        # print(invoice_cost_profit_ids)
                        for cost_profit_id in invoice_cost_profit_ids:
                            cost_profit_id.invoice_paid = True
                            booking.invoice_paid_status = '02'
                        check_all_paid = True
                        for check_line in booking.cost_profit_ids:
                            if not check_line.invoice_paid:
                                check_all_paid = False
                        if check_all_paid:
                            booking.invoice_paid_status = '03'

                    elif operation.type == 'in_invoice':  # vendor bill
                        booking = self.env['freight.booking'].search([
                            ('id', '=', operation.freight_booking.id),
                        ], limit=1)
                        ##print('booking len=' + str(len(bookings)))
                        if booking:
                            vendor_cost_profit_ids = booking.cost_profit_ids.filtered(
                                lambda r: r.vendor_id.id == operation.partner_id.id)
                            # print('vendor_cost_profit_ids len=' + str(len(vendor_cost_profit_ids)))
                            for cost_profit_id in vendor_cost_profit_ids:
                                cost_profit_id.paid = True
                        # update bill paid status
                        booking.bill_paid_status = '02'
                        check_all_paid = True
                        for check_line in booking.cost_profit_ids:
                            if not check_line.paid and check_line.product_id.is_billable:
                                check_all_paid = False
                                break
                        if check_all_paid:
                            booking.bill_paid_status = '03'
                else:
                    # assign cost for vendor bill line item
                    if operation.type == 'in_invoice':
                        for line in operation.invoice_line_ids:
                            if line.freight_booking:
                                if line.booking_line_id:
                                    cost_line = self.env['freight.cost_profit'].browse(line.booking_line_id.id)
                                    if cost_line:
                                        # for cost_line in freight_cost_profit_lines:
                                        cost_line.paid = True
                                line.freight_booking.bill_paid_status = '02'
                                # update bill paid status
                                check_all_paid = True
                                for check_line in line.freight_booking.cost_profit_ids:
                                    if not check_line.paid and check_line.product_id.is_billable:
                                        check_all_paid = False
                                        break
                                if check_all_paid and line.freight_booking:
                                    line.freight_booking.bill_paid_status = '03'

        # TS Bug for ETA/ETD
        for operation in self:
            # print(operation.freight_booking)
            # print(operation.booking_date)
            if operation.freight_booking:
                bookings = self.env['freight.booking'].search([
                    ('id', '=', operation.freight_booking.id),
                ])
                if not operation.booking_date:
                    vals.update({'booking_date': self.freight_booking.booking_date_time})

        return res

    @api.onchange('partner_id')
    def set_currency_from_partner_pricelist(self):
        if self.partner_id.property_product_pricelist:
            self.currency_id = self.partner_id.property_product_pricelist.currency_id.id


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    freight_currency = fields.Many2one('res.currency', string='Currency',
                                       default=lambda self: self.env.user.company_id.currency_id.id,
                                       track_visibility='onchange')
    freight_foreign_price = fields.Float(string='Unit Price(FC)', track_visibility='onchange')
    # freight_currency_rate = fields.Float(string='Rate', default="1.000000", digit=dp.get_precision('Exchange Rate'))
    freight_currency_rate = fields.Float(string='Rate', default="1.000000", digits=(12, 6))
    price_unit = fields.Float(string='Unit Price', required=True, digits=(12, 6))

    # Yulia 26112024 change price invoice issue
    @api.onchange('quantity', 'price_unit', 'freight_currency', 'freight_currency_rate', 'freight_foreign_price')
    def change_price(self):
        for rec in self:
            # Ahmad Zaman - 27/11/24 - Added foreign currency condition as the onchange was triggering on all invoices
            if (rec.freight_currency.id != rec.invoice_id.currency_id.id
                    and rec.freight_currency.id != rec.env.user.company_id.currency_id.id):
                rec.price_unit = rec.freight_foreign_price * rec.freight_currency_rate

    @api.onchange('invoice_line_tax_ids')
    def onchange_invoice_line_ids(self):
        if self.invoice_line_tax_ids and sum(
                self.invoice_line_tax_ids.mapped('amount')) == 6.0 and self.partner_id.property_account_position_id:
            sst_exemption_record = self.env['account.tax'].sudo().search([
                ('name', 'like', 'SST EXEMPTION'), ('company_id.id', '=', self.company_id.id)
            ])
            self.invoice_line_tax_ids = [
                (5, 0, 0)
            ]
            self.invoice_line_tax_ids = [
                (6, 0, sst_exemption_record.ids)
            ]
        else:
            return

    # @api.onchange('freight_booking', 'price_subtotal')
    # def onchange_freight_booking(self):  # trigger second
    #     # print('>>>> onchange_price_subtotal 1')
    #     # vendor bill only
    #     # print('>>>>>>>>>>> onchange_price_subtotal freight_booking: ', self.invoice_type)
    #     if self.freight_booking and self.product_id and self.invoice_type == 'in_invoice' and not self.invoice_id.debit_invoice_id:
    #         booking = self.env['freight.booking'].search([('id', '=', self.freight_booking.id)], limit=1)
    #         check_booking = False
    #         # print('>>>>>>>>>>  onchange_price_subtotal 2 booking.id=', booking.id)
    #         for cost_profit_line in booking.cost_profit_ids:
    #             # print('>>>>>>>>>>self.product_id', self.product_id, ' , cost_profit_line.product_id=', cost_profit_line.product_id)
    #             if cost_profit_line.product_id == self.product_id:
    #                 price_unit = 0
    #                 freight_currency_rate = 1.000000
    #                 currency_id = self.freight_currency
    #                 # print('>>>> onchange_freight_booking equal')
    #                 # if not cost_profit_line.invoiced:
    #                 self.booking_line_id = cost_profit_line
    #                 check_booking = True
    #                 total_cost = 0
    #                 total_qty = 0
    #                 if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
    #                     # print('>>>> onchange_price_subtotal price >0')
    #                     # if already have vendor bills that had assigned cost
    #                     if cost_profit_line.vendor_bill_ids:
    #                         # for second/third vendor bill to the same job cost
    #                         if len(cost_profit_line.vendor_bill_ids) > 1:
    #                             # print('>>>>>>>>>>  onchange_price_subtotal vendor_bill_ids>1=', len(cost_profit_line.vendor_bill_ids))
    #                             total_qty = 0
    #                             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                                 account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
    #                                                                                                  vendor_bill_line.id)])
    #                                 # print('>>>>>>>>>>  onchange_price_subtotal account_invoice_line=',
    #                                 #      len(account_invoice_line))
    #                                 for invoice_line_item in account_invoice_line:
    #                                     # print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_booking=',
    #                                     #     invoice_line_item.freight_booking)
    #                                     if (invoice_line_item.product_id == cost_profit_line.product_id) and \
    #                                             (invoice_line_item.freight_booking.id == self.freight_booking.id):
    #                                         total_qty = total_qty + invoice_line_item.quantity
    #                                         # print('>>>> onchange_price_subtotal price total_qty=', total_qty)
    #                                 if not account_invoice_line or len(account_invoice_line) == 0:
    #                                     total_qty = total_qty + self.quantity
    #                             if total_qty > 0:
    #                                 cost_profit_line.write(
    #                                     {  # assuming cost_price will always be same for all vendor bills for same item
    #                                         # 'cost_price': round(price_unit, 2) or 0,
    #                                         'cost_qty': total_qty or False,
    #                                         # 'cost_currency_rate': invoice_line.freight_currency_rate,
    #                                         # 'cost_currency': invoice_line.freight_currency.id,
    #                                         'invoiced': True,
    #                                         # 'vendor_id': self.invoice_id.partner_id.id,
    #                                         # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
    #                                     })
    #                         else:  # First cost assignment from the vendor bill
    #                             if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
    #                                 if self.invoice_id.exchange_rate_inverse:
    #                                     # price_unit = float_round(
    #                                     #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
    #                                     #     2,
    #                                     #     rounding_method='HALF-UP')
    #                                     price_unit = self.price_unit
    #                                     freight_currency_rate = self.invoice_id.exchange_rate_inverse
    #                                     currency_id = self.invoice_id.currency_id
    #                                 else:
    #                                     raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
    #                             else:
    #                                 if self.freight_currency_rate != 1:
    #                                     # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
    #                                     price_unit = float_round(
    #                                         self.price_subtotal / self.quantity / self.freight_currency_rate,
    #                                         2, rounding_method='HALF-UP')
    #                                 else:
    #                                     price_unit = float_round(self.price_subtotal / self.quantity, 6,
    #                                                              rounding_method='HALF-UP')
    #                                 freight_currency_rate = self.freight_currency_rate
    #                                 currency_id = self.freight_currency
    #                             # if self.type == 'in_invoice':
    #                             # total_cost = total_cost + price_unit
    #                             # print('>>>>>>> _onchange_price freight_booking price_unit:', price_unit)
    #                             # total_cost = price_unit  # formula is always cost_price * cost_qty
    #                             total_qty = self.quantity
    #                             cost_profit_line.write({
    #                                 'cost_price': price_unit,
    #                                 'cost_qty': total_qty,  # why add 1
    #                                 'invoiced': True,
    #                                 'vendor_id': self.invoice_id.partner_id.id,
    #                                 'vendor_bill_id': self.invoice_id.id,
    #                                 'cost_currency': currency_id.id,
    #                                 'cost_currency_rate': freight_currency_rate,
    #                                 # 'vendor_bill_ids': [(4, self.invoice_id.id)],
    #                             })
    #
    #                     else:
    #                         # assign the cost for first vendor bill
    #                         # print('>>>> onchange_price_subtotal else')
    #                         if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
    #                             if self.invoice_id.exchange_rate_inverse:
    #                                 # price_unit = float_round(
    #                                 #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
    #                                 #     2,
    #                                 #     rounding_method='HALF-UP')
    #                                 price_unit = self.price_unit
    #                                 freight_currency_rate = self.invoice_id.exchange_rate_inverse
    #                                 currency_id = self.invoice_id.currency_id
    #                             else:
    #                                 raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
    #                         else:
    #                             if self.freight_currency_rate != 1:
    #                                 # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
    #                                 price_unit = float_round(
    #                                     self.price_subtotal / self.quantity / self.freight_currency_rate,
    #                                     6, rounding_method='HALF-UP')
    #                             else:
    #                                 price_unit = float_round(self.price_subtotal / self.quantity, 2,
    #                                                          rounding_method='HALF-UP')
    #                             freight_currency_rate = self.freight_currency_rate
    #                             currency_id = self.freight_currency
    #                         # if self.invoice_id.type == 'out_invoice':
    #                         #     cost_profit_line.write({
    #                         #         'list_price': price_unit or 0,
    #                         #         'profit_qty': self.quantity or False,
    #                         #         'profit_currency_rate': self.freight_currency_rate,
    #                         #     })
    #                         #
    #                         # elif self.invoice_id.type == 'in_invoice':
    #
    #                         # print('>>>> onchange_freight_booking price_unit=', str(price_unit))
    #                         # price_unit = invoice_line_item.price_subtotal / self.quantity
    #                         total_cost = total_cost + price_unit
    #                         total_qty += self.quantity
    #                         vendor_ids_list = []
    #                         # vendor_bill_ids_list = []
    #                         vendor_ids_list.append(self.invoice_id.partner_id.id)
    #                         # vendor_bill_ids_list.append(self.invoice_id.id)
    #                         # print('vendor_ids_list', vendor_ids_list)
    #                         # print('vendor_ids_list', vendor_bill_ids_list)
    #                         # print('new_parent_id', self.env.context.get('new_parent_id'))
    #                         # print('parent_id', self.inv_parent_id)
    #                         cost_profit_line.write({
    #                             'cost_price': float_round(total_cost, 2, rounding_method='HALF-UP'),
    #                             'cost_qty': total_qty,
    #                             'invoiced': True,
    #                             'vendor_id': self.invoice_id.partner_id.id,
    #                             'vendor_bill_id': self.invoice_id.id,
    #                             'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
    #                             'cost_currency': currency_id.id,
    #                             'cost_currency_rate': freight_currency_rate,
    #                             # 'vendor_bill_ids': [(4, self.invoice_id._ids)],
    #                             # 'vendor_bill_ids': [(4, vendor_bill_ids_list)],
    #                         })
    #
    #                 if not booking.analytic_account_id:
    #                     # print('>>>> onchange_freight_booking no analytic account')
    #                     values = {
    #                         'partner_id': booking.customer_name.id,
    #                         'name': '%s' % booking.booking_no,
    #                         'company_id': self.env.user.company_id.id,
    #                     }
    #                     analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #                     booking.write({'analytic_account_id': analytic_account.id,
    #                                    })
    #                     self.account_analytic_id = analytic_account.id
    #                 else:
    #                     # print('>>>> onchange_freight_booking with AA')
    #                     self.account_analytic_id = booking.analytic_account_id.id
    #         # if check_booking:
    #         #    booking.action_calculate_cost()
    #         if not check_booking:
    #             # TODO - add product
    #             cost_profit_obj = self.env['freight.cost_profit']
    #             if self.freight_currency_rate != 1:
    #                 price_unit = float_round(
    #                     self.price_subtotal / self.quantity / self.freight_currency_rate,
    #                     6, rounding_method='HALF-UP')
    #             else:
    #                 price_unit = float_round(self.price_subtotal / self.quantity, 2,
    #                                          rounding_method='HALF-UP')
    #             cost_profit_line = cost_profit_obj.create({
    #                 'product_id': self.product_id.id or False,
    #                 'product_name': self.name or False,
    #                 'booking_id': booking.id or '',
    #                 'cost_qty': self.quantity or 0,
    #                 'cost_currency': self.freight_currency.id,
    #                 'cost_currency_rate': self.freight_currency_rate or 1.0,
    #                 'cost_price': float_round(price_unit, 2, rounding_method='HALF-UP'),
    #                 'vendor_id': self.invoice_id.partner_id.id or False,
    #                 'vendor_bill_id': self.invoice_id.id or 0.0,
    #                 'invoiced': True,
    #             })
    #             self.wh_line_id = cost_profit_line
    #             booking.write({'cost_profit_ids': cost_profit_line or False})
    #             if not booking.analytic_account_id:
    #                 # print('>>>> onchange_freight_booking no analytic account')
    #                 values = {
    #                     'partner_id': booking.customer_name.id,
    #                     'name': '%s' % booking.booking_no,
    #                     'company_id': self.env.user.company_id.id,
    #                 }
    #                 analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #                 booking.write({'analytic_account_id': analytic_account.id,
    #                                })
    #                 self.account_analytic_id = analytic_account.id
    #             else:
    #                 self.account_analytic_id = booking.analytic_account_id.id
    #             #raise exceptions.ValidationError('Product Not Found in Booking Job Cost&Profit')
