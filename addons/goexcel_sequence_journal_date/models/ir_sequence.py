# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    based_on_document_date = fields.Boolean('Based on Document Date?', default=True)
