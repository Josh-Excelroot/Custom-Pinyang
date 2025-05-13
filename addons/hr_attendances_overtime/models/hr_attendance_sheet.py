# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class Attendancesheet(models.Model):
    """Attendance Sheet."""

    _name = 'hr.attendance.sheet'
    _description = 'Attendance Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "employee_id"

    employee_id = fields.Many2one("hr.employee", string="Employee")
    date_from = fields.Date("Date from")
    date_to = fields.Date("Date to")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('approved', 'Approved')],
                             default="draft")
    request_date_from = fields.Date("request_date_from")
    request_date_to = fields.Date("request_date_to")
    attendance_policy = fields.Many2one(
        "hr.attendance.policies", string="Attendance Policies")
    attendance_sheet_ids = fields.One2many(
        "hr.attendance.sheet.line", "name_id", string="Attendance Line")
    no_latein = fields.Integer("No of Lates")
    total_latein = fields.Float("Total Late in")
    no_overtime = fields.Integer("No of Overtime")
    total_overtime = fields.Float("Total Overtime")
    no_difftime = fields.Integer("No of Diff Times")
    total_difftime = fields.Float("Total Diff Times Hours")
    no_absence = fields.Integer("No of Absence")
    total_absence = fields.Float("Total Absence Hours")

    latein = fields.Float(string='Late In', default='00')

    overtime = fields.Float(string='Overtime', default="00")

    time_different = fields.Float(string='Time Different', default="00")
    absent = fields.Float(string='Absence', default="00")

    @api.constrains('employee_id', 'request_date_from', 'request_date_to')
    def validation_attendance_sheet(self):
        """Method to set constrains for attendance sheet."""
        for sheet in self:
            attendance_ids = sheet.search([
                ('employee_id', '=', sheet.employee_id.id),
                ('request_date_from', '<=', sheet.request_date_from),
                ('request_date_to', '>=', sheet.request_date_from),
                ('id', '!=', sheet.id), ])
            if attendance_ids:
                raise ValidationError(
                    "Record already exists with same Value/Field %s !!!" % (sheet.employee_id.name))

    @api.multi
    def unlink(self):
        """Method to set validation for attendance sheet."""
        for sheet in self:
            if sheet.state == 'approved':
                raise ValidationError("You can't delete attendance sheet"
                                      " which is approved.")
        return super(Attendancesheet, self).unlink()

    @api.multi
    @api.constrains('request_date_from')
    def check_start_date(self):
        """Method to check start date."""
        for sheet in self:
            if sheet.request_date_from > sheet.request_date_to:
                raise ValidationError("Start date should be less "
                                      "than End date.")

    @api.multi
    def compute_attendance_data(self):
        """Compute Data."""
        dates = [self.request_date_from + timedelta(days=x) for x in range(
            (self.request_date_to - self.request_date_from).days + 1)]
        for rec in self:
            overtime = 00
            latein = 00
            rec._onchange_attendance_sheet_ids()
            contract_id = self.env['hr.contract'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'open')])
            policies_id = contract_id.attend_police_id or False
            if policies_id:
                # Calculated the letin amount if time different is not present.
                if rec.no_latein and policies_id.late_id and\
                        rec.total_latein:
                    latein_id = policies_id.late_id
                    weekday_ids = self.env['hr.attendance.sheet.line'].search([
                        ('name_id', '=', rec.id), ('status', '=', 'weekday')])
                    for weekday in weekday_ids:
                        if not weekday.difftime:
                            for line in latein_id.attendance_line_ids:
                                if weekday.latein >= line.time:
                                    if line.amount_type == "rate":
                                        latein = weekday.latein * line.rate
                                        break
                                    else:
                                        latein = rec.latein + line.amount
                                        break

                # Calculated the overtime
                if rec.no_overtime and rec.total_overtime and\
                        policies_id.overtime_id:
                    weekend_id = self.env['hr.attendance.sheet.line'].search([
                        ('name_id', '=', rec.id), ('status', '=', 'weekend')])
                    weekday_id = self.env['hr.attendance.sheet.line'].search([
                        ('name_id', '=', rec.id), ('status', '=', 'weekday')])
                    holiday_id = self.env['hr.attendance.sheet.line'].search([('name_id', '=', rec.id), ('status', '=', 'holiday')])
                    contract = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)])
                    for weekend in weekend_id:
                        for line in\
                                policies_id.overtime_id.overtime_line_ids:
                            if line.policie_type == 'week_end' and\
                                    weekend.overtime >= line.apply_after:
                                overtime = overtime + \
                                    (weekend.overtime * (line.rate * contract.rate_per_hour))
                                break
                    for weekday in weekday_id:
                        for line in\
                                policies_id.overtime_id.overtime_line_ids:
                            if line.policie_type == 'working_days' and\
                                    weekday.overtime >= line.apply_after:
                                overtime = overtime + \
                                    (weekday.overtime * (line.rate * contract.rate_per_hour))
                                break
                    for holiday in holiday_id:
                        ot_time = 0.0
                        for date in dates:
                            holiday_rate = self.env['hr.holiday.lines'].search([('holiday_date', '=', date)])
                            if holiday_rate:
                                overtime = overtime + \
                                    (holiday.overtime * (holiday_rate.rate * contract.rate_per_hour))
                                ot_time += overtime
                        if ot_time <= 0.0:
                            for line in\
                                    policies_id.overtime_id.overtime_line_ids:
                                if line.policie_type == 'holiday' and\
                                        holiday.overtime >= line.apply_after and line.rate > 0.0:
                                    overtime = overtime + \
                                        (holiday.overtime * (line.rate * contract.rate_per_hour))
                                    break
                rec.overtime = overtime
                rec.latein = latein
                # calculating the time Different
                if rec.no_difftime and policies_id.diff_rule_id and\
                        rec.total_difftime:
                    difftime = policies_id.diff_rule_id
                    for line in difftime.diff_line_ids:
                        if rec.total_difftime >= line.time:
                            rec.time_different = rec.total_difftime * line.rate
                            break

                if rec.no_absence and policies_id.absent_id:
                    absent = policies_id.absent_id
                    for line in absent.absence_line_ids:
                        if str(rec.no_absence) == line.time:
                            rec.absent = line.rate
                            break

    @api.multi
    def _get_planned_checkin(self, curr_date):
        cr = self._cr
        user = self.env.user
        check_in_dt = datetime.strptime(str(curr_date),
                                        DEFAULT_SERVER_DATE_FORMAT)
        local_tz = pytz.timezone(user.tz or 'UTC')
        ci_dt = check_in_dt.replace(tzinfo=pytz.utc
                                    ).astimezone(local_tz)
        hour_from = 0.0
        for rec in self:
            qry = '''select hour_from
                            from resource_calendar rc, \
                            resource_calendar_attendance rca
                            where rc.id = rca.calendar_id and
                            rc.id = %s and \
                            dayofweek=%s'''
            qry1 = qry + " and %s between date_from and date_to order by \
            hour_from limit 1"
            params1 = (rec.employee_id.resource_calendar_id.id,
                       str(ci_dt.weekday()),
                       curr_date)
            cr.execute(qry1, params1)
            res = cr.fetchone()
            # If specific dates are not given then fetch the records that do
            # not have dates
            if not res:
                qry2 = qry + " order by hour_from limit 1"
                params2 = (rec.employee_id.resource_calendar_id.id,
                           str(ci_dt.weekday()))
                cr.execute(qry2, params2)
                res = cr.fetchone()
            hour_from = res and res[0] or 0.0
        return hour_from

    @api.multi
    def _get_planned_checkout(self, curr_date):
        cr = self._cr
        user = self.env.user
        employee = self.employee_id

        check_in_dt = datetime.strptime(str(curr_date),
                                        DEFAULT_SERVER_DATE_FORMAT)
        local_tz = pytz.timezone(user.tz or 'UTC')
        co_dt = check_in_dt.replace(tzinfo=pytz.utc
                                    ).astimezone(local_tz)
        hour_to = 0.0
        for rec in self:
            qry = '''select hour_to,rca.id as rca_id
                        from resource_calendar rc, \
                        resource_calendar_attendance rca
                        where rc.id = rca.calendar_id and
                        rc.id = %s and \
                        dayofweek=%s'''
            qry1 = qry + "and %s between date_from and date_to order by \
               hour_to desc limit 1"
            params1 = (employee.resource_calendar_id.id,
                       str(co_dt.weekday()), curr_date)
            cr.execute(qry1, params1)
            res = cr.fetchone()
            # If specific dates are not given then fetch the records that do
            # not have dates
            if not res:
                qry2 = qry + " order by hour_to desc limit 1"
                params2 = (employee.resource_calendar_id.id,
                           str(co_dt.weekday()))
                cr.execute(qry2, params2)
                res = cr.fetchone()
            hour_to = res and res[0] or 0.0
        return hour_to

    @api.multi
    def _calc_current_attendance(self, attendances_ids, curr_date):
        """Method is used to calculate total attendance."""
        user = self.env.user
        local_tz = pytz.timezone(user.tz or 'UTC')
        curr_dt = curr_date
        vals = {}
        for atten in self:
            ttl_diff = 0.0
            converted_time = 0.0
            last_in = []
            last_out = []
            vals = {}
            lastin = 0.0
            lastout = 0.0
            for attends in attendances_ids:
                if attends.check_in:
                    ci_dt = attends.check_in.replace(tzinfo=pytz.utc
                                                     ).astimezone(local_tz)
                    ci_dt1 = ci_dt.date()
                    if curr_dt == ci_dt1:
                        last_in.append(ci_dt.time())
                        if attends.check_out:
                            co_dt = attends.check_out.replace(
                                tzinfo=pytz.utc).astimezone(local_tz)
                            co_dt1 = co_dt.date()
                            last_out.append(co_dt.time())
                            if curr_dt == co_dt1:
                                diff = co_dt - ci_dt
                                ttl_diff = diff.total_seconds() / 60.0 / 60.0
                                converted_time += ttl_diff
                        else:
                            diff = curr_dt - ci_dt.date()
                            ttl_diff = diff.total_seconds() / 60.0 / 60.0
                            converted_time += ttl_diff

            curr_ttl_attendance = converted_time
            last_in.sort()
            last_out.sort(reverse=True)
            for date in last_in:
                lastin = date.hour + (date.minute * 100 / 60) / 100.0
                break
            for date in last_out:
                lastout = date.hour + (date.minute * 100 / 60) / 100.0
                break

            vals.update({'total_attendance': curr_ttl_attendance,
                         'psignin': atten._get_planned_checkin(
                             curr_date) or False,
                         'psignout': atten._get_planned_checkout(
                             curr_date) or False,
                         'day': calendar.day_name[curr_dt.weekday() or False],
                         'asignin': lastin or False,
                         'asignout': lastout or False,
                         })
        return vals

    @api.multi
    def get_attendance(self, data):
        """Get Attendance History Of Employee."""
        attendance_ids = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '>=', self.request_date_from),
            ('check_in', '<=', self.request_date_to)])
        lst = []
        vals = {}
        dates = [self.request_date_from + timedelta(days=x) for x in range(
            (self.request_date_to - self.request_date_from).days + 1)]
        self.attendance_sheet_ids.unlink()

        for date in dates:
            vals = {}
            if date not in lst:
                lst.append(date)
                vals = self._calc_current_attendance(attendance_ids, date)
                vals.update({'name_id': self.id, 'date': date})
                vals.update({'status': 'weekday'})

                if vals['psignin'] == 0.0 and vals['psignout'] == 0.0:
                    vals.update({'status': 'weekend'})

                if vals['psignin'] and vals['psignout']:
                    if vals['asignin'] == 0.0 and vals['asignout'] == 0.0:

                        leave = self.env['hr.leave'].search(
                            [('employee_id', '=', self.employee_id.id),
                             ('state', '=', 'validate'),
                             ('request_date_from', '<=', date),
                             ('request_date_to', '>=', date)
                             ])
                        if leave:
                            vals.update({'status': 'leave'})
                        if not leave:
                            vals.update({'status': 'absence'})
                holiday = self.env['hr.holiday.lines'].search(
                            [('holiday_date', '=', date)])
                if holiday:
                    vals.update({'status': 'holiday'})
                if vals['status'] == 'holiday':
                    vals.update({'psignin': 0.0, 'psignout': 0.0})
                if vals['asignin'] > vals['psignin'] and\
                        vals['status'] == 'weekday':
                    late = vals['asignin'] - vals['psignin']
                    vals.update({'latein': late})

                avg_hours = self.employee_id and \
                    self.employee_id.resource_calendar_id and \
                    self.employee_id.resource_calendar_id.hours_per_day or\
                    False

                resource_calendar_id = self.employee_id and\
                    self.employee_id.resource_calendar_id

                for line in resource_calendar_id.attendance_ids:
                    if line.date_from == date or line.date_to == date:
                        avg_hours = line.hour_to - line.hour_from

                if vals['total_attendance'] > avg_hours:
                    vals.update({'overtime':
                                 vals['total_attendance'] - avg_hours or False}
                                )

                if vals['status'] == 'weekend' or vals['status'] == 'holiday' and vals['total_attendance']:
                    vals.update(
                        {'overtime': vals['total_attendance'] or False})

                if vals['total_attendance'] < avg_hours and\
                        vals['psignin'] > 0.0 and vals['psignout'] > 0.0:
                    if vals.get('status') == 'weekday':
                        vals.update({'difftime': avg_hours -
                                     vals['total_attendance'] or False})
                    if vals.get('status') == 'holiday':
                        vals.update({'difftime': avg_hours - vals['total_attendance'] or False})
                flage = True
                if vals['status'] == 'weekend' and\
                        vals.get('overtime', False) <= 0.0:
                    continue
                if vals['status'] == 'absence':
                    for line in resource_calendar_id.attendance_ids:

                        if int(date.weekday()) == int(line.dayofweek) and\
                                line.date_from and line.date_to:
                            if not line.date_to == date or\
                                    line.date_from == date:
                                vals = {}

                if flage and vals:
                    self.env['hr.attendance.sheet.line'].create(vals)
        self.employee_id.attendance_sheet_id = self.id or False

    @api.multi
    def name_get(self):
        """Name Get."""
        result = []
        for record in self:
            user_lang = self.env.user.lang
            lang = self.env['res.lang'].search(
                    [('code', '=', user_lang)])
            cust_name = ''
            if lang:
                cust_name = 'Attendance Sheet of ' + str(record.employee_id.name) \
                    + ' From ' + record.request_date_from.strftime(lang.date_format) +\
                    ' To ' + record.request_date_to.strftime(lang.date_format)
            result.append((record.id, cust_name))
        return result

    @api.multi
    def execute_send_to_manager(self):
        """State Confirm."""
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def execute_set_to_draft(self):
        """State to draft."""
        self.write({'state': 'draft'})
        return True

    @api.multi
    def execute_set_to_approve(self):
        """State To Approved."""
        self.write({'state': 'approved'})
        return True

