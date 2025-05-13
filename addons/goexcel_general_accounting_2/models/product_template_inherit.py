from odoo import fields, models, api

class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    tax_code  = fields.Char(string="Tax Code")
    display_tax_code = fields.Boolean(string="display tax code",compute="_compute_display",  store=True,
        default=False)

    @api.depends('taxes_id')
    def _compute_display(self):
        for record in self:
            if record.taxes_id:
                record.display_tax_code = True
            else:
                record.display_tax_code = False