# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime, time as d_time
from dateutil import rrule
from pytz import timezone, UTC
from werkzeug import url_encode

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.tools import float_compare
#DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period')

HOURS_PER_DAY = 8
class LeaveRequest(models.Model):
    _inherit = "hr.leave"

    @api.one
    @api.depends('employee_id')
    def _user_view_validate(self):
        uid = self.env.uid
        res_user = self.env['res.users']
        for holiday in self:
            if uid != SUPERUSER_ID and \
                (res_user.has_group('base.group_user') or
                 res_user.has_group('hr.group_hr_user')) and not \
                    (res_user.has_group('hr.group_hr_manager')):
                if holiday.employee_id.user_id.id == uid:
                    self.user_view = True
                else:
                    self.user_view = False
            else:
                self.user_view = False

    @api.model
    def _get_hr_year(self):
        '''
        The method used to get HR year value.
        @param self : Object Pointer
        @return : id of HR year
        ------------------------------------------------------
        '''
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return self.fetch_hryear(today)

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

    folder_id = fields.Char()
    rejection = fields.Text('Reason')
    notes = fields.Text('Reasons', readonly=False,
                        states={'validate': [('readonly', True)]})
    employee_document_ids = fields.One2many('employee.document',
                                            'employee_doc_id', 'Documents')
    create_date = fields.Datetime('Create Date', readonly=True)
    write_date = fields.Datetime('Write Date', readonly=True)
    leave_type = fields.Selection([('am', 'AM'), ('pm', 'PM'),
                                   ('full', 'FULL')], 'Duration')
    state = fields.Selection([('draft', 'New'),
                              ('confirm', 'Waiting Pre-Approval'),
                              ('refuse', 'Refused'),
                              ('validate1', 'Waiting Final Approval'),
                              ('validate', 'Approved'),
                              ('cancel', 'Cancelled')],
                             'State', readonly=True, help='The state is set to \'Draft\', when a \
        holiday request is created.\nThe state is \'Waiting Approval\',\
        when holiday request is confirmed by user.\nThe state is \'Refused\',\
        when holiday request is refused by manager.\nThe state is \
        \'Approved\',when holiday request is approved by manager.')
    carry_forward = fields.Boolean('Carry Forward Leave')
    user_view = fields.Boolean(compute='_user_view_validate',
                               string="validate")
    hr_year_id = fields.Many2one('hr.year', 'HR Year', default=_get_hr_year)
    date_from = fields.Datetime(
        'Start Date', readonly=True, index=True, copy=False, required=True,
        default=datetime.now().replace(hour=00, minute=00, second=1),
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=True,
        default=datetime.now().replace(hour=23, minute=59, second=59),
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    added_to_payslip = fields.Boolean('Added to Payslip',default=False)
    # kashif 1 sept 23: override and add code to send email to leave notifiers

    def activity_update(self):
        to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
        for holiday in self:
            start = UTC.localize(holiday.date_from).astimezone(timezone(holiday.employee_id.tz or 'UTC'))
            end = UTC.localize(holiday.date_to).astimezone(timezone(holiday.employee_id.tz or 'UTC'))
            note = _('New %s Request created by %s from %s to %s') % (holiday.holiday_status_id.name, holiday.create_uid.name, start, end)
            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state == 'confirm':
                holiday.send_email(holiday,"my_holiday.email_template_leave_request")
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate1':
                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            # holiday.send_email(holiday,'my_holiday.email_template_leave_approvals')
            to_do.activity_feedback(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])

    def _validate_leave_request(self):
        """ Validate leave requests (holiday_type='employee')
        by creating a calendar event and a resource leaves. """
        holidays = self.filtered(lambda request: request.holiday_type == 'employee')
        holidays._create_resource_leave()
        for holiday in holidays:
            meeting_values = holiday._prepare_holidays_meeting_values()
            meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True).create(meeting_values)
            self.send_email(self,'my_holiday.email_template_leave_approval')
            holiday.write({'meeting_id': meeting.id})

    def send_email(self, res, template):
        template = self.env.ref(template)
        template.send_mail(res.id, force_send=True)

    def get_email_ids_of_leave_approval(self):
        user = self.env.user.company_id.approve_leave_recipients

        notification_recipent = user

        # email = 'moosahussain784@gmail.com'
        # print(email)
        if len(notification_recipent) == 1:
            email = str([notification_recipent.email]).replace("[", "").replace("]", "")
        else:
            comma_separated_email = []
            for recipients in notification_recipent:
                comma_separated_email.append(recipients.email)

            email = ",".join(comma_separated_email)
        return email.replace("'", "")

    def get_email_ids_of_leave_request(self):
        user = self.env.user.company_id.request_leave_recipients
        notification_recipent = user
        if len(notification_recipent) == 1:
            email = str([notification_recipent.email]).replace("[", "").replace("]", "")
        else:
            comma_separated_email = []
            for recipients in notification_recipent:
                comma_separated_email.append(recipients.email)

            email = ",".join(comma_separated_email)
        return email.replace("'", "")

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        #kashif 4sept23: fix bug used sudo
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url_params = {
            'id': self.id,
            'view_type': 'form',
            'model': 'hr.leave',
            # 'menu_id': self.env.ref('module_name.menu_record_id').id,
            'action': self.env.ref('hr_holidays.hr_leave_action_all').id,
        }
        params = '/web?#%s' % url_encode(url_params)
        return base_url + params

