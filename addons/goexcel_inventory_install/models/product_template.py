from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Product(models.Model):
    _inherit = 'product.template'
    _order = 'order_number'

    order_number = fields.Integer()

    @api.constrains('order_number')
    def minimum_order_number(self):
        for rec in self:
            if rec.order_number < 0:
                raise ValidationError('Order number cannot be negative!')