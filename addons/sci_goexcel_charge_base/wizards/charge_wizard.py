from odoo import api, fields, models


class ServiceChargeWizard(models.TransientModel):
    _name = 'charge.wizard'

    service = fields.Selection([], string='Service')

class ServiceChargeWizardLine(models.TransientModel):
    _name = 'charge.wizard.line'