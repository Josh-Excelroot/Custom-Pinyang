from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class Invoice(models.Model):
    _inherit = "account.invoice"

    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange')
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange')
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', track_visibility='onchange')

    @api.multi
    def action_service(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_charge_base.charge_view_form')
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'charge.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(invoice_id=self.id),
        }