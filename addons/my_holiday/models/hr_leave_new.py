# See LICENSE file for full copyright and licensing details

import math
import time
import pytz
from datetime import datetime
from dateutil import parser, rrule
from datetime import date, timedelta

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, \
    DEFAULT_SERVER_DATETIME_FORMAT, ustr


class HrHolidays(models.Model):

    _inherit = "hr.leave"

    @api.depends('employee_id')
    @api.one
    def _user_view_validate(self):
        cr, uid, context = self.env.args
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
        hr_year_obj = self.env['hr.year']
        args = [('date_start', '<=', date), ('date_stop', '>=', date)]
        hr_year_brw = hr_year_obj.search(args)
        if hr_year_brw and hr_year_brw.ids:
            hr_year_ids = hr_year_brw
        else:
            year = datetime.strptime(date,
                                     DEFAULT_SERVER_DATE_FORMAT).year
            end_date = str(year) + '-12-31'
            start_date = str(year) + '-01-01'
            hr_year_ids = hr_year_obj.create({'date_start': start_date,
                                              'date_stop': end_date,
                                              'code': str(year),
                                              'name': str(year)
                                              })
        return hr_year_ids.ids[0]

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

#    @api.constrains('date_from', 'date_to', 'employee_id')
#    def _check_date(self):
#        for holiday in self:
#            domain = [
#                ('date_from', '<=', holiday.date_to),
#                ('date_to', '>=', holiday.date_from),
#                ('employee_id', '=', holiday.employee_id.id),
#                ('id', '!=', holiday.id),
#                ('type', '=', holiday.type),
#                ('state', 'not in', ['cancel', 'refuse']),
#            ]
#            nholidays = self.search_count(domain)
#            if nholidays:
#                raise ValidationError(_('You can not have 2 leaves that ' \
#                                        'overlaps on same day!'))

    @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    def _check_public_holiday_leave(self):
        for rec in self:
            if rec.holiday_status_id and rec.holiday_status_id.count_days_by:
                if rec.holiday_status_id.count_days_by == 'working_days_only':
                    diff_day = rec._check_holiday_to_from_dates(
                        rec.request_date_from, rec.request_date_to)
                    if diff_day == 0:
                        raise ValidationError(
                            _('You are not able to apply leave Request on Holiday.!'))

    @api.constrains('request_date_from', 'request_date_to', 'hr_year_id')
    def _check_current_year_leave_req(self):
        '''
        The method is used to validate only current year leave request.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        current_year = datetime.today().date().year
        for rec in self:
            if rec.holiday_status_id.id:
                from_date_year = datetime.strptime(
                    rec.request_date_from, DEFAULT_SERVER_DATETIME_FORMAT).date().year
                to_date_year = datetime.strptime(
                    rec.request_date_to, DEFAULT_SERVER_DATETIME_FORMAT).date().year
                if current_year != from_date_year or current_year != to_date_year:
                    raise ValidationError(
                        _('You can apply leave Request only for the current year!'))
                if rec.hr_year_id and rec.hr_year_id.date_start and rec.hr_year_id.date_stop:
                    if rec.hr_year_id.date_start > rec.request_date_from or rec.hr_year_id.date_stop < rec.request_date_to:
                        raise ValidationError(
                            _('Start date and end date must be related to selected HR year!'))

    def _get_number_of_daystmp(self, date_from, date_to):
        """
        Returns a float equals to the time delta between two dates given.
        """
        from_dt = date_from
        to_dt = date_to
        if self._context and 'tz' in self._context:
            date_from = self.check_time_zone(from_dt)
            date_to = self.check_time_zone(to_dt)
        strp_s_date = datetime.strptime(
            date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
        strf_s_date = strp_s_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        strp_e_date = datetime.strptime(
            date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
        strf_e_date = strp_e_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        dates = list(rrule.rrule(rrule.DAILY,
                                 dtstart=parser.parse(date_from),
                                 until=parser.parse(date_to)))
        dates = [x.strftime(DEFAULT_SERVER_DATETIME_FORMAT) for x in dates]
        return len(dates)

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
            dates = list(rrule.rrule(rrule.DAILY,
                                     dtstart=parser.parse(from_date),
                                     until=parser.parse(to_date)))
        return dates

    def check_time_zone(self, t_date):
        t_date = str(t_date)
        dt_value = t_date
        if t_date:
            timez = 'Asia/Kuala_Lumpur'
            if self._context.get('tz'):
                timez = self._context.get('tz')
            rec_date_from = datetime.strptime(
                t_date, DEFAULT_SERVER_DATETIME_FORMAT)
            src_tz = pytz.timezone('UTC')
            dst_tz = pytz.timezone(timez)
            src_dt = src_tz.localize(rec_date_from, is_dst=True)
            dt_value = src_dt.astimezone(dst_tz)
            dt_value = dt_value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return dt_value

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
        --------------------------------------------------------------------------
        '''
        if self._context and 'tz' in self._context:
            start_date = self.check_time_zone(start_date)
            end_date = self.check_time_zone(end_date)
        strp_s_date = datetime.strptime(
            start_date, DEFAULT_SERVER_DATETIME_FORMAT).date()
        strf_s_date = strp_s_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        strp_e_date = datetime.strptime(
            end_date, DEFAULT_SERVER_DATETIME_FORMAT).date()
        strf_e_date = strp_e_date.strftime(DEFAULT_SERVER_DATE_FORMAT)

        dates = self.get_date_from_range(strf_s_date, strf_e_date)
        dates = [x.strftime(DEFAULT_SERVER_DATE_FORMAT) for x in dates]
        remove_date = []
        for day in dates:
            date = datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT).date()
            if date.isoweekday() in [6, 7]:
                remove_date.append(day)
        for remov in remove_date:
            if remov in dates:
                dates.remove(remov)
        date_f = datetime.strptime(start_date,
                                   DEFAULT_SERVER_DATETIME_FORMAT).date()
        calendar = date_f.isocalendar()
        public_holiday_ids = self.env['hr.holiday.public'
                                      ].search([('state', '=', 'validated'),
                                                ('hr_year_id.name', '=', calendar[0])])
        if public_holiday_ids and public_holiday_ids.ids:
            for public_holiday_record in public_holiday_ids:
                for holidays in public_holiday_record.holiday_line_ids:
                    if holidays.holiday_date in dates:
                        dates.remove(holidays.holiday_date)
        no_of_day = 0.0
