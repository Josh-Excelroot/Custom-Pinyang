# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHolidaysStatus(models.Model):

    _inherit = "hr.leave.type"

    code = fields.Char('Code', size=64)
    weekend_calculation = fields.Boolean('Weekend Calculation')
    count_days_by = fields.Selection([
        ('calendar_day', 'Calendar Days'),
        ('working_days_only', 'Working Days only')],
        string="Count Days By",
        help="If Calendar Days : system will counts all calendar days in"
             "leave request. \nIf Working Days only : system will counts all"
             "days except public and weekly holidays in leave request. ",
        default='calendar_day')
    company_ids = fields.Many2many('res.company', string="Companies")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Leave code must be unique !'),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        leave_brw = self.search([('code', operator, name)] + args,
                                limit=limit)
        return leave_brw.name_get()

    @api.multi
    def get_days(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        result = dict((id, dict(max_leaves=0, leaves_taken=0,
                                remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

        leave_domain = [
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ]
        hr_year_id = self.env['hr.leave'].fetch_hryear()
        if hr_year_id:
            leave_domain += [('hr_year_id', '=', hr_year_id)]

        requests = self.env['hr.leave'].search(leave_domain)
        allocations = self.env['hr.leave.allocation'].search(leave_domain)

        for request in requests:
            status_dict = result[request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                        if request.leave_type_request_unit == 'hour'
                                                        else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                            if allocation.type_request_unit == 'hour'
                                                            else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                              if allocation.type_request_unit == 'hour'
                                              else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                    if allocation.type_request_unit == 'hour'
                                                    else allocation.number_of_days)

        return result

    @api.multi
    def unlink(self):
        leave_type_list = []
        sick_leave = self.env.ref('hr_holidays.holiday_status_sl')
        leave_type_list += [sick_leave.id]
        anuual_leave = self.env.ref('hr_holidays.holiday_status_cl')
        leave_type_list += [anuual_leave.id]
        compassionate_leave = self.env.ref('hr_holidays.holiday_status_comp')
        leave_type_list += [compassionate_leave.id]
        Unpaid_leave = self.env.ref('hr_holidays.holiday_status_unpaid')
        leave_type_list += [Unpaid_leave.id]
        maternity_leave = self.env.ref('my_holiday.holiday_status_maternity')
        leave_type_list += [maternity_leave.id]
        marriage_leave = self.env.ref('my_holiday.holiday_status_marriage')
        leave_type_list += [marriage_leave.id]
        paternity_leave = self.env.ref('my_holiday.holiday_status_paternity')
        leave_type_list += [paternity_leave.id]
        study_leave = self.env.ref('my_holiday.holiday_status_study')
        leave_type_list += [study_leave.id]
        hospital_leave = self.env.ref('my_holiday.holiday_status_hospital')
        leave_type_list += [hospital_leave.id]
        child_mrg_leave = self.env.ref('my_holiday.holiday_status_child_mrg')
        leave_type_list += [child_mrg_leave.id]
        for rec in self:
            if rec.id in leave_type_list:
                raise ValidationError(
                      'You Can not delete this Leave Type!!!')
        return super(HrHolidaysStatus, self).unlink()
