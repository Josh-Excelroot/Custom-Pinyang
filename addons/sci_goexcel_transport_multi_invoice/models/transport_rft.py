from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class TransportRFT(models.Model):
    _inherit = "transport.rft"

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.rft_no))
        return result

    def get_product_cost_profit_line(self, product_id, is_invoice, exception_line_ids):
        # will get the cost profit lines of related rft which has same product selected
        if is_invoice:
            cost_profit_lines = self.cost_profit_ids_rft.filtered(lambda cp: not cp.added_to_invoice and cp.product_id.id == product_id and cp.id not in exception_line_ids)
        else:
            cost_profit_lines = self.cost_profit_ids_rft.filtered(lambda cp: not cp.invoiced and cp.product_id.id == product_id and cp.id not in exception_line_ids)
        return cost_profit_lines

    @api.multi
    def write(self, vals):
        return super(TransportRFT, self).write(vals)


class RFTCostProfit(models.Model):
    _inherit = 'rft.cost.profit'

    invoice_id = fields.Many2one('account.invoice', readonly=True)
    invoice_line_id = fields.Many2one('account.invoice.line', readonly=True)

    def remove_invoice(self):
        self.write({
            'sales_qty': 0,
            'sales_currency': False,
            'sale_currency_rate': 1,
            'unit_price': 0,
            'added_to_invoice': False,
            'invoice_id': False,
            'invoice_line_id': False
        })

    @api.multi
    def write(self, vals):
        if 'added_to_invoice' in vals and not vals.get('added_to_invoice'):
            vals.update({'invoice_id': False, 'invoice_line_id': False})
            self.invoice_line_id.write({'rft_id': False, 'rft_line_id': False})
        return super(RFTCostProfit, self).write(vals)
