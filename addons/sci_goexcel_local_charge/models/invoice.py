from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class Invoice(models.Model):
    _inherit = "account.invoice"

    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange')
    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange')

