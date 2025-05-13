from odoo import api, models, fields, _


class TechnicalCustomerPlan(models.Model):
    _inherit = 'technical.customer.plan'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", copy=False)
