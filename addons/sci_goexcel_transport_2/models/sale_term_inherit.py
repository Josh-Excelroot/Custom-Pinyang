from odoo import models,fields, api


class TransportLetterTemplate(models.Model):
    _inherit = 'sale.letter.template'

    doc_type = fields.Selection(selection_add=[('dot', 'Delivery Order Transportation')])