# calculate the attendance data

    @api.onchange('attendance_sheet_ids')
    def _onchange_attendance_sheet_ids(self):
        no_ot = 0
        no_dt = 0
        no_lt = 0
        total_ot = 0.0
        total_lt = 0.0
        total_dt = 0.0
        total_abs = 0.0
        for lines in self.attendance_sheet_ids:
            if lines.overtime != 0.0:
                no_ot += 1
                total_ot += lines.overtime
            if lines.difftime != 0.0:
                no_dt += 1
                total_dt += lines.difftime
            if lines.latein != 0.0:
                no_lt += 1
                total_lt += lines.latein
            if lines.status == 'absence':
                total_abs += 1
        self.no_latein = no_lt
        self.total_latein = total_lt
        self.no_overtime = no_ot
        self.total_overtime = total_ot
        self.no_difftime = no_dt
        self.total_difftime = total_dt
        self.no_absence = total_abs
        self.total_absence = total_abs * \
            self.employee_id.resource_calendar_id.hours_per_day or False


class Attendancesheetline(models.Model):
    """Attendance Sheet Line."""

    _name = 'hr.attendance.sheet.line'
    _description = "Attendance Sheet Line"

    date = fields.Date("Date")
    day = fields.Char("Day")
    psignin = fields.Float("Planned Signin")
    psignout = fields.Float("Planned Signout")
    asignin = fields.Float("Actual Signin")
    asignout = fields.Float("Actual Signout")
    latein = fields.Float("Late in")
    overtime = fields.Float("Overtime")
    difftime = fields.Float("Diff Time")
    status = fields.Selection(
        [('weekend', 'Weekend'),
         ('absence', 'Absent'),
         ('leave', 'Leave'),
         ('holiday', 'Public Holiday'),
         ('weekday', 'WeekDay')], default='weekday')
    note = fields.Text("Note")
    name_id = fields.Many2one("hr.attendance.sheet", string="name")
    d_asignin = fields.Datetime("actual sign in for date")
    d_asignout = fields.Datetime("actual signout for time")
    total_attendance = fields.Float(string="Total Attendance")

    @api.multi
    def open_wizard(self):
        """Method to open wizard."""
        vals = {'default_overtime': self.overtime,
                'default_latein': self.latein,
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
