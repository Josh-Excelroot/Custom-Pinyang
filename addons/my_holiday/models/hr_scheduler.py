# See LICENSE file for full copyright and licensing details

import time
import base64
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, ustr
# from odoo.addons.resource.models.resource import HOURS_PER_DAY

HOURS_PER_DAY = 8
class LeaveRequest(models.Model):

    _inherit = "hr.leave"


    def check_outgoining_mail_server(self):
        mail_server_id = self.env['ir.mail_server'].search(
            [('smtp_user', '!=', False)], limit=1)
        return mail_server_id

    @api.model
    def notification_leave_information(self):
        mail_server_id = self.check_outgoining_mail_server()
        mail_server_record = mail_server_id and mail_server_id.id or False
        leave_details = ''
        work_email = []
        today = datetime.now().date()
        week_end = today + timedelta(days=6)
        leaves = self.search([('request_date_from', '>=', today),
                              ('request_date_from', '<', week_end),
                              ('state', '=', 'validate')])
        if not mail_server_record or not leaves:
            return True
        for leave in leaves:
            if leave.employee_id.is_daily_notificaiton_email_send:
                if not leave.employee_id.work_email and \
                        leave.employee_id.user_id.login not in work_email:
                    work_email.append(leave.employee_id.user_id.login)
                elif leave.employee_id.work_email and \
                        leave.employee_id.work_email not in work_email:
                    work_email.append(leave.employee_id.work_email)
                leave_details += '<tr>' +\
                    '<td width="25%%">' + leave.employee_id.name + '</td>'\
                    '<td width="20%%">' + leave.date_from.strftime('%d-%m-%Y')\
                    + '</td>'\
                    '<td width="20%%">' + leave.date_to.strftime('%d-%m-%Y')\
                    + '</td>'\
                    '<td width="20%%">' + leave.holiday_status_id.name + \
                    '</td></tr>'
        if not work_email:
            raise ValidationError(_('Email must be configured in employees.'
                                    'which have notification is enable for Receiving email'
                                    'notifications of employees who are on leave !'))
        start_mail = """Hi,<br/><br/>These are the list of employees who are \
        on leave in this week.<br/><br/>
        <table border=\'1\'>
         <tr><td width="25%%"><b> Employee Name </b></td><td width="20%%"><b>
         Date From</b></td><td width="20%%"><b>Date To</b></td>
         <td width="20%%"><b>Leave Type</b></td></tr>"""
        mail_body = start_mail + leave_details + \
            "</table><br/><br/>Thank You.<br/><br/>Server <b>" + self._cr.dbname + \
            "</b>"
        message_hrmanager = self.env['ir.mail_server'].build_email(
            email_from=mail_server_record.smtp_user,
            email_to=work_email,
            subject='Notification : Employees who are on Leave in this week.',
            body=mail_body,
            body_alternative=mail_body,
            email_cc=None,
            email_bcc=None,
            attachments=None,
            references=None,
            object_id=None,
            subtype='html',
            subtype_alternative=None,
            headers=None)
        self.env['ir.mail_server'].send_email(
            message_hrmanager, mail_server_id=mail_server_record.id)
        return True

    @api.model
    def notification_leave_approval(self):
        mail_server_id = self.check_outgoining_mail_server()
        mail_server_record = mail_server_id and mail_server_id.id or False
        obj_mail_server = self.env['ir.mail_server']
        holiday_ids = self.search([('state', 'in', ['confirm', 'validate1'])])
        if not mail_server_record or not holiday_ids:
            return False
        work_email = []
        hrmanager = ''
        directmanager = {}
        indirectmgr = {}
        for holiday in holiday_ids:
            start_date = holiday.date_from
            end_date = holiday.date_to
            create_date = holiday.create_date
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
                    (holiday.employee_id.parent_id.work_email
                     or holiday.employee_id.parent_id.user_id.login
                     or False)
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
    def assign_carry_forward_leave(self):
        '''
        This method will be called by scheduler which will assign
        carry forward leaves
        '''
        emp_obj = self.env['hr.employee']
        today = datetime.now().date()
        year = today.year
        prev_year_date = str(year - 1) + '-01-01'
        next_year_date = str(year + 1) + '-01-01'
        empl_ids = emp_obj.search(
            [('active', '=', True), ('cry_frd_leave', '>', 0)])
