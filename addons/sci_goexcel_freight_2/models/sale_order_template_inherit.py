from odoo import models,fields, api



class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    cost_price = fields.Float(string="Cost Price")
    currency_id = fields.Many2one('res.currency', string='Currency')
    cost_currency = fields.Many2one('res.currency', string="Cost Currency")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            name = self.product_id.name
            if self.product_id.description_sale:
                name += '\n' + self.product_id.description_sale
            self.name = name
            self.price_unit = self.product_id.lst_price
            self.product_uom_id = self.product_id.uom_id.id
            domain = {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            return {'domain': domain}



