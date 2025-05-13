from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    order_type = fields.Selection([('sale_order', 'Sale Order'), ('prospect', 'Prospect')], string="Order type",
                                  default='sale_order',
                                  track_visibility='onchange')
    @api.multi
    def action_prospect_creation(self):
        self.ensure_one()
        view = self.env.ref('prospect_creation.prospect_creation_view_form')
        return {
            'name': 'Create Prospect',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'prospect.creation.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        res = super(SaleQuotation, self).create(vals)
        if res.opportunity_id and res.partner_id:
            res.opportunity_id.partner_id = res.partner_id.id
        return res
