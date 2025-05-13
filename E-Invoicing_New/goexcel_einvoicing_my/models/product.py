from odoo import api, fields, models, exceptions
import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = "product.product"

    classification_item = fields.Many2one('classification.type', string='Classification Name')
    self_bill_classification_item = fields.Many2one('classification.type', string='Self Billed Classification')
    enable_e_invoice = fields.Boolean(string="Enable E-invoice", compute='check_einvoice_enable')

    def check_einvoice_enable(self):
        for rec in self:
            rec.enable_e_invoice = self.env.user.company_id.enable_e_invoice

