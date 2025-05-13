from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_billable = fields.Boolean(string='Is Billable', default=True,
                                 help='Is this Charge Code has cost that linked to vendor bill?')

    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default='service', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')

    is_air_freight_product = fields.Boolean(string='Is Air Freight Product', default=False)

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_billable = fields.Boolean(string='Is Billable', default=True,
                                 help='Is this Charge Code has cost that linked to vendor bill?')
    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default='service', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')

    is_air_freight_product = fields.Boolean(string='Is Air Freight Product', default=False)