#end





    # ============================================
#    constrains Methods
# ============================================

    @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    def _check_public_holiday_leave(self):
        for rec in self:
            if rec.holiday_status_id and \
                    rec.holiday_status_id.count_days_by and\
                    rec.holiday_status_id.count_days_by == 'calendar_day':
                diff_day = rec._check_holiday_to_from_dates(
                    rec.request_date_from, rec.request_date_to)
                if diff_day == 0:
                    raise ValidationError(_(
                        'You are not able to apply leave request on Holiday.!'))

    @api.constrains('request_date_from', 'request_date_to', 'hr_year_id')
    def _check_current_year_leave_req(self):
        '''
        The method is used to validate only Selected HR year leave request.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        #### this function is commented out because it doesn't allow the program to create holidays for next year / Lo Gee Yen / 12/10/2023
        for rec in self:
            # if rec.holiday_status_id.id and rec.hr_year_id:
            #     if rec.hr_year_id.date_start and rec.hr_year_id.date_stop:
            #         if rec.hr_year_id.date_start <= rec.request_date_from and \
            #                 rec.hr_year_id.date_stop >= rec.request_date_to:
                        continue
                    # else:
                    #     raise ValidationError(
                    #         _('Start date and End date must be related to selected HR year!'))
        #### this function is commented out because it doesn't allow the program to create holidays for next year / Lo Gee Yen / 12/10/2023

    @api.constrains('number_of_days')
    def _check_numberof_days(self):
        for rec in self:
            if rec.number_of_days == 0:
                raise ValidationError(
                    _('You can not request leave for 0 days!'))

# ============================================
#    On change Methods
# ============================================

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        """
            This method is overridden due to one purpose is that
            when changing holidays_status_id then based on holiday type
            recalculate the number of days.
        """
        self._onchange_leave_dates()
        return super(LeaveRequest, self)._onchange_holiday_status_id()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        """
        The method purpose is to check the date_from and date_to and also
        recalculate number_od_days based on Holiday Type.
        """
        result = {'value': {}}
        if self.date_from and self.date_to:
            if self.date_from.date() > self.date_to.date():
                result['value']['request_date_from'] = self.request_date_from
                result['value']['request_date_to'] = self.request_date_to
                warning = {
                    'title': 'Warning',
                    'message': _('Warning!\nThe start date must be anterior to\
                 the end date.')
                }
                result.update({'warning': warning})
                return result
            if self.holiday_status_id and\
                    self.holiday_status_id.count_days_by == 'calendar_day':
                diff_day = self.with_context({
                    'working_days': True})._get_number_of_days(
                        self.date_from, self.date_to, self.employee_id.id)
                self.number_of_days = diff_day
            else:
                self.number_of_days = self._get_number_of_days(
                    self.date_from, self.date_to, self.employee_id.id)
        else:
            self.number_of_days = 0

# ============================================
#    Other Methods
# ============================================
    @api.multi
    def get_date_from_range(self, from_date, to_date):
        '''
            Returns list of dates from from_date to to_date
            @self : Current Record Set
            @api.multi : The decorator of multi
            @param from_date: Starting date for range
            @param to_date: Ending date for range
            @return : Returns list of dates from from_date to to_date
            -----------------------------------------------------------
        '''
        dates = []
        if from_date and to_date:
            dates = list(rrule.rrule(
                rrule.DAILY, dtstart=from_date, until=to_date))
        return dates

    @api.multi
    def _check_holiday_to_from_dates(self, start_date, end_date):
        '''
        Checks that there is a public holiday,Saturday and Sunday
        on date of leave
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : The current object of id
        @param from_date: Starting date for range
        @param to_date: Ending date for range
        @return : Returns the numbers of days
        -----------------------------------------------------------
        '''
        public_holiday_dates = [line.holiday_date for line in
                                self.env['hr.holiday.lines'].search([
                                    ('holiday_date', '>=', start_date),
                                    ('holiday_date', '<=', end_date),
                                    ('holiday_id.state', '=', 'validated')])]
        dates = self.get_date_from_range(start_date, end_date)
        dates = [date for date in dates if date.date()
                 not in public_holiday_dates]
        no_of_day = len(dates)
        return no_of_day

#     def _get_number_of_days(self, date_from, date_to, employee_id):
#         """
#             Returns a float equals to the timedelta between two dates
#             given as string.
#         """
#         if self._context.get('working_days'):
#             leave_day = self._check_holiday_to_from_dates(date_from, date_to)
#             return leave_day
#         return super(LeaveRequest, self)._get_number_of_days(
#             date_from, date_to, employee_id)

    @api.multi
    def action_refuse(self):
        context = dict(self._context)
        result = {}
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse\
            leave requests.'))
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1']:
                raise UserError(_('Leave request must be confirmed or \
                validated in order to refuse it.'))
            context.update({'active_id': holiday.id})
            result = {
                'name': _('Refuse Leave'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'refuse.leave',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context,
            }
        return result

    @api.model
    def create(self, vals):
        ret = super(LeaveRequest, self).create(vals)
        if 'employee_id' in vals and 'holiday_status_id' in vals:
            record = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', vals['employee_id']), ('holiday_status_id', '=', vals['holiday_status_id'])])
            record = record.filtered(lambda x: x.remaining_leaves_from_past_year)
            if record.remaining_leaves_from_past_year:
                if record.remaining_leaves_from_past_year >= vals['number_of_days']:
                    record.remaining_leaves_from_past_year -= vals['number_of_days']
                else:
                    record.remaining_leaves_from_past_year = 0
        return ret

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        #print('>>>>>>>>>>>>>>> _check_holiday holiday_type')
        for holiday in self:
            #print('>>>>>>>>>>>>>>> _check_holiday holiday_type=', holiday.holiday_type, ', state=',holiday.state)
            if holiday.holiday_type == 'company':
                #print('>>>>>>>>>>>>>>> _check_holiday holiday_type 2=', holiday.holiday_type)
                break
            elif holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
                continue
            leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
            #print('>>>>>>>>>>>>>>> _check_holiday remaining leave=', leave_days['remaining_leaves'])
            if holiday.holiday_type == 'employee' and holiday.state != 'validate':
                if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                        float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                            'Please also check the leaves waiting for validation.'))



    # @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
    #               'request_date_from', 'request_date_to',
    #               'employee_id')
    # def _onchange_request_parameters(self):
    #     if not self.request_date_from:
    #         self.date_from = False
    #         return
    #
    #     if self.request_unit_half or self.request_unit_hours:
    #         self.request_date_to = self.request_date_from
    #
    #     if not self.request_date_to:
    #         self.date_to = False
    #         return
    #
    #     domain = [('calendar_id', '=', self.employee_id.resource_calendar_id.id or self.env.user.company_id.resource_calendar_id.id)]
    #     attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'dayofweek', 'day_period'], ['dayofweek', 'day_period'], lazy=False)
    #
    #     # Must be sorted by dayofweek ASC and day_period DESC
    #     attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))
    #
    #     default_value = DummyAttendance(0, 0, 0, 'morning')
    #
    #     # find first attendance coming after first_day
    #     attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()), attendances[0] if attendances else default_value)
    #     # find last attendance coming before last_day
    #     attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()), attendances[-1] if attendances else default_value)
    #
    #     if self.request_unit_half:
    #         if self.request_date_from_period == 'am':
    #             hour_from = float_to_time(attendance_from.hour_from)
    #             hour_to = float_to_time(attendance_from.hour_to)
    #         else:
    #             hour_from = float_to_time(attendance_to.hour_from)
    #             hour_to = float_to_time(attendance_to.hour_to)
    #     elif self.request_unit_hours:
    #         # This hack is related to the definition of the field, basically we convert
    #         # the negative integer into .5 floats
    #         hour_from = float_to_time(abs(self.request_hour_from) - 0.5 if self.request_hour_from < 0 else self.request_hour_from)
    #         hour_to = float_to_time(abs(self.request_hour_to) - 0.5 if self.request_hour_to < 0 else self.request_hour_to)
    #     elif self.request_unit_custom:
    #         hour_from = self.date_from.time()
    #         hour_to = self.date_to.time()
    #     else:
    #         hour_from = float_to_time(attendance_from.hour_from)
    #         hour_to = float_to_time(attendance_to.hour_to)
    #
    #     tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC
    #     self.date_from = timezone(tz).localize(datetime.combine(self.request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
    #     self.date_to = timezone(tz).localize(datetime.combine(self.request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)
    #     self._onchange_leave_dates()

    # Sajjad - 20/01/24 - Fix for Civon Public Holiday Issue
    @api.model
    def create(self, data):
        res = super(LeaveRequest, self).create(data)
        ph = self.env['hr.leave.type'].search([
            ('name', '=', 'Public Holiday'),
        ], limit=1)  ## 18 for public holdiday
        if res['holiday_status_id'].id == ph.id and res['employee_id'] and res['user_id']:
            res['employee_id'] = ''
            res['user_id'] = ''
        return res
    # end


class ResUsers(models.Model):

    _inherit = 'res.users'

# ============================================
#    Users: ORM Methods
# ============================================

    @api.model
    def create(self, data):
        context = dict(self._context) or {}
        context['noshortcut'] = True
        user_id = super(ResUsers, self).create(data)
        user_id.check_user_access()
        return user_id

    @api.multi
    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        self.check_user_access()
        return result

    @api.multi
    def check_user_access(self):
        mod_obj = self.env['ir.model.data']
        group_result = mod_obj.get_object('base', 'group_erp_manager')
        new_user_add = [user.id for user in group_result.users]
        group_result = mod_obj.get_object('base', 'group_system')
        system_user_add = [user.id for user in group_result.users]
        # for user in self:
        #     if self._uid in [1, 2]:
        #         continue
        #     if user.id in new_user_add or user.id in system_user_add:
        #         raise ValidationError(_('You cannot give administrator \
        #         access rights !'))
        return True
