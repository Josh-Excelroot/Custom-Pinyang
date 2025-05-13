from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    invoice_preview_field = fields.Boolean("Invoice Preview", config_parameter='account.invoice_preview_field')
    vendor_preview_field = fields.Boolean("Vendor Preview", config_parameter='account.vendor_preview_field')

