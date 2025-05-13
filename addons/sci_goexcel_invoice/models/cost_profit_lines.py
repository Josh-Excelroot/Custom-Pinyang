from odoo import api, fields, models, exceptions,_
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import date
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class FreightInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('freight_currency_rate', 'freight_foreign_price', 'freight_currency')
    def onchange_freight_currency_rate(self):
        # if self.freight_currency != self.env.user.company_id.currency_id:
        self.price_unit = self.freight_foreign_price * self.freight_currency_rate
        # else:
        #     self.price_unit = self.freight_foreign_price

    def delete_related_cost_profit_line(self, is_invoice):
        for rec in self:
            rec.transfer_cost_profit_lines(False, is_invoice)

    def get_cost_profit_amount_values(self, values, profit=True, positive=True):
        qty = values['quantity']
        currency = values.get('freight_currency')
        currency_rate = values['freight_currency_rate']
        if values.get('freight_currency') != self.env.user.company_id.currency_id.id:
            unit_price = values['freight_foreign_price']
        else:
            unit_price = values['price_unit']

        if not values['invoice'].is_company_and_invoice_currency_same():
            if self.is_invoice_and_line_currency_same(values):
                currency_rate = values['invoice_currency_rate']
            else:
                if values.get('freight_currency') != self.env.user.company_id.currency_id.id:
                    currency_rate = values['invoice_currency_rate'] * values['freight_currency_rate']
                else:
                    unit_price = round(unit_price * values['invoice_currency_rate'], 2)
                    currency_rate = 1

        if not positive:
            unit_price = -unit_price

        vals = [qty, currency, currency_rate, unit_price, True]

        if profit:
            keys = ['profit_qty', 'profit_currency', 'profit_currency_rate', 'list_price', 'added_to_invoice']
        else:  # cost
            keys = ['cost_qty', 'cost_currency', 'cost_currency_rate', 'cost_price', 'invoiced']

        return dict(zip(keys, vals))

    def get_cost_profit_product_values(self, values):
        return {
            'product_id': values['product_id'] or self.product_id,
            'product_name': values['name'] or self.name
        }

    def make_cost_profit_line_values(self, values, invoice, profit=True, positive=True):
        vals = {}
        if values == {}:
            # CN/DN
            vals['invoice_id'] = self.invoice_id.id
            vals['inv_line_id'] = self.id
            values = self.read()[0]
            for key, val in values.items():
                if type(val) == tuple:
                    values[key] = val[0]
        values.update({
            'invoice': invoice,
            'invoice_currency': invoice.currency_id.id,
            'invoice_currency_rate': (invoice.exchange_rate_inverse or 1)
        })
        vals.update(self.get_cost_profit_amount_values(values, profit, positive))
        vals['uom_id'] = values.get('uom_id')
        vals.update(self.get_cost_profit_product_values(values))
        vals['booking_id'] = invoice.freight_booking.id
        if not profit:
            vals['vendor_id'] = invoice.partner_id.id

        return vals

    def make_cost_profit_line(self, values, invoice, profit=True, positive=True):
        # Profit=True, Positive=True == Customer Invoice
        # Profit=False(Cost), Positive=True ==
        # Profit=True, Positive=False(Negative) ==
        # Profit=False(Cost), Positive=False(Negative) ==
        cost_profit_values = self.make_cost_profit_line_values(values, invoice, profit, positive)
        cost_profit_line = self.env['freight.cost_profit'].create(cost_profit_values)
        return cost_profit_line

    def transfer_cost_profit_lines(self, selected_booking_id, is_invoice):
        cost_profit_lines = self.mapped('booking_line_id')
        if selected_booking_id:
            self.write({'fright_booking': selected_booking_id})
            cost_profit_lines.write({'booking_id': selected_booking_id})
            # for cp_line in cost_profit_lines:
            #     cp_line.booking_id = selected_booking_id
        else:
            # TODO - what should we do when freight_booking of invoice set to NULL
            if is_invoice:
                write_vals = ['invoice_id', 'inv_line_id', 'added_to_invoice']
            else:
                write_vals = ['vendor_id', 'bill_id', 'vendor_bill_id', 'bill_line_id', 'invoiced']
            cost_profit_lines.write(dict(zip(write_vals, [False] * 5)))
            self.write({'freight_booking': False, 'booking_line_id': False})

    # @api.constrains('freight_currency')
    # def validate_currency(self):
    #     for rec in self:
    #         if 'create_from_job' in self._context:
    #             rec.invoice_id.validate_currency()

    def is_invoice_and_line_currency_same(self, vals=None):
        if vals is None:
            vals = {}
        invoice_currency_id = vals.get('invoice_currency') or self.invoice_id.currency_id.id
        line_currency_id = vals.get('freight_currency') or self.freight_currency.id
        return invoice_currency_id == line_currency_id


class FreightInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_invoice_type(self):
        if self.type == 'out_invoice' and self.debit_invoice_id:
            return 'Customer Debit Note'
        elif self.type == 'out_invoice':
            return 'Customer Invoice'
        elif self.type == 'out_refund':
            return 'Customer Credit Note'
        elif self.type == 'in_invoice' and self.debit_invoice_id:
            return 'Vendor Debit Note'
        elif self.type == 'in_invoice':
            return 'Vendor Bill'
        elif self.type == 'in_refund':
            return 'Vendor Credit Note / Refund'
        return ''

    # @api.constrains('currency_id', 'invoice_line_ids.freight_currency')
    # def validate_currency(self):
    #     if not self.is_freight_booking_invoice({}):
    #         return True
    #     invoice_currency = self.currency_id
    #     company_currency = self.env.user.company_id.currency_id
    #     if invoice_currency != company_currency:
    #         for line in self.invoice_line_ids:
    #             if line.freight_currency != invoice_currency and line.freight_currency != company_currency:
    #                 if 'create_from_job' in self._context:
    #                     raise ValidationError(f'Cost & profit line can not be selected with currency other than {company_currency.name} and {invoice_currency.name} (Customer\'s Pricelist)')
    #                 else:
    #                     raise ValidationError(f'This {self.get_invoice_type()} can not have line with currency other than {company_currency.name} and {invoice_currency.name}')


    @api.multi
    def unlink(self):
        for rec in self:
            is_invoice = rec.type in ['out_invoice', 'out_refund']
            rec.invoice_line_ids.delete_related_cost_profit_line(is_invoice)
        return super(FreightInvoice, self).unlink()


    @api.constrains('exchange_rate_inverse')
    def change_cost_profit_line_currency_rate(self):
        invoice_type = self.get_invoice_type()
        if invoice_type in ['Customer Invoice', 'Vendor Bill'] and not self.is_company_and_invoice_currency_same():
            for line in self.invoice_line_ids:
                if line.is_invoice_and_line_currency_same() and line.booking_line_id:
                    if invoice_type == 'Customer Invoice':
                        line.booking_line_id.profit_currency_rate = self.exchange_rate_inverse
                    else:
                        line.booking_line_id.cost_currency_rate = self.exchange_rate_inverse

    def is_company_and_invoice_currency_same(self, vals=None):
        if vals is None:
            vals = {}
        company_currency_id = self.env.user.company_id.currency_id.id
        invoice_currency_id = (vals.get('currency_id') or self.currency_id.id)
        return invoice_currency_id == company_currency_id

    def is_freight_booking_invoice(self, vals):
        if 'invoice_type' in vals:
            invoice_type = vals.get('invoice_type')
        else:
            invoice_type = self.invoice_type
        if 'freight_booking' in vals:
            freight_booking = vals.get('freight_booking')
        else:
            freight_booking = self.freight_booking
        return invoice_type != 'lorry'

    @api.multi
    def write(self, vals):
        for inv in self:
            if not inv.is_freight_booking_invoice(vals):
                return super(FreightInvoice, inv).write(vals)

            account_invoice_line_obj = self.env['account.invoice.line']
            cost_profit_obj = self.env['freight.cost_profit']
            freight_booking_obj = self.env['freight.booking']
            new_cost_profit_lines = []
            company_currency_id = self.env.user.company_id.currency_id.id
            invoice_currency_id = (vals.get('currency_id') or inv.currency_id.id)
            company_and_invoice_currency_same = invoice_currency_id == company_currency_id

            selected_freight_booking_temp = inv.freight_booking
            if 'freight_booking' in vals:
                selected_freight_booking_temp = self.check_analytic_account_freight_booking(vals['freight_booking'])

            if inv.type in ['in_invoice',
                            'out_invoice'] and not inv.debit_invoice_id and inv.freight_booking:  # CUSTOMER INVOICE
                is_invoice = inv.type == 'out_invoice'  # or bill

                # if 'freight_booking' in vals:
                # transfer lines from old freight_booking to selected freight_booking
                # self.invoice_line_ids.transfer_cost_profit_lines(vals['freight_booking'], is_invoice=is_invoice)

                if 'invoice_line_ids' in vals:
                    for invoice_line in vals['invoice_line_ids']:
                        line_vals = invoice_line[2]

                        if invoice_line[0] in [1, 0]:
                            if line_vals.get('freight_booking'):
                                selected_freight_booking = self.check_analytic_account_freight_booking(
                                    line_vals.get('freight_booking'))
                            elif inv.freight_booking:
                                selected_freight_booking = inv.freight_booking
                            else:
                                selected_freight_booking = selected_freight_booking_temp

                        if invoice_line[0] == 1:
                            # update related c&p line
                            invoice_line_rec = account_invoice_line_obj.browse(invoice_line[1])
                            line_currency_id = line_vals.get('freight_currency') or invoice_line_rec.freight_currency.id
                            invoice_and_line_currency_same = invoice_currency_id == line_currency_id
                            company_and_line_currency_same = company_currency_id == line_currency_id
                            cost_profit_line = invoice_line_rec.booking_line_id
                            cost_profit_values = {}
                            # Ahmad Zaman - 28/11/24 - Tax Line Changes will Reflect in Cost & Profit lines
                            if is_invoice:
                                keys = ['profit_qty', 'profit_currency', 'profit_currency_rate', 'list_price', 'tax_id']
                            else:
                                keys = ['cost_qty', 'cost_currency', 'cost_currency_rate', 'cost_price']

                            if 'freight_booking' in line_vals:
                                raise ValidationError('Booking can not be changed.\n'
                                                      'Please delete the line and add a new line with required Booking.')

                            if 'product_id' in line_vals:
                                cost_profit_values['product_id'] = line_vals['product_id']
                            if 'name' in line_vals:
                                cost_profit_values['product_name'] = line_vals['name']
                            if 'quantity' in line_vals:
                                cost_profit_values[keys[0]] = line_vals['quantity']
                            if 'uom_id' in line_vals:
                                cost_profit_values['uom_id'] = line_vals['uom_id']
                            if 'freight_currency' in line_vals:
                                cost_profit_values[keys[1]] = line_vals['freight_currency']
                            if 'freight_currency_rate' in line_vals:
                                cost_profit_values[keys[2]] = line_vals['freight_currency_rate']
                            if 'price_unit' in line_vals or 'freight_foreign_price' in line_vals or 'freight_currency_rate' in line_vals or 'freight_currency' in line_vals:
                                foreign_currency_price = line_vals.get(
                                    'freight_foreign_price') or invoice_line_rec.freight_foreign_price
                                foreign_currency_rate = line_vals.get(
                                    'freight_currency_rate') or invoice_line_rec.freight_currency_rate
                                foreign_currency = line_vals.get(
                                    'freight_currency') or invoice_line_rec.freight_currency
                                price_unit = line_vals.get('price_unit') or invoice_line_rec.price_unit
                                invoice_exchange_rate = vals.get('exchange_rate_inverse') or inv.exchange_rate_inverse
                                if line_vals.get('freight_currency') and line_vals[
                                    'freight_currency'] != self.env.user.company_id.currency_id.id:
                                    cost_profit_values[keys[3]] = foreign_currency_price
                                elif not line_vals.get(
                                        'freight_currency') and invoice_line_rec.freight_currency and invoice_line_rec.freight_currency != self.env.user.company_id.currency_id:
                                    cost_profit_values[keys[3]] = foreign_currency_price
                                    if invoice_line_rec.freight_currency != inv.currency_id:
                                        cost_profit_values[keys[2]] = foreign_currency_rate * invoice_exchange_rate
                                else:
                                    if not company_and_invoice_currency_same:
                                        cost_profit_values[keys[3]] = round(price_unit * invoice_exchange_rate, 2)
                                        if invoice_and_line_currency_same or company_and_line_currency_same:
                                            cost_profit_values[keys[2]] = 1
                                            if company_and_line_currency_same and foreign_currency_rate != (
                                                    1 / invoice_exchange_rate):
                                                # for MYR line rate which is different from inverse of invoice rate
                                                cost_profit_values[keys[3]] = round(price_unit, 2)
                                                cost_profit_values[keys[2]] = foreign_currency_rate
                                        else:
                                            cost_profit_values[keys[2]] = foreign_currency_rate * invoice_exchange_rate

                                    else:
                                        cost_profit_values[keys[3]] = round(price_unit, 2)
                                        cost_profit_values[keys[2]] = 1
                                        line_vals['freight_foreign_price'] = price_unit
                                        line_vals['freight_currency_rate'] = 1
                            # Ahmad Zaman - 30/7/24 - Tax Line Changes will Reflect in Cost & Profit lines
                            if 'invoice_line_tax_ids' in line_vals and is_invoice:
                                cost_profit_values[keys[4]] = line_vals['invoice_line_tax_ids']

                            if not is_invoice:
                                cost_profit_values['vendor_id'] = vals.get('partner_id') or inv.partner_id.id

                            cost_profit_line.write(cost_profit_values)

                        elif invoice_line[0] == 0:
                            # new c&p line
                            if line_vals.get('freight_currency') == self.env.user.company_id.currency_id.id:
                                line_vals['freight_foreign_price'] = line_vals['price_unit']
                                line_vals['freight_currency_rate'] = 1

                            cost_profit_line = selected_freight_booking.get_product_cost_profit_line(line_vals,
                                                                                                     is_invoice=is_invoice,
                                                                                                     exception_line_ids=new_cost_profit_lines)
                            cost_profit_values = account_invoice_line_obj.make_cost_profit_line_values(line_vals, inv,
                                                                                                       profit=is_invoice,
                                                                                                       positive=True)
                            cost_profit_values['booking_id'] = selected_freight_booking.id
                            if not is_invoice:
                                cost_profit_values['vendor_id'] = vals.get('partner_id') or inv.partner_id.id

                            if cost_profit_line:
                                cost_profit_line.write(cost_profit_values)
                            else:
                                cost_profit_line = self.env['freight.cost_profit'].create(cost_profit_values)

                            line_vals['freight_booking'] = selected_freight_booking.id
                            line_vals['account_analytic_id'] = selected_freight_booking.analytic_account_id.id
                            line_vals['booking_line_id'] = cost_profit_line.id
                            new_cost_profit_lines.append(cost_profit_line)

                        elif invoice_line[0] == 2:
                            # delete related c&p line
                            account_invoice_line_obj.browse(invoice_line[1]).delete_related_cost_profit_line(is_invoice)

                        else:
                            continue

            elif vals.get('state') == 'open' and inv.freight_booking:
                for invoice_line in inv.invoice_line_ids:
                    cost_profit = False
                    if inv.type == 'out_invoice' and inv.debit_invoice_id:  # CUSTOMER DEBIT NOTE
                        cost_profit = invoice_line.make_cost_profit_line({}, inv, profit=True, positive=True)
                    if inv.type == 'out_refund':  # CUSTOMER CREDIT NOTE
                        cost_profit = invoice_line.make_cost_profit_line({}, inv, profit=True, positive=False)
                    if inv.type == 'in_invoice' and inv.debit_invoice_id:  # VENDOR DEBIT NOTE
                        cost_profit = invoice_line.make_cost_profit_line({}, inv, profit=False, positive=True)
                    if inv.type == 'in_refund':  # VENDOR CREDIT NOTE / REFUND
                        cost_profit = invoice_line.make_cost_profit_line({}, inv, profit=False, positive=False)
                    if cost_profit:
                        invoice_line.write({
                            'freight_booking': inv.freight_booking.id,
                            'account_analytic_id': inv.freight_booking.analytic_account_id.id,
                            'booking_line_id': cost_profit.id
                        })

            res = super(FreightInvoice, self).write(vals)

            if inv.type in ['in_invoice', 'out_invoice'] and not inv.debit_invoice_id:
                if new_cost_profit_lines:
                    for cost_profit in new_cost_profit_lines:
                        related_invoice_line = inv.invoice_line_ids.filtered(lambda l: l.booking_line_id == cost_profit)
                        if is_invoice:
                            cost_profit.write({
                                'invoice_id': inv.id,
                                'inv_line_id': related_invoice_line.id,
                                'booking_id': inv.freight_booking.id
                            })
                        else:
                            cost_profit.write({
                                'bill_id': inv.id,
                                'vendor_bill_id': inv.id,
                                'bill_line_id': related_invoice_line.id,
                                'booking_id': related_invoice_line.freight_booking.id
                            })

                if 'freight_booking' in vals:
                    inv.invoice_line_ids.write({
                        'freight_booking': vals['freight_booking'],
                        'account_analytic_id': selected_freight_booking.analytic_account_id.id
                    })

            return res

    def check_analytic_account_freight_booking(self, freight_booking_id):
        if freight_booking_id:
            freight_booking = self.env['freight.booking'].browse(freight_booking_id)
            if freight_booking and not freight_booking.analytic_account_id:
                freight_booking.create_and_select_analytic_account()
            return freight_booking
        return False

    def create(self, vals):
        if not self.is_freight_booking_invoice(vals):
            return super(FreightInvoice, self).create(vals)

        ail_obj = self.env['account.invoice.line']
        freight_booking_id_temp = vals.get('freight_booking')
        freight_booking_temp = self.check_analytic_account_freight_booking(freight_booking_id_temp)

        is_invoice = vals.get('type') == 'out_invoice'  # or bill

        if not self._context.get('create_from_job') and vals.get('type') in ['in_invoice', 'out_invoice'] and not vals.get('debit_invoice_id'):# and freight_booking_id:
            for line in vals.get('invoice_line_ids', []):
                exception_cost_profit_line_ids = []
                line_vals = line[2]
                if line_vals.get('freight_booking'):
                    freight_booking_id = line_vals.get('freight_booking')
                    freight_booking = self.check_analytic_account_freight_booking(freight_booking_id)
                else:
                    freight_booking_id = freight_booking_id_temp
                    freight_booking = freight_booking_temp
                product_id = line_vals.get('product_id')
                if product_id:
                    if line_vals.get('freight_currency') == self.env.user.company_id.currency_id.id:
                        line_vals['freight_foreign_price'] = line_vals['price_unit']
                        line_vals['freight_currency_rate'] = 1
                    if freight_booking:
                        cost_profit_line = freight_booking.get_product_cost_profit_line(line_vals, is_invoice=is_invoice, exception_line_ids=exception_cost_profit_line_ids)
                        cost_profit_values = ail_obj.make_cost_profit_line_values(line_vals, self, profit=is_invoice, positive=True)
                        cost_profit_values['booking_id'] = freight_booking_id
                        if not is_invoice:
                            cost_profit_values['vendor_id'] = vals.get('partner_id')

                        if cost_profit_line:
                            cost_profit_line.write(cost_profit_values)
                        else:
                            cost_profit_line = self.env['freight.cost_profit'].create(cost_profit_values)
                        exception_cost_profit_line_ids.append(cost_profit_line.id)

                        line_vals['freight_booking'] = freight_booking_id
                        line_vals['account_analytic_id'] = freight_booking.analytic_account_id.id
                        line_vals['booking_line_id'] = cost_profit_line.id

        res = super(FreightInvoice, self).create(vals)

        if vals.get('type') in ['in_invoice','out_invoice'] and not vals.get('debit_invoice_id'):  # and freight_booking_id:
            for line in res.invoice_line_ids:
                if is_invoice:
                    line.booking_line_id.write({'invoice_id': res.id, 'inv_line_id': line.id})
                else:
                    line.booking_line_id.write({'bill_id': res.id, 'vendor_bill_id': res.id, 'bill_line_id': line.id})

        return res

    def action_invoice_cancel(self):
        if (self.type in ['in_invoice','out_invoice'] and self.debit_invoice_id) or self.type in ['in_refund','out_refund']:
            is_invoice = self.type in ['out_invoice', 'out_refund']
            self.invoice_line_ids.delete_related_cost_profit_line(is_invoice)
        super(FreightInvoice, self).action_invoice_cancel()


