from odoo import api, fields, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.model
    def create(self, vals):
        if self._context.get('install_mode'):
            vals_list = []
            for company in self.env['res.company'].search([]):
                new_vals = vals.copy()
                new_vals['company_id'] = company.id
                vals_list.append(new_vals)
            res = super(IrSequence, self).create(vals_list)
            return res
        res = super(IrSequence, self).create(vals)
        return res
