from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    #date_format = fields.Many2one('ocr.date.format', string='OCR Date Format')
    ocr_partner_template = fields.Many2one('ocr.partner.template', string='OCR Partner Template')

