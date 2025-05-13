# 1. Standard library imports
from geopy.distance import geodesic
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

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_location = fields.Many2many(comodel_name='location.data')
    enable_attendance_location = fields.Boolean()

    @api.onchange('enable_attendance_location')
    def _clear_attendance_location(self):
        for rec in self:
            if not rec.enable_attendance_location:
                rec.attendance_location = False

    @api.multi
    def attendance_action_change(self):
        print('attendance_action_change')
        res = super().attendance_action_change()
        attendance_location = self.env.context.get('attendance_location', False)
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if attendance_location:
            if employee.enable_attendance_location:
                closest_location = False
                closest_distance = False
                is_allowed_checkin = False
                for location in employee.attendance_location:
                    distance_in_meter = geodesic((location.latitude, location.longitude), (attendance_location[0], attendance_location[1])).meters
                    if distance_in_meter <= location.radius:
                        print('dim ', distance_in_meter, location.radius)
                        is_allowed_checkin = True
                        if not closest_distance and not closest_location:
                            closest_location = location.id
                            closest_distance = distance_in_meter
                        elif distance_in_meter >= closest_distance:
                            pass
                        else:
                            closest_location = location.id
                            closest_distance = distance_in_meter
                    print(closest_location, closest_distance)
                if not is_allowed_checkin:
                    raise UserError('Check-in unsuccessful. You are currently outside the designated location.')
                print('self.attendance_state ', self.attendance_state)
                if self.attendance_state == 'checked_in':
                    vals = {
                        'attendance_location_checkin': closest_location,
                        'location_distance_checkin': closest_distance,
                        'check_in_latitude': attendance_location[0],
                        'check_in_longitude': attendance_location[1],
                    }
                    print('in vals ', vals)
                    res.write(vals)
                else:
                    vals = {
                        'attendance_location_checkout': closest_location,
                        'location_distance_checkout': closest_distance,
                        'check_out_latitude': attendance_location[0],
                        'check_out_longitude': attendance_location[1],
                    }
                    print('out vals ', vals)
                    res.write(vals)
        print('res ', res)
        return res
