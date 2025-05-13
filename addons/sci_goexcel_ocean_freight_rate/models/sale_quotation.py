from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange', required=True)
