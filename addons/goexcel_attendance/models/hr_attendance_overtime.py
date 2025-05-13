# 1. Standard library imports
from datetime import datetime, timedelta
from itertools import groupby
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _, http
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class HrAttendanceOvertime(models.Model):
    _inherit = 'hr.attendance.overtime'

    overtime_active = fields.Boolean(string='Overtime Active')

    def activate_overtime(self):
        self.ensure_one()
        self.env['hr.attendance.overtime'].write({'overtime_active': False})
        self.overtime_active = True