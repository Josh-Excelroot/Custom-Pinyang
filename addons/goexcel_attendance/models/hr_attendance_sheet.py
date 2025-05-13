# 1. Standard library imports
from datetime import date
from itertools import groupby
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _, http
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

def calculate_overtime_pay(overtime_hours, hourly_rates):
    total_overtime_pay = 0
    remaining_hours = overtime_hours

    for i, rate in enumerate(hourly_rates):
        rate_value = rate['rate']
        print(i+1, len(hourly_rates))
        if i+1 <= len(hourly_rates)-1:
            rate_hours = hourly_rates[i+1]['hour_start'] - rate['hour_start'] #how many hours the current rate applies
        else:
            rate_hours = 24 #random number that signifies unlimited hours
        print(rate_hours, rate_value)

        if remaining_hours <= rate_hours:
            total_overtime_pay += remaining_hours * rate_value
            break
        else:
            total_overtime_pay += rate_hours * rate_value
            remaining_hours -= rate_hours

    return total_overtime_pay

class HrAttendanceSheet(models.Model):
    _inherit = 'hr.attendance.sheet'

    email_sent = fields.Boolean(invisible=True)
    manager_id = fields.Many2one(comodel_name='hr.employee', related='employee_id.parent_id')
    overtime_cost_total = fields.Float(compute='_compute_overtime_cost_total', string='Overtime Cost (RM)')

    def _compute_overtime_cost_total(self):
        for rec in self:
            total_cost = 0.0
            for line in rec.attendance_sheet_ids:
                total_cost += line.overtime_cost
            rec.overtime_cost_total = total_cost

    @api.multi
    def execute_send_to_manager(self):
        super(HrAttendanceSheet, self).execute_send_to_manager()
        for rec in self:
            config_setting = rec.env['res.config.settings'].search([], order='id DESC', limit=1)
            print('config_setting ', config_setting)
            email_string = ''
            if config_setting.is_notify_hr:
                email_list = []
                for user in config_setting.email_list_ids:
                    email_list.append(user.login)
                    pass
                email_string = ', '.join(email_list)
            if email_string:
                company_id = self.env.user.company_id
                # base url variables
                base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                model = 'hr.attendance.sheet'
                action_id = self.env.ref('hr_attendances_overtime.action_attendance_sheets1').id
                url = f'{base_url}/web#model={model}&id={rec.id}&view_type=form&action={action_id}'
                employee_url = f'<a href="{url}">{rec.employee_id.name} ({rec.date_from.strftime("%d/%m/%Y")} - {rec.date_to.strftime("%d/%m/%Y")})</a>'
                ctx = {
                    'email_string': email_string,
                    'company': company_id,
                    'manager': rec.manager_id,
                    'employee_url': employee_url
                }
                self.env.ref('goexcel_attendance.attendance_sheet_notify_hr_template').with_context(ctx).send_mail(
                    res_id=self.id, force_send=True)
        return True

    def generate_employee_attendance_sheet(self):
        #check if today need to generate attendance
        date_today = fields.Datetime.now().today()
        active_config = self.env['attendance.report.config'].search([('config_active', '=', True)])
        date_list = [multi.date for multi in active_config.multiple_dates_ids]
        date_list.sort()
        print('active_config.multiple_dates_ids ', active_config.multiple_dates_ids)
        print('date_list ', date_list)
        print('date_today.day ', date_today.day)
        if date_today.day in date_list:
            #get start date
            i = date_list.index(date_today.day) - 1
            if date_list[i] > date_today.day:
                start_date = date(date_today.year, date_today.month - 1, date_list[i])
            else:
                start_date = date(date_today.year, date_today.month, date_list[i])
            end_date = date_today

            #get employee list
            attendance = self.env['hr.attendance'].search([('check_in', '>=', start_date), ('check_out', '<=', end_date)])
            unique_employee_ids = set(record.employee_id for record in attendance)
            unique_employee_ids_list = list(unique_employee_ids)

            #base url variables
            base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            model = 'hr.attendance.sheet'
            action_id = self.env.ref('hr_attendances_overtime.action_attendance_sheets1').id

            #create attendance sheet
            attendance_sheet_list = []
            for employee in unique_employee_ids_list:
                attendance_sheet_id = self.env['hr.attendance.sheet'].search([('employee_id', '=', employee.id),
                                                        ('date_from', '=', start_date),
                                                        ('date_to', '=', end_date)], limit=1)
                if not attendance_sheet_id:
                    vals = {
                        'employee_id': employee.id,
                        'date_from':start_date,
                        'request_date_from':start_date,
                        'date_to':end_date,
                        'request_date_to':end_date,
                    }
                    attendance_sheet_id = self.env['hr.attendance.sheet'].create(vals)
                    data = ''
                    attendance_sheet_id.get_attendance(data)
                    attendance_sheet_id.compute_attendance_data()
                url = f'{base_url}/web#model={model}&id={attendance_sheet_id.id}&view_type=form&action={action_id}'
                if attendance_sheet_id.email_sent == False:
                    attendance_sheet_list.append({
                        'employee': employee,
                        'manager': employee.parent_id,
                        'url': url,
                    })
                print('attendance_sheet_id ', attendance_sheet_id)
            sorted_attendance_sheet_list = sorted(attendance_sheet_list, key=lambda x: x['manager'])
            grouped_attendance_sheet_list = {}
            for manager, group in groupby(sorted_attendance_sheet_list, key=lambda x: x['manager']):
                grouped_attendance_sheet_list[manager] = list(group)
            for manager, values in grouped_attendance_sheet_list.items():
                if manager.work_email:
                    employee_list = [emp for emp in values]
                    html_employee_list = '<ul>'
                    for employee in employee_list:
                        print('employee ', employee)
                        html_employee_list += f'<li><a href="{employee["url"]}">{employee["employee"].name}</a></li>'
                    html_employee_list += '</ul>'
                    ctx = {
                        'manager': manager,
                        'employee_list': html_employee_list,
                        'company': manager.address_id,
                        'date_from': start_date,
                        'date_to': end_date,
                    }
                    print('ctx ', ctx)
                    self.env.ref('goexcel_attendance.attendance_sheet_generated_template').with_context(ctx).send_mail(res_id=self.id, force_send=True)
                    attendance_sheet_id.email_sent = True


