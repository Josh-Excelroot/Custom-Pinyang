from odoo import models,fields, api


class FreightLetterTemplate(models.Model):
    _inherit = 'sale.letter.template'

    doc_type = fields.Selection(selection_add=[('bc', 'Booking Confirmation')])

