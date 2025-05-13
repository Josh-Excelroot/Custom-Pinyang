# 1. Standard library imports
import hashlib
import json
import requests
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class LocationData(models.Model):
    _name = 'location.data'

    name = fields.Char(required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    radius = fields.Float(string='Radius (m)', required=True)

    @api.constrains('radius')
    def _check_radius_value(self):
        for rec in self:
            if rec.radius <= 0.0:
                raise UserError('Radius cannot be 0 or lower!')