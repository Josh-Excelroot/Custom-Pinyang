from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    #Change the display name when user select partner
    def name_get(self):
        res = []
        for field in self:
            if field.ref:
                res.append((field.id, '%s %s' % (field.ref, field.name)))
            else:
                res.append((field.id, '%s %s' % ('', field.name)))

        return res

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'ref')
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=False)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            if partner.ref and len(partner.ref) > 0:
                name = names.get(partner.id)
                new_name = name.replace(partner.ref, '')
                partner.display_name = new_name.strip()
            else:
                partner.display_name = names.get(partner.id)