class FreightBooking(models.Model):
    _inherit = 'freight.booking'

    def create_and_select_analytic_account(self):
        values = {
            'partner_id': self.customer_name.id,
            'name': '%s' % self.booking_no,
            'company_id': self.env.user.company_id.id,
        }
        analytic_account = self.env['account.analytic.account'].sudo().create(values)
        self.write({'analytic_account_id': analytic_account.id})

    def get_product_cost_profit_line(self, payload, is_invoice, exception_line_ids):
        # will get the cost profit lines of related booking which has same product selected
        if is_invoice:
            cost_profit_lines = self.cost_profit_ids.filtered(lambda cp:not cp.added_to_invoice and cp.product_id.id == payload.get('product_id') and cp.id not in exception_line_ids)
        else:
            cost_profit_lines = self.cost_profit_ids.filtered(lambda cp:not cp.invoiced and cp.product_id.id == payload.get('product_id') and cp.id not in exception_line_ids)

        # TODO - filter with quantity and currency if find multiple
        # if len(cost_profit_lines) > 1:
        #     if is_invoice:
        #         cost_profit_lines = cost_profit_lines.filtered(lambda cp:cp.profit_qty == payload.get('quantity', 0))
        #     else:
        #         cost_profit_lines = cost_profit_lines.filtered(lambda cp:cp.cost_qty == payload.get('quantity', 0))
        #     if
        #     return cost_profit_lines[0]
        # else:
        return cost_profit_lines and cost_profit_lines[0]
