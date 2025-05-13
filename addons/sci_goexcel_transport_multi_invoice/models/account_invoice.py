from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Invoice for multiple RFT feature only available for Customer Invoice yet. See create_update_rft_cost_profit_line


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def get_cost_profit_amount_values(self, values, profit=True, positive=True):
        qty = values['quantity']
        currency = values.get('freight_currency')
        currency_rate = values['freight_currency_rate']
        if values.get('freight_currency') != self.env.user.company_id.currency_id.id:
            unit_price = values['freight_foreign_price']
        else:
            unit_price = values['price_unit']

        if not positive:
            unit_price = -unit_price

        vals = [qty, currency, currency_rate, unit_price, True]

        if profit:
            keys = ['sales_qty', 'sales_currency', 'sale_currency_rate', 'unit_price', 'added_to_invoice']
        else:  # cost
            keys = ['cost_qty', 'cost_currency', 'cost_currency_rate', 'cost_price', 'invoiced']

        return dict(zip(keys, vals))

    def get_cost_profit_product_values(self, values):
        return {
            'product_id': values.get('product_id') or self.product_id,
            'product_name': values.get('name') or self.name
        }

    def create_update_rft_cost_profit_line(self):
        profit, positive = True, True
        # profit True : Sales values | profit False : Cost values
        # positive True : unit price in positive | positive False : unit price in negative

        # comment/remove return, if you want to make this feature work on respective invoice's type
        invoice = self.invoice_id
        if invoice.type == 'out_invoice' and invoice.debit_invoice_id:  # CUSTOMER DEBIT NOTE
            profit, positive = True, True
            return False
        elif invoice.type == 'out_invoice':  # CUSTOMER INVOICE
            profit, positive = True, True
            # return False
        elif invoice.type == 'out_refund':  # CUSTOMER CREDIT NOTE
            profit, positive = True, False
            return False
        elif invoice.type == 'in_invoice':  # VENDOR BILL OR VENDOR DEBIT NOTE
            profit, positive = False, True
            return False
        elif invoice.type == 'in_refund':  # VENDOR CREDIT NOTE / REFUND
            profit, positive = False, False
            return False

        values = self.read()[0]
        for key, val in values.items():
            if type(val) == tuple:
                values[key] = val[0]
        cost_profit_line_vals = self.get_cost_profit_amount_values(values, profit=profit, positive=positive)
        cost_profit_line_vals['uom_id'] = values.get('uom_id')
        cost_profit_line_vals.update(self.get_cost_profit_product_values(values))
        if self.rft_line_id:
            self.rft_line_id.write(cost_profit_line_vals)
            return True
        else:
            cost_profit_line_vals.update({'invoice_id': self.invoice_id.id, 'invoice_line_id': self.id})
        if self.rft_id:
            cost_profit_line = self.rft_id.get_product_cost_profit_line(values.get('product_id'), is_invoice=profit, exception_line_ids=[])
            if cost_profit_line:
                cost_profit_line[0].write(cost_profit_line_vals)
            else:
                cost_profit_line_vals['rft_transport_id'] = self.rft_id.id
                cost_profit_line = self.rft_line_id.create(cost_profit_line_vals)
            self.rft_line_id = cost_profit_line[0].id

    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        if res.invoice_id.invoice_type == 'lorry' and res.rft_id:
            res.create_update_rft_cost_profit_line()
        return res

    @api.multi
    def write(self, vals):
        if self.invoice_id.invoice_type == 'lorry':
            if 'rft_line_id' not in vals and 'rft_id' in vals and self.rft_id and vals.get('rft_id') != self.rft_id.id:
                if vals.get('rft_id'):
                    raise ValidationError('RFT can not be changed.\n'
                                          'Please delete the invoice line and add a new line with required RFT.')
                else:
                    raise ValidationError('RFT can not be removed.\n'
                                          'Please delete the invoice line.')

        res = super(AccountInvoiceLine, self).write(vals)
        if self.invoice_id.invoice_type == 'lorry' and self.rft_id and not vals.get('rft_line_id'):
            self.create_update_rft_cost_profit_line()
        return res

    @api.multi
    def unlink(self):
        self.rft_line_id.remove_invoice()
        return super(AccountInvoiceLine, self).unlink()
