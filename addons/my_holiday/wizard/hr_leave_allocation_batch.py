# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models
from datetime import datetime, timedelta, time


class HrLeaveAllocationBatch(models.TransientModel):

    _name = 'hr.leave.allocation.batch'
    _description = "Leave Allocation By Batch"

    # holiday_status_id = fields.Many2one("hr.leave.type", string="Leave Type")
    leave_entitlement_id = fields.Many2one('leave.entitlement',string="Leave Entitlement")
    job_position_id = fields.Many2one('hr.job',string="Job Position")
    # employee_ids = fields.One2many("leave.allocation.employee.batch")
    # employee_ids = fields.Many2many(
    #     'hr.employee', 'batch_hr_employee_rel', 'emp_id', 'employee_id', 'Employee', required=False)
    employee_ids_entry = fields.Many2many('hr.employee')

    @api.multi
    def create_leaves(self):
        # print("SAJJAD")
        if self.leave_entitlement_id and self.job_position_id:
            for employee in self.employee_ids_entry:
                print(employee.name)
                description = employee.name+' '+self.leave_entitlement_id.leave_type_id.name
                existing_record = self.env['hr.leave.allocation'].sudo().search([('employee_id','=',employee.id),
                                                                                 ('holiday_status_id','=',self.leave_entitlement_id.leave_type_id.id)])

                if existing_record:
                    existing_record = existing_record[-1]
                    record = self.env['hr.leave.allocation'].sudo().create({
                        'name': description,
                        'accrual': True,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'mode_company_id': employee.company_id.id,
                        'department_id': employee.department_id.id,
                        'holiday_status_id': self.leave_entitlement_id.leave_type_id.id,
                        'number_of_days': existing_record.number_of_days + self.leave_entitlement_id.additional_leave_entitlement_per_year,
                        # 'max_transfer_annual_leaves': self.leave_entitlement_id.max_transfer_annual_leave,
                    })
                    print(record.max_transfer_annual_leaves)
                    # # self.unit_per_interval, self.interval_unit = 'days', 'years'
                    hr_year_last_date = record.hr_year_id.date_stop
                    date_to = datetime.combine(hr_year_last_date, time(18, 59, 59))
                    last_day_next_year = hr_year_last_date.replace(year=hr_year_last_date.year + 1, month=12, day=31)
                    print(last_day_next_year)
                    hr_year_id = self.env['hr.year'].sudo().search([('name','=',last_day_next_year.year)])
                    record.write({
                        'max_transfer_annual_leaves': self.leave_entitlement_id.max_transfer_annual_leave,
                        'unit_per_interval': 'days',
                        'interval_unit': 'years',
                        'duration_readonly': True,
                        'hr_year_id': hr_year_id.id,
                        'date_to': last_day_next_year
                    })
                else:
                    record = self.env['hr.leave.allocation'].sudo().create({
                        'name': description,
                        'accrual': True,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'mode_company_id': employee.company_id.id,
                        'department_id': employee.department_id.id,
                        'holiday_status_id': self.leave_entitlement_id.leave_type_id.id,
                        'number_of_days': self.leave_entitlement_id.minimum_annual_leave_entitlement,
                        # 'max_transfer_annual_leaves': self.leave_entitlement_id.max_transfer_annual_leave,
                    })
                    print(record.max_transfer_annual_leaves)
                    # self.unit_per_interval, self.interval_unit = 'days', 'years'
                    hr_year_last_date = record.hr_year_id.date_stop
                    date_to = datetime.combine(hr_year_last_date, time(18, 59, 59))
                    record.write({
                        'max_transfer_annual_leaves': self.leave_entitlement_id.max_transfer_annual_leave,
                        'unit_per_interval': 'days',
                        'interval_unit': 'years',
                        'duration_readonly': True,
                        'date_to': date_to
                    })

# class HrLeaveAllocationBatch(models.Model):
#
#     _name = 'hr.leave.allocation.batch'
#     _description = "Leave Allocation By Batch"
