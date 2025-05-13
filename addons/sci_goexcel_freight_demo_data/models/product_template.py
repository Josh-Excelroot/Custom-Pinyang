from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def create_variant_ids(self):
        variants = super(ProductTemplate, self).create_variant_ids()
        # after creating product template, check if the template has the type value (a required field)
        for template in self:
            for variant in template.product_variant_ids:
                if not variant.type:
                    variant.write({'type': template.type})
        return variants
