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

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_location_checkin = fields.Many2one('location.data')
    attendance_location_checkout = fields.Many2one('location.data')
    location_distance_checkin = fields.Float()
    location_distance_checkout = fields.Float()

    def attendances_with_no_checkout(self):
        today_date = datetime.now().date() - timedelta(days=1)
        end_of_day = datetime.now()

        # Find attendances with no checkout for the current date
        attendances_no_checkout = self.env['hr.attendance'].search([
            ('check_out', '=', False),
            ('check_in', '<=', end_of_day),
            ('check_in', '>=', today_date),
        ])

        # Compile the array of attendances with no checkout
        compiled_attendances = []
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        model = 'hr.attendance'
        action_id = self.env.ref('hr_attendance.hr_attendance_action').id
        for attendance in attendances_no_checkout:
            view_type = 'form'
            url = f'{base_url}/web#model={model}&id={attendance.id}&view_type={view_type}&action={action_id}'
            compiled_attendances.append({
                'employee': attendance.employee_id,
                'manager': attendance.employee_id.parent_id,
                'url_list': url
            })
        print('compiled_attendances ', compiled_attendances)
        sorted_attendances = sorted(compiled_attendances, key=lambda x: x['manager'])
        grouped_attendances = {}
        for manager, group in groupby(sorted_attendances, key=lambda x: x['manager']):
            grouped_attendances[manager] = list(group)
        for manager, values in grouped_attendances.items():
            if manager.work_email:
                employee_list = [emp for emp in values]
                html_employee_list = '<ul>'
                for employee in employee_list:
                    print('employee ', employee)
                    html_employee_list += f'<li><a href="{employee["url_list"]}">{employee["employee"].name}</a></li>'
                html_employee_list += '</ul>'

                view_type='list'
                url = f'{base_url}/web#model={model}&view_type={view_type}&action={action_id}'
                ctx = {
                    'manager': manager,
                    'employee_list': html_employee_list,
                    'company': manager.address_id,
                    'url': url
                }
                print('ctx ', ctx)
                print(self.env.ref('goexcel_attendance.missed_attendance_template') \
                      .with_context(ctx) \
                      .send_mail(res_id=self.id, force_send=True))