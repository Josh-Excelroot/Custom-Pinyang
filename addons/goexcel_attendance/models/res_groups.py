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

class ResGroups(models.Model):
    _inherit = 'res.groups'

    full_name = fields.Char(compute='_compute_full_name', string='Group Name', search='_search_full_name', store=True)

