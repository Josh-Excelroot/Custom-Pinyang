from odoo import api, models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    company_rft_count = fields.Integer(compute="_compute_company_rft_count")

    def _compute_company_rft_count(self):
        for partner in self:
            rfts = self.env["transport.rft"].search(
                [("billing_address", "=", partner.id),]
            )
            partner.company_rft_count = len(rfts)

