# 1. Standard library imports
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class HRChangeAttendance(models.TransientModel):
    _inherit = 'hr.change.attendance'

    asignin = fields.Float('Actual Sign In')
    asignout = fields.Float('Actual Sign Out')

    @api.multi
    def apply_changes(self):
        """Appled Changes."""
        super(HRChangeAttendance, self).apply_changes()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        get_changes = self.env[active_model].browse(active_id)
        get_changes.update({'asignin': self.asignin,
                            'asignout': self.asignout,
                            'overtime': self.overtime,
                            'latein': self.latein,
                            'difftime': self.difftime,
                            'note': self.reason})
