from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class Booking(models.Model):
    _inherit = "freight.booking"

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
            'context': dict(booking_id=self.id),
        }