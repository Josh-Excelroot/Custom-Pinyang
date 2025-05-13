# See LICENSE file for full copyright and licensing details

import time as times
from datetime import datetime, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrLeaveAllocation(models.Model):

    _inherit = "hr.leave.allocation"

    @api.model
    def fetch_hryear(self, date=False):
        '''
        The method used to fetch HR year value.
        @param self : Object Pointer
        @return : id of HR year
        ------------------------------------------------------
        '''
        if not date:
            date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if isinstance(date, str):
            date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        hr_year_obj = self.env['hr.year']
        args = [('date_start', '<=', date), ('date_stop', '>=', date)]
        hr_year_brw = hr_year_obj.search(args)
        if hr_year_brw and hr_year_brw.ids:
            hr_year_ids = hr_year_brw
        else:
            year = date.year
            end_date = str(year) + '-12-31'
            start_date = str(year) + '-01-01'
            hr_year_ids = hr_year_obj.create({
                'date_start': start_date,
                'date_stop': end_date,
                'code': str(year),
                'name': str(year)
            })
        return hr_year_ids.ids[0]

    @api.constrains('number_of_days')
    def _check_numberof_days(self):
        for rec in self:
            if rec.number_of_days == 0:
                raise ValidationError(
                    _('You can not create allocation request for 0 days!'))

    @api.multi
    def _notify_get_groups(self, message, groups):
        return []

    @api.onchange('employee_id')
    def _onchange_employee(self):
        super(HrLeaveAllocation, self)._onchange_employee()
        self.holiday_status_id = False
        self.number_of_days = 0
        if self.holiday_type == 'employee':
            self.department_id = self.employee_id.department_id

    @api.model
    def _get_hr_year(self):
        '''
        The method used to get HR year value.
        @param self : Object Pointer
        @return : id of HR year
        ------------------------------------------------------
        '''
        print(DEFAULT_SERVER_DATE_FORMAT)
        today = times.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return self.fetch_hryear(today)

    hr_year_id = fields.Many2one('hr.year', 'HR Year', default=_get_hr_year)
    carry_forward = fields.Boolean('Carry Forward Leave')
    expiry_date = fields.Date('Expiry Date')
    accrual_transferred = fields.Boolean('At the end of the calendar year, unused accruals will be transferred to next year')
    remaining_leaves_from_past_year = fields.Float("Remaining Leaves from Past Year", readonly=True)
    expiry_done = fields.Boolean("Expiry Date Done", default=False)
    remaining_leaves_for_payslip = fields.Float("Remaining Leaves for Paid Leave Payslip")
    max_transfer_annual_leave = fields.Float(related='employee_id.leave_entitlement.max_transfer_annual_leave',string='Max Transferred Leave',default=0.0,requried=True)
    duration_readonly = fields.Boolean('Duration Readonly',default=False)
    # xml - to add  old leaves to new employees(schedule action), xml- expiry daet if is today then remove added leaves

    @api.onchange('accrual','holiday_status_id','employee_id')
    def _compute_get_duration_readonly(self):
        if self.accrual and self.holiday_status_id and self.employee_id:
            leave_entitlement = self.employee_id.leave_entitlement
            if leave_entitlement:
                self.number_per_interval = leave_entitlement.additional_leave_entitlement_per_year
                self.number_of_days = leave_entitlement.minimum_annual_leave_entitlement
                self.duration_readonly = True
            else:
                self.duration_readonly = False
        else:
            self.duration_readonly = False

    @api.onchange('accrual','hr_year_id')
    def onchange_accrual_date_to(self):
        if self.accrual and self.hr_year_id.date_stop:
            self.unit_per_interval,self.interval_unit = 'days','years'
            hr_year_last_date = self.hr_year_id.date_stop
            self.date_to = datetime.combine(hr_year_last_date, time(18, 59, 59))
            user_tz = self.env.user.tz or 'UTC'
            localized_dt = timezone('UTC').localize(datetime.combine(hr_year_last_date, time(23, 59, 59))).astimezone(timezone(user_tz))
            year_id_name = int(self.hr_year_id.name) + 1
            first_day_of_year = datetime(year_id_name, 1, 1).date()
            self.expiry_date = first_day_of_year
            # print(localized_dt)

    @api.model
    def _update_accrual(self):
        today = fields.Date.from_string(fields.Date.today())
        holidays = self.search([('accrual', '=', True), ('employee_id.active', '=', True), ('state', '=', 'validate'),
                                ('holiday_type', '=', 'employee'),
                                '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
                                '|', ('nextcall', '=', False), ('nextcall', '<=', today)])
        for holiday in holidays:
            holiday.remaining_leaves_from_past_year = 0
            if holiday.accrual_transferred and holiday.expiry_date:
                record = self.env['hr.leave.report'].search([('employee_id', '=', holiday.employee_id.id),
                                                        ('holiday_status_id', '=', holiday.holiday_status_id.id)])
                sum_of_remaining_leaves = sum(record.mapped('number_of_days'))
                # print(holiday.employee_id.remaining_leaves)
                if sum_of_remaining_leaves > holiday.max_transfer_annual_leave:
                    holiday.remaining_leaves_from_past_year = holiday.max_transfer_annual_leave
                else:
                    holiday.remaining_leaves_from_past_year += sum_of_remaining_leaves
                print("remaining super",holiday.remaining_leaves_from_past_year)
        res = super(HrLeaveAllocation, self)._update_accrual()
        return res

    def reset_remaining_days_in_hr_leave(self):
        holidays = self.env['hr.leave.allocation'].sudo().search([('accrual', '=', True), ('employee_id.active', '=', True), ('state', '=', 'validate'),
                                ('holiday_type', '=', 'employee')])
        print(holidays)
        for holiday in holidays:
            if not holiday.remaining_leaves_from_past_year and not holiday.expiry_done: ## add demo field to tell that expiry date function run so not to again add here
                record = self.env['hr.leave.report'].search([('employee_id', '=', holiday.employee_id.id),
                                                             ('holiday_status_id', '=', holiday.holiday_status_id.id)])
                sum_of_remaining_leaves = sum(record.mapped('number_of_days'))
                print(sum_of_remaining_leaves)
                if holiday.number_of_days <= sum_of_remaining_leaves:
                        holiday.remaining_leaves_from_past_year = sum_of_remaining_leaves


    @api.model
    def create(self,values):
        if not values.get('expiry_date', False) and not values.get('accrual_transferred', False) and not values.get('hr_year', False):
            values['expiry_date'] = self.expiry_date
            values['accrual_transferred'] = self.accrual_transferred
            values['hr_year'] = self.hr_year_id.id
            values['max_transfer_annual_leave'] = self.max_transfer_annual_leave
        res = super(HrLeaveAllocation,self).create(values)
        return res

    def expiry_date_reset(self):
        holidays = self.env['hr.leave.allocation'].sudo().search(
            [('accrual', '=', True), ('employee_id.active', '=', True), ('state', '=', 'validate'),
             ('holiday_type', '=', 'employee')])
        print(holidays)
        for holiday in holidays:
            if holiday.expiry_date == datetime.now().today() or not holiday.expiry_done:
                days_to_add = holiday.remaining_leaves_from_past_year
                if days_to_add:
                    date_find = ''
                    check_start_date = holiday.expiry_date
                    while not date_find:
                        record_of_hr_leave = self.env['hr.leave'].sudo().search([('request_date_from','=',check_start_date)])
                        print(record_of_hr_leave)
                        if not record_of_hr_leave:
                            date_find = check_start_date
                        else:
                            check_start_date = check_start_date + timedelta(1)
                    start_date = date_find
                    end_date = start_date + timedelta(days=days_to_add)
                    record = self.env['hr.leave'].sudo().create(
                        {
                            'holiday_status_id':holiday.holiday_status_id.id,
                            'employee_id':holiday.employee_id.id,
                            'request_date_from':start_date,
                            'request_date_to':end_date,
                            'number_of_days': days_to_add,
                            'name':'Carry on Leave Washed Out Due to Expiry Date',
                         }
                    )
                    print(record.id)
                    record.action_approve()
                    holiday.remaining_leaves_for_payslip += days_to_add
                    holiday.remaining_leaves_from_past_year = 0
                    holiday.expiry_done = True
