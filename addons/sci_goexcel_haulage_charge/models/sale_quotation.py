from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_service(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_haulage_charge.service_view_form')
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.charge.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(sq_id=self.id),
        }