#        start_date1 = datetime.strptime(start_date,
#                                                 DEFAULT_SERVER_DATETIME_FORMAT
#                                                 ).date().strftime(DEFAULT_SERVER_DATE_FORMAT)
#        end_date1 = datetime.strptime(end_date,
#                                               DEFAULT_SERVER_DATETIME_FORMAT
#                                               ).date().strftime(DEFAULT_SERVER_DATE_FORMAT)
        for day in dates:
            #            if day >= start_date1 and day <= end_date1:
            if day >= strf_s_date and day <= strf_e_date:
                no_of_day += 1
        return no_of_day

    @api.onchange('date_from', 'date_to', 'holiday_status_id')
    def onchange_date_from(self, date_from=False, date_to=False,
                           holiday_status_id=False):
        '''
        when you change from date, this method will set
        leave type and numbers of leave days accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        if date_from == False:
            date_from = self.date_from
        if date_to == False:
            date_to = self.date_to
        if holiday_status_id == False:
            holiday_status_id = self.holiday_status_id.id
        leave_day_count = False
        if holiday_status_id and holiday_status_id != False:
            leave_day_count = self.env['hr.leave.type'
                                       ].browse(holiday_status_id
                                                ).count_days_by
        if (date_from and date_to) and (date_from > date_to):
            raise UserError(_('Warning!\nThe start date must be anterior to\
             the end date.'))
        elif (date_from and date_to):
            date_to = date_from
        result = {'value': {}}
        if date_from and not date_to:
            date_to_with_delta = date_from
            result['value']['date_to'] = str(date_to_with_delta)
        if (date_to and date_from) and (date_from <= date_to):
            if leave_day_count != False and leave_day_count == \
                    'working_days_only':
                diff_day = self._check_holiday_to_from_dates(date_from,
                                                             date_to)
                result['value']['number_of_days'] = \
                    round(math.floor(diff_day))
            else:
                diff_day = self._get_number_of_daystmp(date_from, date_to)
                result['value']['number_of_days'] = diff_day
        else:
            result['value']['number_of_days'] = 0
        return result

# ============================================
#    Users: Button Methods
# ============================================

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
    def notification_leave_information(self):
        obj_mail_server = self.env['ir.mail_server']
        mail_server_ids = obj_mail_server.search([])
        if not mail_server_ids and mail_server_ids.ids:
            raise ValidationError(_('No mail outgoing mail server specified.')
                                  )
        mail_server_record = mail_server_ids[0]
        work_email = []
        domain = [('is_daily_notificaiton_email_send', '=', True)]
        for emp in self.env['hr.employee'].search(domain):
            if not emp.work_email:
                if emp.user_id and emp.user_id.login and \
                        emp.user_id.login not in work_email:
                    work_email.append(str(emp.user_id.login))
            elif emp.work_email not in work_email:
                work_email.append(str(emp.work_email))
        if not work_email:
            raise ValidationError(_('Email must be configured in employees.'
                                    'which have notification is enable for Receiving email'
                                    'notifications of employees who are on leave !'))
        hr_manager = ''
        today = datetime.now()
        new_list_holidays = []
        for day in range(0, 6):
            date_calc = today + timedelta(days=day)
            date_calc = date_calc.strftime(DEFAULT_SERVER_DATE_FORMAT)
            hr_domain = [('type', '=', 'remove'),
                         ('state', 'in', ['validate']),
                         ('date_from', '<=', date_calc + " 23:59:59"),
                         ('date_to', '>=', date_calc + " 00:00:00")
                         ]
            for holiday in self.search(hr_domain):
                if holiday.id in new_list_holidays:
                    continue
                new_list_holidays.append(holiday.id)
        for holiday in self.browse(new_list_holidays):
            leave_type = ustr(holiday.holiday_status_id.name)
            start_date = datetime.strptime(holiday.date_from,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            end_date = datetime.strptime(holiday.date_to,
                                         DEFAULT_SERVER_DATETIME_FORMAT)
            hr_manager += '<tr><td width="25%%">' + \
                holiday.employee_id.name + '</td><td width="20%%">' + \
                start_date.strftime('%d-%m-%Y') + '</td><td width="20%%">' + \
                end_date.strftime('%d-%m-%Y') + '</td><td width="20%%">' + \
                leave_type + '</td></tr>'
        if not hr_manager:
            return True
        start_mail = """Hi,<br/><br/>These are the list of employees who are \
        on leave in this week.<br/><br/>
        <table border=\'1\'>
         <tr><td width="25%%"><b> Employee Name </b></td><td width="20%%"><b>
         Date From</b></td><td width="20%%"><b>Date To</b></td>
         <td width="20%%"><b>Leave Type</b></td></tr>"""
        final_hrmanager_body = start_mail + hr_manager + \
            "</table><br/><br/>Thank You.<br/><br/>Server <b>" + self._cr.dbname +\
            "</b>"
        message_hrmanager = obj_mail_server.build_email(
            email_from=mail_server_record.smtp_user,
            email_to=work_email,
            subject='Notification : Employees who are on Leave in this week.',
            body=final_hrmanager_body,
            body_alternative=final_hrmanager_body,
            email_cc=None,
            email_bcc=None,
            attachments=None,
            references=None,
            object_id=None,
            subtype='html',
            subtype_alternative=None,
            headers=None)
        obj_mail_server.send_email(message_hrmanager,
                                   mail_server_id=mail_server_record.id)
        return True

    @api.model
    def notification_leave_approval(self):
        if datetime.now().weekday() not in [0]:
            return False
        holiday_ids = self.search([('type', '=', 'remove'),
                                   ('state', 'in', ['confirm', 'validate1'])
                                   ])
        if not holiday_ids and not holiday_ids.ids:
            return False
        obj_mail_server = self.env['ir.mail_server']
        mail_server_ids = obj_mail_server.search([])
        if not mail_server_ids and not mail_server_ids.ids:
            raise ValidationError(_('No mail outgoing mail server specified!')
                                  )
        mail_server_record = mail_server_ids[0]
        work_email = []
        user_ids = self.env.ref('hr.group_hr_manager').users.ids
        emp_ids = self.env['hr.employee'
                           ].search([('user_id', 'in', user_ids)])
        for emp in emp_ids:
            if not emp.is_pending_leave_notificaiton:
                continue
            if not emp.work_email:
                if emp.user_id and emp.user_id.login and \
                        emp.user_id.login not in work_email:
                    work_email.append(str(emp.user_id.login))
                else:
                    raise ValidationError(_('Email must be configured \
                    in %s HR manager !') % (emp.name))
            elif emp.work_email not in work_email:
                work_email.append(str(emp.work_email))
        hrmanager = ''
        directmanager = {}
        indirectmgr = {}
        for holiday in holiday_ids:
            start_date = datetime.strptime(holiday.date_from,
                                           "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(holiday.date_to,
                                         "%Y-%m-%d %H:%M:%S")
            create_date = datetime.strptime(holiday.create_date,
                                            "%Y-%m-%d %H:%M:%S")
            state_dict = {
                'draft': 'New',
                'confirm': 'Waiting Pre-Approval',
                'refuse': 'Refused',
                          'validate1': 'Waiting Final Approval',
                          'validate': 'Approved',
                          'cancel': 'Cancelled',
            }
            mail_cont = '<tr><td width="25%%">' + holiday.employee_id.name + \
                '</td><td width="20%%">' + state_dict.get(holiday.state) + \
                '</td><td width="20%%">' + create_date.strftime('%d-%m-%Y') + \
                '</td><td width="20%%">' + start_date.strftime('%d-%m-%Y') + \
                '</td><td width="20%%">' + end_date.strftime('%d-%m-%Y') + \
                '</td></tr>'
            hrmanager += mail_cont
            if holiday.state == 'confirm' and \
                    holiday.employee_id and holiday.employee_id.parent_id and \
                    holiday.employee_id.parent_id.is_pending_leave_notificaiton:
                direct_manager_mail = holiday.employee_id.parent_id and \
                    holiday.employee_id.parent_id.work_email or \
                    holiday.employee_id.parent_id.user_id.login or \
                    False
                if direct_manager_mail not in work_email:
                    if direct_manager_mail and \
                            direct_manager_mail in directmanager:
                        directmanager[direct_manager_mail
                                      ] = directmanager[direct_manager_mail
                                                        ] + mail_cont
                    elif direct_manager_mail:
                        directmanager[direct_manager_mail] = mail_cont
            elif holiday.state == 'validate1' and \
                    holiday.employee_id and holiday.employee_id.parent_id2 and \
                    holiday.employee_id.parent_id2.is_pending_leave_notificaiton:
                indirect_mgr_mail = holiday.employee_id.parent_id2 and \
                    holiday.employee_id.parent_id2.work_email or \
                    holiday.employee_id.parent_id2.user_id.login or \
                    False
                if indirect_mgr_mail not in work_email:
                    if indirect_mgr_mail \
                            and indirect_mgr_mail in indirectmgr:
                        indirectmgr[indirect_mgr_mail
                                    ] = indirectmgr[indirect_mgr_mail
                                                    ] + mail_cont
                    elif indirect_mgr_mail:
                        indirectmgr[indirect_mgr_mail] = mail_cont
        start_mail = """Hi,<br/><br/>Below are the list of employees who have
        pending leave approval.<br/><br/>
        <table border=\'1\'>
         <tr><td width="25%%"><b>Name Of Employee</b> </td><td width="20%%">
         <b>Status</b></td><td width="20%%"><b>Date Applied</b></td>
         <td width="20%%"><b>Leave Start Date</b></td>
         <td width="20%%"><b>Leave End Date</b></td></tr>"""
        final_hrmanager_body = start_mail + hrmanager + \
            "</table><br/><br/>Thanks."
        # Send mail to HR Manager
        if work_email:
            message_hrmanager = obj_mail_server.build_email(
                email_from=mail_server_record.smtp_user,
                email_to=work_email,
                subject='Pending Leaves Notification Email.',
                body=final_hrmanager_body,
                body_alternative=final_hrmanager_body,
                email_cc=None,
                email_bcc=None,
                attachments=None,
                references=None,
                object_id=None,
                subtype='html',
                subtype_alternative=None,
                headers=None)
            obj_mail_server.send_email(message_hrmanager,
                                       mail_server_id=mail_server_record.id)
        # Send mail to Direct Manager
        for key, val in directmanager.items():
            final_direcmanager_body = start_mail + val + \
                "</table><br/><br/>Thanks."
            message_directmanager = obj_mail_server.build_email(
                email_from=mail_server_record.smtp_user,
                email_to=[key],
                subject='Pending Leaves Notification Email.',
                body=final_direcmanager_body,
                body_alternative=final_direcmanager_body,
                email_cc=None,
                email_bcc=None,
                attachments=None,
                references=None,
                object_id=None,
                subtype='html',
                subtype_alternative=None,
                headers=None)
            obj_mail_server.send_email(message_directmanager,
                                       mail_server_id=mail_server_record.id)

        # Send mail to Indirect Manager
        for key, val in indirectmgr.items():
            final_indirecmanager_body = start_mail + val + \
                "</table><br/><br/>Thanks."
            message_indirectmanager = obj_mail_server.build_email(
                email_from=mail_server_record.smtp_user,
                email_to=[key],
                subject='Pending Leaves Notification Email.',
                body=final_indirecmanager_body,
                body_alternative=final_indirecmanager_body,
                email_cc=None,
                email_bcc=None,
                attachments=None,
                references=None,
                object_id=None,
                subtype='html',
                subtype_alternative=None,
                headers=None)
            obj_mail_server.send_email(message_indirectmanager,
                                       mail_server_id=mail_server_record.id)
        return True

    @api.model
    def _check_holiday_carryforward(self, holiday_id, start_date, end_date):
        '''
            Checks that there is a public holiday,Saturday and
            Sunday on date of leave
        '''
        holiday_rec = self.browse(holiday_id)
        dates = self.get_date_from_range(holiday_id,
                                         holiday_rec.date_from,
                                         holiday_rec.date_to)
        dates = [x.strftime('%Y-%m-%d') for x in dates]

        remove_date = []
        for day in dates:
            date = datetime.strptime(day,
                                     DEFAULT_SERVER_DATE_FORMAT
                                     ).date()
            if date.isoweekday() in [6, 7]:
                remove_date.append(day)

        for remov in remove_date:
            if remov in dates:
                dates.remove(remov)
        public_holiday_ids = self.env['hr.holiday.public'
                                      ].search([('state', '=', 'validated')])
        if public_holiday_ids:
            for public_holiday_record in public_holiday_ids:
                for holidays in public_holiday_record.holiday_line_ids:
                    if holidays.holiday_date in dates:
                        dates.remove(holidays.holiday_date)
        no_of_day = 0.0
        for day in dates:
            if day >= start_date and day <= end_date:
                no_of_day += 1
        return no_of_day

    @api.model
    def assign_carry_forward_leave(self):
        '''
        This method will be called by scheduler which will assign
        carry forward leave on end of the year i.e YYYY/12/31 23:59:59
        '''
        emp_obj = self.env['hr.employee']
        data_obj = self.env['ir.model.data']
        fiscal_obj = self.env['hr.year']

        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.strptime(today,
                                 DEFAULT_SERVER_DATE_FORMAT).year
        prev_year_date = str(year - 1) + '-01-01'

        empl_ids = emp_obj.search([('active', '=', True)])
        holiday_status_ids = self.env['hr.leave.type'
                                      ].search([('cry_frd_leave', '>', 0)])
        hr_year_id = self.fetch_hryear(prev_year_date)
        current_hr_year_id = self.fetch_hryear(today)
        hr_year_rec = self.env['hr.year'].browse(hr_year_id)
        start_date = hr_year_rec.date_start
        end_date = hr_year_rec.date_stop
        for holiday in holiday_status_ids:
            for employee in empl_ids:
                if employee.user_id and employee.user_id.id == 1:
                    continue
                add = 0.0
                remove = 0.0
                self._cr.execute("SELECT sum(number_of_days_temp) FROM"
                                 " hr_holidays where employee_id=%d and"
                                 " state='validate' and holiday_status_id "
                                 "= %d and type='add' and hr_year_id=%d" %
                                 (employee.id, holiday.id, hr_year_id))
                all_datas = self._cr.fetchone()
                if all_datas and all_datas[0]:
                    add += all_datas[0]
                self._cr.execute("SELECT sum(number_of_days_temp) "
                                 "FROM hr_holidays where employee_id=%d"
                                 " and state='validate' and "
                                 "holiday_status_id = %d and type='remove'"
                                 " and date_from >= '%s' and date_to "
                                 "<= '%s'" %
                                 (employee.id, holiday.id,
                                  start_date, end_date))
                leave_datas = self._cr.fetchone()
                if leave_datas and leave_datas[0]:
                    remove += leave_datas[0]
                self._cr.execute("SELECT id FROM hr_holidays where "
                                 "employee_id=%d and state='validate'"
                                 " and holiday_status_id = %d and "
                                 "type='remove' and date_from <= '%s' "
                                 "and date_to >= '%s'" %
                                 (employee.id, holiday.id,
                                  start_date, end_date))
                leave_datas = self._cr.fetchall()
                if leave_datas:
                    for data in leave_datas:
                        if data[0]:
                            remove += \
                                self._check_holiday_carryforward(data[0],
                                                                 start_date,
                                                                 end_date)
                final = add - remove
                final = final > holiday.cry_frd_leave and \
                    holiday.cry_frd_leave or final
                if final > 0.0:
                    cleave_dict = {
                        'name': 'Default Carry Forward Leave Allocation',
                        'employee_id': employee.id,
                        'holiday_type': 'employee',
                        'holiday_status_id': holiday.id,
                        'number_of_days_temp': final,
                        'type': 'add',
                        'hr_year_id': current_hr_year_id,
                        'carry_forward': True
                    }
                    self.create(cleave_dict)
        obj_mail_server = self.env['ir.mail_server']
        mail_server_ids = obj_mail_server.search([])
        if not mail_server_ids:
            raise ValidationError(_('No mail outgoing mail server'
                                    ' specified!'))
        mail_server_record = mail_server_ids[0]

        result_data = data_obj._get_id('hr', 'group_hr_manager')
        model_data = data_obj.browse(result_data)
        group_data = self.env['res.groups'].browse(model_data.res_id)
        user_ids = [user.id for user in group_data.users]
        work_email = []
        emp_ids = emp_obj.search([('user_id', 'in', user_ids)])
        for emp in emp_ids:
            if not emp.work_email:
                if emp.user_id and emp.user_id.login and \
                        emp.user_id.login not in work_email:
                    work_email.append(str(emp.user_id.login))
                else:
                    raise ValidationError(_('Email must be configured in'
                                            ' %s HR manager !') %
                                          (emp.name))
            elif emp.work_email not in work_email:
                work_email.append(str(emp.work_email))
        if mail_server_record.smtp_user:
            body = "Hi,<br/><br/>Server <b> " + self._cr.dbname + \
                "</b> has finished performing the Auto Allocation For <b>\
                    " + str(year) + "</b>.<br/><br/>Kindly login to "\
                "Server <b> " + self._cr.dbname + \
                "</b> to confirm the leave allocations. "\
                "<br/><br/>Thank You,<br/><br/>Server <b>" + \
                self._cr.dbname + "</b>"
            message_hrmanager = obj_mail_server.build_email(
                email_from=mail_server_record.smtp_user,
                email_to=work_email,
                subject='Notification : Auto Allocation Complete for ' +
                str(year),
                body=body,
                body_alternative=body,
                email_cc=None,
                email_bcc=None,
                attachments=None,
                references=None,
                object_id=None,
                subtype='html',
                subtype_alternative=None,
                headers=None)
            obj_mail_server.send_email(message=message_hrmanager,
                                       mail_server_id=mail_server_record.id)
        return True

    @api.multi
    def assign_default_leave(self):
        '''
        This method will be called by scheduler which will assign
        Annual leave at end of the year i.e YYYY/12/01 00:01:01
        '''
        emp_obj = self.env['hr.employee']

        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.strptime(today,
                                 DEFAULT_SERVER_DATE_FORMAT).year
        next_year_date = str(year) + '-01-01'
        fiscalyear_id = self.fetch_hryear(next_year_date)

        holiday_status_ids = self.env['hr.leave.type'
                                      ].search([('default_leave_allocation',
                                                 '>', 0)])
        empl_ids = emp_obj.search([('active', '=', True)])
        for holiday in holiday_status_ids:
            for employee in empl_ids:
                if employee.user_id and employee.user_id.id == 1:
                    continue
                leave_dict = {
                    'name': 'Assign Default Allocation.',
                    'employee_id': employee.id,
                    'holiday_type': 'employee',
                    'holiday_status_id': holiday.id,
                    'number_of_days_temp': holiday.default_leave_allocation,
                    'type': 'add',
                    'hr_year_id': fiscalyear_id
                }
                self.create(leave_dict)
        return True


class ResUsers(models.Model):

    _inherit = 'res.users'

# ============================================
#    Users: ORM Methods
# ============================================

    @api.model
    def create(self, data):
        context = dict(self._context)
        context['noshortcut'] = True
        user_id = super(ResUsers, self).create(data)
        user_id.check_user_access()
        return user_id

    @api.multi
    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        self.check_user_access()
        return result

    # @api.multi
    # def check_user_access(self):
    #     mod_obj = self.env['ir.model.data']
    #     group_result = mod_obj.get_object('base', 'group_erp_manager')
    #     new_user_add = [user.id for user in group_result.users]
    #     group_result = mod_obj.get_object('base', 'group_system')
    #     system_user_add = [user.id for user in group_result.users]
    #     for user in self:
    #         if self._uid == 1:
    #             continue
    #         if user.id in new_user_add or user.id in system_user_add:
    #             raise ValidationError(_('You cannot give administrator \
    #             access rights !'))
    #     return True