#         holiday_status_ids = self.env['hr.leave.type'].search([
#             ('cry_frd_leave', '>', 0), ('allocation_type', '!=', 'no')])
        hr_year_id = self.fetch_hryear(prev_year_date)
        current_hr_year_id = self.fetch_hryear(today)
        next_hr_year_id = self.fetch_hryear(next_year_date)
        hr_year_rec = self.env['hr.year'].browse(hr_year_id)
        start_date = hr_year_rec.date_start
        end_date = hr_year_rec.date_stop
        holiday_type = self.env.ref('hr_holidays.holiday_status_cl')
#         for holiday in holiday_status_ids:
        for employee in empl_ids:
            #                 if employee.user_id and employee.user_id.id in [1, 2]:
            #                     continue
            add = 0.0
            remove = 0.0
            self._cr.execute("""
                                SELECT
                                    sum(number_of_days)
                                FROM
                                    hr_leave_allocation
                                where
                                    employee_id=%s and
                                    state='validate' and
                                    holiday_status_id=%s and
                                    hr_year_id=%s
                            """, (employee.id, holiday_type.id, hr_year_id))
            all_datas = self._cr.fetchone()
            if all_datas and all_datas[0]:
                add += all_datas[0]
            self._cr.execute("""
                                SELECT
                                    sum(number_of_days)
                                FROM
                                    hr_leave
                                where
                                    employee_id=%s and
                                    state='validate' and
                                    holiday_status_id=%s and
                                    date_from >=%s and
                                    date_to <=%s
                            """, (employee.id, holiday_type.id,
                                  start_date, end_date))
            leave_datas = self._cr.fetchone()
            if leave_datas and leave_datas[0]:
                remove += leave_datas[0]
            final = add - remove
            final = final > employee.cry_frd_leave and \
                employee.cry_frd_leave or final
            if final > 0.0:
                cleave_dict = {
                    'name': 'Default Carry Forward Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_type': 'employee',
                    'holiday_status_id': holiday_type.id,
                    'number_of_days': final,
                    'hr_year_id': next_hr_year_id,
                    'carry_forward': True,
                    'state': 'confirm',
                }
                leave = self.env['hr.leave.allocation'].create(cleave_dict)
#                 leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('hr_holidays.holiday_status_cl')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_leave_allocation', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Allocation.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_leave_allocation,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_leave_allocation / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_sick_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('hr_holidays.holiday_status_sl')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_sick_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Sick Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_sick_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_sick_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_hospital_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('my_holiday.holiday_status_hospital')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_hospital_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Hospital Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_hospital_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_hospital_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_maternity_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('my_holiday.holiday_status_maternity')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_maternity_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Maternity Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_maternity_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_maternity_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_paternity_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('my_holiday.holiday_status_paternity')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_paternity_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Paternity Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_paternity_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_paternity_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_unpaid_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('hr_holidays.holiday_status_unpaid')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_unpaid_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Unpaid Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_unpaid_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_unpaid_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True

    @api.model
    def assign_default_marriage_leave(self):
        emp_obj = self.env['hr.employee']
        holiday_type = self.env.ref('my_holiday.holiday_status_marriage')
        today = datetime.now().date()
        year = today.year
        next_year_date = str(year + 1) + '-01-01'
        next_hr_year_id = self.fetch_hryear(next_year_date)
        empl_ids = emp_obj.search(
            [('active', '=', True), ('default_mrg_leave', '>', 0)])
        for employee in empl_ids:
            leave_dict = {
                'name': 'Assign Default Marriage Leave.',
                'employee_id': employee.id,
                'holiday_type': 'employee',
                'holiday_status_id': holiday_type.id,
                'hr_year_id': next_hr_year_id,
                'type_request_unit': holiday_type.request_unit,
                'number_of_days': employee.default_mrg_leave,
                'state': 'confirm',
            }
            if holiday_type.request_unit == 'hour':
                emp_days = employee.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY or 8
                leave_dict['number_of_days'] = round(
                    employee.default_mrg_leave / emp_days)
            leave = self.env['hr.leave.allocation'].create(leave_dict)
