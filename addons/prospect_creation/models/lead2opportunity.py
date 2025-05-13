from odoo import api, models, fields, _

class CRMLead2Opportunity(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    action = fields.Selection(
        [('exist', 'Link to an existing customer'), ('create', 'Create a new prospect'),
         ('nothing', 'Do not link to a customer')],
        'Related Customer', default="create")



