# 1. Standard library imports
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _, http
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_notify_hr = fields.Boolean(string="Notify HR", related='company_id.is_notify_hr', readonly=False)
    email_list_ids = fields.Many2many(comodel_name='res.users', related='company_id.email_list_ids', readonly=False)

    @api.constrains('is_notify_hr', 'email_list_ids')
    def check_user_group_validation(self):
        for res in self:
            print('check_user_group_validation')