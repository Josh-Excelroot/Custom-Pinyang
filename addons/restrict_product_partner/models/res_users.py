from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    product_ids = fields.Many2many('product.template', string='Product')
    category_ids = fields.Many2many('product.category', string='Category')
    allow_by = fields.Selection(
        [('product', 'Product'), ('product_Category', 'Product Category'), ('all', 'Product/Category')],
        default='product_Category', string='Allow By')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)


    @api.multi
    @api.onchange('allow_by')
    def _onchange_allow(self):
        for user in self:
            user.category_ids = [(6, 0, [])]
            user.product_ids = [(6, 0, [])]

