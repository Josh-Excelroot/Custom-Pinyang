from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_won_stage = fields.Boolean("Is Won Stage?", default=False)
    won_true = fields.Boolean("Won", default=False)

    @api.onchange('is_won_stage','won_true')
    def won_onchange(self):
        if self.is_won_stage:
            self.probability = 100.0
            self.won_true = True
        else:
            self.won_true = False