class HrAttendanceSheetLine(models.Model):
    _inherit = 'hr.attendance.sheet.line'

    overtime_cost = fields.Float(compute='_compute_overtime_cost', string="Overtime Cost (RM)")

    @api.onchange('overtime')
    def _compute_overtime_cost(self):
        print('_compute_overtime_cost')
        for rec in self:
            employee_contract_id = rec.name_id.employee_id.contract_id
            print('employee_contract_id ', employee_contract_id)
            if employee_contract_id:
                if employee_contract_id.state in ['open', 'pending']:
                    overtime_id = self.env['hr.attendance.overtime'].search([('overtime_active','=',True)],limit=1)
                    overtime_rules = []
                    for line in overtime_id.overtime_line_ids:
                        vals = {
                            'hour_start': line.apply_after,
                            'rate': line.rate * employee_contract_id.rate_per_hour,
                        }
                        overtime_rules.append(vals)
                    sorted_overtime_rules = sorted(overtime_rules, key=lambda x: x['hour_start'])
                    if rec.overtime > 0:
                        print('overtime_rules ', sorted_overtime_rules)
                        print('rec.overtime ', rec.overtime)
                    rec.overtime_cost = calculate_overtime_pay(rec.overtime, sorted_overtime_rules)

    @api.multi
    def open_wizard(self):
        super(HrAttendanceSheetLine,self).open_wizard()
        """Method to open wizard."""
        vals = {'default_overtime': self.overtime,
                'default_latein': self.latein,
                'default_asignin': self.asignin,
                'default_asignout': self.asignout,
                'default_difftime': self.difftime,
                'default_reason': self.note
                }
        view_id = self.env.ref(
            'hr_attendances_overtime.change_attendance_data_wizard_view')
        return {
            'name': 'Change Attendance',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.change.attendance',
            'target': 'new',
            'context': vals,
        }