#             leave.sudo().action_approve()
        return True


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    @api.model
    def _check_employee_status(self):
        """
        This Function is call by scheduler.
        """
        mail_ids = []
        emp_resign_str = 'Employee Name\t\tLast Date\n'
        work_email = []
        hr_groups = self.env.ref('hr.group_hr_manager')
        emp_ids = self.search([('user_id', 'in', hr_groups.users.ids)])
        for emp in emp_ids:
            if not emp.work_email:
                if emp.user_id and emp.user_id.login and \
                        emp.user_id.login not in work_email:
                    work_email.append(str(emp.user_id.login))
                else:
                    raise ValidationError(
                        _('Email must be configured in %s HR manager !'
                          ) % (emp.name))
            else:
                work_email.append(emp.work_email)
        mail_server_ids = self.env['ir.mail_server'].search([])
        if not mail_server_ids and not mail_server_ids.ids:
            raise ValidationError(
                _('No mail outgoing mail server specified!'))
        mail_server_record = mail_server_ids[0]
        email_from = mail_server_record.smtp_user
        if not email_from:
            raise ValidationError(_('No email specified in SMTP server!'))
        if not work_email:
            raise ValidationError(_('No Hr Manager email found!'))
        emp_change_ids = []
        emp_resign_list = []
        current_date = datetime.now().date()
        for employee in self.search([]):
            if employee.evaluation_date:
                evaluation_date = self.check_time_zone(
                    employee.evaluation_date)
                current_date = self.check_time_zone(current_date)
                evaluation_date = datetime.strptime(evaluation_date,
                                                    DEFAULT_SERVER_DATE_FORMAT)
                current_date = datetime.strptime(current_date,
                                                 DEFAULT_SERVER_DATE_FORMAT)
                diff_days = (evaluation_date - current_date).days
                if diff_days == 30:
                    body = 'Hello,\n\n \
                           %s has an upcoming performance review on %s : \n\n \
                           Please conduct it by %s \n\n \
                           Thanks,' % (employee.name,
                                       evaluation_date.strftime("%d/%m/%Y"),
                                       evaluation_date.strftime("%d/%m/%Y"))
                    if work_email:
                        vals = {
                            'state': 'outgoing',
                            'subject': 'Upcoming performance review date on \
                                %s.' % evaluation_date.strftime("%d/%m/%Y"),
                            'body_html': '<pre>%s</pre>' % ustr(body) or
                            '',
                            'email_to': " , ".join(work_email),
                            'email_from': email_from}
                        email_30 = self.env['mail.mail'].create(vals)
                        mail_ids.append(email_30.id)
            if employee.rem_days == 0 and employee.emp_status == "in_notice":
                emp_change_ids.append(employee.id)
            if employee.rem_days == 3 and employee.emp_status == "in_notice":
                emp_resign_list.append(employee.id)
                emp_resign_str += '%s\t\t%s\n' % (employee.name,
                                                  employee.last_date)
        if emp_resign_list:
            body = 'Hello,\n\nBelow is the list of employees who are \
            resigning this month \n\n%s\n\nThanks,' % (emp_resign_str)
            if work_email:
                vals = {
                    'state': 'outgoing',
                    'subject': 'Notification for Terminate with in 3 days',
                    'body_html': '<pre>%s</pre>' % ustr(body) or '',
                    'email_to': " , ".join(work_email),
                    'email_from': email_from}
                email_rsg = self.env['mail.mail'].create(vals)
                mail_ids.append(email_rsg.id)
        if emp_change_ids:
            for emp_brw in self.browse(emp_change_ids):
                emp_brw.write({'emp_status': 'terminated'})
        if mail_ids:
            for mails in self.env['mail.mail'].browse(mail_ids):
                mails.send()
        return True

    @api.model
    def _check_employee_doc_expiry(self):
        """
            This Function is call by scheduler.
        """
        doc_emp_list = 'Employee Name\t\tDocument\t\tExpiry Date\n'
        doc_exp_list = []
        mail_server_ids = self.env['ir.mail_server'].search([])
        if not mail_server_ids and not mail_server_ids.ids:
            raise ValidationError(_('No mail outgoing mail server specified!')
                                  )
        group_data = self.env.ref('hr.group_hr_manager')
        work_email = []
        user_ids = [user.id for user in group_data.users]
        emp_ids = self.search([('user_id', 'in', user_ids)])
        for emp in emp_ids:
            if not emp.work_email:
                if emp.user_id and emp.user_id.login not in work_email:
                    work_email.append(str(emp.user_id.login))
            else:
                work_email.append(str(emp.work_email))
        mail_server_record = mail_server_ids[0]
        email_from = mail_server_record.smtp_user
        if not email_from:
            raise ValidationError(_('No email specified in smtp server!'))
        if not work_email:
            raise ValidationError(_('No Hr Manager found!'))
        current_date = datetime.now().date()
        for employee in self.search([]):
            if employee.immigration_ids and employee.immigration_ids.ids:
                for document in employee.immigration_ids:
                    exp_dt = document.exp_date
                    doc_name = document.documents
                    rem_day = (exp_dt - current_date).days
                    if rem_day < 60:  # or rem_day <= 123:
                        doc_exp_list.append(employee.id)
                        doc_emp_list += '%s\t\t%s\t\t%s\n' % (employee.name,
                                                              doc_name,
                                                              exp_dt)
        if doc_exp_list:
            exp_doc_mail_body = 'Hello,\n\nBelow is the list of names which '\
                'documents are going to expire.' \
                '\n\n\n%s\n\nThanks,' % (doc_emp_list)
            if work_email:
                vals = {
                    'state': 'outgoing',
                    'subject': 'Notification for Document Expiry Date',
                    'body_html': '<pre>%s</pre>' % ustr(exp_doc_mail_body
                                                        ) or '',
                    'email_to': " , ".join(work_email),
                    'email_from': email_from}
                new_mails = self.env['mail.mail'].create(vals)
                new_mails.send()
        return True

    @api.model
    def get_expiry_documents(self):
        """
        It will be called from scheduler and finds the documents that
        will be expired after 30 days.
        """
        next_date = (datetime.strptime(time.strftime('%Y-%m-%d'),
                                       '%Y-%m-%d') +
                     relativedelta(days=30)).strftime('%Y-%m-%d')
        self._cr.execute("SELECT employee_id as employee, doc_type_id as \
            type FROM employee_immigration GROUP BY employee_id, doc_type_id")
        datas = self._cr.dictfetchall()
        res = {}
        for data in datas:
            employee_id = data['employee']
            doc_type = data['type']
            imig_ids = self.search([('employee_id', '=', employee_id),
                                    ('doc_type_id', '=', doc_type),
                                    ('exp_date', '=', next_date)],
                                   order='exp_date desc')
            if imig_ids and imig_ids.ids:
                if employee_id in res:
                    res[employee_id].append({'type': doc_type,
                                             'exp_date': next_date})
                else:
                    res.update({employee_id: [{'type': doc_type,
                                               'exp_date': next_date}]})
                res.update({'img_id': imig_ids.ids})
                self.generate_send_mail(res)
        return True

    @api.model
    def generate_send_mail(self, res):
        """
        It calls Document Expiry Report and will attache it to mail,
        generate mail body and send it to hr manager and system admin.
        """
        data = {
            'ids': [],
            'model': 'employee.immigration',
            'form': res
        }
        if 'img_id' in res:
            self._ids = res['img_id']
        mail_server_ids = self.env['ir.mail_server'].search([])
        if mail_server_ids:
            mail_server_ids = mail_server_ids.ids
            attachment_ids = []
            groups = [self.env['ir.model.data'
                               ].get_object('hr', 'group_hr_manager')]
            groups += [self.env['ir.model.data'
                                ].get_object('base', 'group_system')]
            email_ids = ''
            for group in groups:
                for user in group.users:
                    email = user.email
                    if email:
                        email_ids += email + ','
            values = {
                'email_to': email_ids,
                'body_html': "Kindly find attached Document Expiry Report.",
                'subject': 'Document Expiry Report',
                'mail_server_id': mail_server_ids[0],
                'auto_delete': True,
            }
            ir_attachment = self.env['ir.attachment']
            msg_id = self.env['mail.mail'].create(values)
            domain = [('report_name', '=',
                       'my_holiday.document_expirey_report')]
            matching_reports = self.env['ir.actions.report'
                                        ].search(domain, limit=1)
            if matching_reports and matching_reports.ids:
                result, report_format = matching_reports.render(self._ids,
                                                                data)
                result = base64.b64encode(result)
                file_name = "Document Expiry Report.pdf"
                if result:
                    attach_data = {
                        'name': file_name,
                        'datas_fname': file_name,
                        'datas': result,
                        'res_model': 'mail.mail',
                        'type': 'binary',
                        'res_id': msg_id.id,
                    }
                    attach_id = ir_attachment.create(attach_data)
                    attachment_ids.append(attach_id.id)
                if attachment_ids:
                    msg_id.write({'attachment_ids': [(6, 0, attachment_ids)]})
            msg_id.send()
        return True
