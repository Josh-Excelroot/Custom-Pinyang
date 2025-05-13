from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class EInvoice_UOM(models.Model):
    _inherit = "uom.uom"

    uom_code = fields.Many2one(
        'einvoice.uom',
        string='E-Invoice UOM',
        readonly = False,
    )

    # @api.depends('name')
    # def _compute_uom_code(self):
    #     for record in self:
    #         matching_einvoice_uom = self.env['einvoice.uom'].search(
    #             [('uom_name'.lower(), '=', record.name.capitalize())], limit=1
    #         )
    #         record.uom_code = matching_einvoice_uom.id if matching_einvoice_uom else False