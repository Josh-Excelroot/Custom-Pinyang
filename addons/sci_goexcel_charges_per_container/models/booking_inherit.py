from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking1(models.Model):
    _inherit = "freight.booking"

    # CR5
    @api.onchange('cost_profit_ids')
    def _onchange_cost_profit_ids(self):
        # super(FreightBooking, self)._onchange_cost_profit_ids()
        for cost_profit in self.cost_profit_ids:
            if cost_profit.product_id:
                product = self.env['container.volume.charges'].search([('uom', '=', cost_profit.product_id.uom_id.id)])
                if product:
                    print(product)
                    product_exclude = self.env['container.volume.charges.line'].search(
                        [('charges_id', '=', product.id), ('product_id', '=', cost_profit.product_id.id)])
                    print(product_exclude)
                    if not product_exclude:
                        if cost_profit.profit_qty == 0 or cost_profit.profit_qty == 1:
                            cost_profit.profit_qty = self.container_qty
                        if cost_profit.cost_qty == 0 or cost_profit.cost_qty == 1:
                            cost_profit.cost_qty = self.container_qty