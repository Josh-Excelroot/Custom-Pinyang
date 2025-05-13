# 1. Standard library imports
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class ResCompany(models.Model):
    _inherit = 'res.company'

    is_notify_hr = fields.Boolean(string="Notify HR")
    email_list_ids = fields.Many2many(comodel_name='res.users', relation='email_list_configuration_rel')