from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    warning = fields.Boolean(string='Warning', default=False)
    show_error = fields.Boolean(String="Show Error Message", default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        warning = param.get_param('restrict_product_partner.warning')
        show_error = param.get_param('restrict_product_partner.show_error')
        res.update(warning=warning, show_error=show_error)
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        warning = self.warning or False
        param.set_param('restrict_product_partner.warning', warning)
        show_error = self.show_error or False
        param.set_param('restrict_product_partner.show_error', show_error)
        if warning and show_error:
            raise ValidationError("You can either show warning or error on partner duplication but not both.")
        return res