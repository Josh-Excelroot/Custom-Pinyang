# See LICENSE file for full copyright and licensing details

import pytz
import time
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import json
import requests


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    @api.depends('birthday')
    def compute_age(self):
        today = datetime.today().date()
        for rec in self:
            years = 0
            if rec.birthday and rec.birthday <= today:
                relative_year = relativedelta(today, rec.birthday)
                if relative_year.years:
                    years = relative_year.years
            rec.age = years

    @api.one
    @api.depends('emp_status', 'last_date')
    def _get_rem_days(self):
        today = datetime.today()
        diff_day = 0
        for rec in self:
            if rec.last_date and rec.emp_status == 'in_notice':
                timedelta = rec.last_date - today.date()
                if timedelta and timedelta.days:
                    diff_day = timedelta.days + float(timedelta.seconds
                                                      ) / 86400
                rec.rem_days = diff_day

    @api.one
    def _compute_manager(self):
        cur_user = self.env.user
        allow_to_see_all_tabs = False
        emp_id = self.env['hr.employee'].search([
            ('user_id', '=', self._uid)], limit=1)
        if emp_id:
            if emp_id.department_id and cur_user.company_id and \
                    cur_user.company_id.department_id and \
                    emp_id.department_id.id == \
                    cur_user.company_id.department_id.id:
                allow_to_see_all_tabs = True
            if not allow_to_see_all_tabs:
                self.hr_manager = False
                if self.user_has_groups('hr.group_hr_manager'):
                    self.hr_manager = True
            else:
                self.hr_manager = True

############## Char Fields ##############
    dialect = fields.Char('Dialect', size=32)
    course = fields.Char('Courses Taken', size=64)
    court = fields.Char('Court Information', size=256)
    place_of_birth = fields.Char('Place Of Birth', size=32)
    dismiss = fields.Char('Dismissed Information', size=256)
    bankrupt = fields.Char('Bankrupt Information', size=256)
    other_know = fields.Char('Other Knowledge & Skills', size=64)
    driving_licence = fields.Char('Driving Licence:Class', size=16)
    comp_prog_knw = fields.Char('Computer Programs Knowledge', size=64)
    emp_country = fields.Char('Nationality', size=256)
    emp_old_ic = fields.Char('Old Identification No', size=256)
############## Many2one Fields ##############
    country_id = fields.Many2one('res.country', 'Country')
    emp_city_id = fields.Many2one('employee.city', 'City')
    emp_state_id = fields.Many2one('res.country.state', 'State')
    parent_id = fields.Many2one('hr.employee', 'Direct Manager')
    parent_id2 = fields.Many2one('hr.employee', 'Indirect Manager')
    employee_type_id = fields.Many2one('employee.id.type', 'Type Of ID')
    job_id = fields.Many2one('hr.job', 'Job', domain="[('state','=','open')]")
############## One2many Fields ##############
    training_ids = fields.One2many('employee.training', 'tr_id', 'Training')
    employee_leave_ids = fields.One2many('hr.leave', 'employee_id',
                                         'Leaves')
    history_ids = fields.One2many('employee.history', 'history_id',
                                  'Job History')
    bank_detail_ids = fields.One2many('hr.bank.details', 'bank_emp_id',
                                      'Bank Details')
    immigration_ids = fields.One2many('employee.immigration', 'employee_id',
                                      'Immigration')
############## Date Fields ##############
    last_date = fields.Date('Last Date')
    join_date = fields.Date('Date Joined')
    confirm_date = fields.Date('Date Confirmation')
    issue_date = fields.Date('Passport Issue Date')
    passport_exp_date = fields.Date('Passport Expiry Date')
    evaluation_date = fields.Date('Next Appraisal Date', help="The date of \
                the next appraisal is computed by the appraisal plan's \
                dates (first appraisal + periodicity).")
############## Integer Fields ##############
    typing = fields.Integer('Typing')
    shorthand = fields.Integer('Shorthand')
    age = fields.Integer(compute='compute_age', store=True, string='Age')
    rem_days = fields.Integer(compute='_get_rem_days', method=True,
                              store=True, string='Remaining Days')
############## Boolean Fields ##############
    citizen = fields.Boolean("Is Citizen?")
    court_b = fields.Boolean('Court (Yes)')
    court_no = fields.Boolean('Court (No)')
    car = fields.Boolean('Do you own a car?')
    bankrupt_no = fields.Boolean('Bankrupt (No)')
    bankrupt_b = fields.Boolean('Bankrupt (Yes)')
    dismissed_b = fields.Boolean('Dismissed (Yes)')
    dismissed_no = fields.Boolean('Dismissed (No)')
    physical_stability = fields.Boolean('Physical Stability (Yes)')
    physical_stability_no = fields.Boolean('Physical Disability (No)')
    hr_manager = fields.Boolean(compute='_compute_manager',
                                string='Hr Manager')
    is_daily_notificaiton_email_send = fields.Boolean('Receiving email \
                    notifications of employees who are on leave?',
                                                      default=True)
    is_pending_leave_notificaiton = fields.Boolean('Receiving email \
                        notifications of Pending Leaves Notification Email?')
############## Binary, text and selection Fields ##############
    resume = fields.Binary('Resume')
    reason = fields.Text('Reason')
    about = fields.Text('About Yourself')
    physical = fields.Text('Physical Stability Information')
    emp_status = fields.Selection([('probation', 'Probation'),
                                   ('active', 'Active'),
                                   ('in_notice', 'In notice Period'),
                                   ('terminated', 'Terminated'),
                                   ('inactive', 'Inactive'),
                                   ('promoted', 'Promoted')
                                   ], string='Employment Status',
                                  default='active')
    residence_status = fields.Selection([('resident', 'Resident'),
                                         ('nonresident', 'Non-resident')],
                                        'Residence Status')
    type_of_resident = fields.Selection([
        ('normal', 'Normal'),
        ('knowledgeworker', 'Knowledge worker'),
        ('returningexpertprogram', 'Returning expert program')
    ], string='Type of Resident')
    permanent_resident = fields.Selection([('yes', 'Yes'),
                                           ('no', 'No')],
                                          String='Permanent Resident')
    contributing_epf = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                        string='Contributing EPF',
                                        default='yes')
    empr_epf_condition = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C'),
                                           ('d', 'D'), ('e', 'E'), ('f', 'F')
                                           ], string='Employer EPF Condition')
    pcb_number = fields.Char('PCB Number',
                             help="PCB number format is like \n \
                             XX 12345678-123 (2 capital letters, [space], \
                             eight digit, - , 3 digit)")
    pcb_borner_by_emp = fields.Boolean('PCB Borne By Employer')
    emp_reg_no = fields.Char("Employee's Number")
    emp_epf_rate_less_60 = fields.Selection([('a', '8%'), ('b', '11%')],
                                            default='b',
                                            string='Employee EPF Rate')
    emp_epf_rate_more_60 = fields.Selection([('a', '4%'), ('b', '5.5%')],
                                            default='a',
                                            string='Employee EPF rate < 60')
    emp_add_rate = fields.Selection([('-11', '-11'), ('-10', '-10'), ('-9', '-9'),
                                     ('-9', '-9'), ('-8', '-8'), ('-7', '-7'), ('-6', '-6'),
                                     ('-5', '-5'), ('-4', '-4'), ('-3', '-3'), ('-2', '-2'),
                                     ('-1', '-1'), ('0', '0'), ('1', '1'), ('2', '2'),
                                     ('3', '3'), ('4', '4'), ('5', '5'),
                                     ('6', '6'), ('7', '7'), ('8', '8'),
                                     ('9', '9'), ('10', '10'), ('11', '11'),
                                     ('12', '12'), ('13', '13'), ('14', '14'),
                                     ('15', '15'), ('16', '16'), ('17', '17'),
                                     ('18', '18'), ('19', '19'), ('20', '20')],
                                    string="Additional Rate Employee",
                                    default='0')
    emp_add_rates = fields.Integer('Additional Rate Employee',default=0)
    empr_add_rate = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'),
                                      ('3', '3'), ('4', '4'), ('5', '5'),
                                      ('6', '6'), ('7', '7'), ('8', '8'),
                                      ('9', '9'), ('10', '10'), ('11', '11'),
                                      ('12', '12'), ('13', '13'),
                                      ('14', '14'), ('15', '15'),
                                      ('16', '16'), ('17', '17'),
                                      ('18', '18'), ('19', '19'),
                                      ('20', '20')],
                                     string="Additional Rate Employer",
                                     default='0')
    empr_epf_rate_cond_a = fields.Selection([('a', '12/13%')], default="a",
                                            string="Employer EPF rates")
    empr_epf_rate_cond_b = fields.Selection([('a', '12/13%'),
                                             ('b', '0%(RM5)')],
                                            default="a",
                                            string="Employer EPF rate B")
    empr_epf_rate_cond_c = fields.Selection([('a', '0%(RM5)')], default="a",
                                            string="Employer EPF rate C")
    empr_epf_rate_cond_d = fields.Selection([('a', '6/6.5%')], default="a",
                                            string="Employer EPF rate D")
    empr_epf_rate_cond_e = fields.Selection([('a', '6/6.5%'),
                                             ('b', '0%(RM5)')],
                                            default="b",
                                            string="Employer EPF rate E")
    cessation_date = fields.Date('Cessation Date')
    work_country_id = fields.Many2one('res.country', 'Work Country')
    work_state_id = fields.Many2one('res.country.state', 'Work State')
    cry_frd_leave = fields.Float('Max. Carry Forward Leave', help='Maximum number \
        of Leaves to be carry forwarded!')
    default_leave_allocation = fields.Integer(
        'Default Annual Leave Allocation')
    default_sick_leave = fields.Float(string="Default Sick Leave Allocation")
    default_hospital_leave = fields.Float(
        string="Default Hospital Leave Allocation")
    default_unpaid_leave = fields.Float(
        string="Default Unpaid Leave Allocation")
    default_maternity_leave = fields.Float(
        string="Default Maternity Leave Allocation")
    default_paternity_leave = fields.Float(
        string="Default Paternity Leave Allocation")
    default_mrg_leave = fields.Float(
        string="Default Marriage Leave Allocation")
    leave_entitlement = fields.Many2one('leave.entitlement',string="Leave Entitlement")
    hrdf_boolean = fields.Boolean('HRDF',default=False)

    # @api.onchange('residence_status')
    # def onchange_residence_status(self):
    #     if self.residence_status == 'nonresident':
    #         self.hrdf = False
    # @api.constrains('pcb_number')
    # def _check_pcb_number(self):
    #     for rec in self:
    #         counter = 0
    #         pcb_no = str(rec.pcb_number)
    #         if rec.pcb_number and len(pcb_no) != 15:
    #             raise ValidationError(
    #                 'Please enter valid PCB number !\nFor Ex. DD 12345678-123')
    #             for no in pcb_no:
    #                 counter += 1
    #                 if counter == 1 and not no.isalpha():
    #                     raise ValidationError(
    #                         'First Character must be alphabet in PCB number!')
    #                 elif counter == 2 and not no.isalpha():
    #                     raise ValidationError(
    #                         'Second Character must be alphabet in PCB number!')
    #                 elif counter == 3 and not no.isspace():
    #                     raise ValidationError(
    #                         'Third position must be space in PCB number!')
    #                 elif counter == 4 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Fourth Character must be numeric in PCB number!')
    #                 elif counter == 5 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Fifth Character must be numeric in PCB number!')
    #                 elif counter == 6 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Sixth Character must be numeric in PCB number!')
    #                 elif counter == 7 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Seventh Character must be numeric in PCB number!')
    #                 elif counter == 8 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Eighth Character must be numeric in PCB number!')
    #                 elif counter == 9 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Nineth Character must be numeric in PCB number!')
    #                 elif counter == 10 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Tenth Character must be numeric in PCB number!')
    #                 elif counter == 11 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Eleventh Character must be numeric in PCB number!')
    #                 elif counter == 12 and no != '-':
    #                     raise ValidationError(
    #                         'Twelfth Character must be Dashed(-) in PCB number!')
    #                 elif counter == 13 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Thirteenth Character must be numeric in PCB number!')
    #                 elif counter == 14 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Fourtheenth Character must be numeric in PCB number!')
    #                 elif counter == 15 and not no.isdigit():
    #                     raise ValidationError(
    #                         'Fifteenth Character must be numeric in PCB number!')

    @api.constrains('birthday')
    def _check_emp_birth(self):
        today = datetime.today().date()
        for rec in self:
            if rec.birthday and rec.birthday > today:
                raise ValidationError(_('Please enter valid Birthdate.!'))

    @api.onchange('country_id')
    def check_citizen(self):
        for emp in self:
            if emp.country_id.code == 'MY':
                self.citizen = True
            else:
                self.citizen = False

    @api.onchange('country_id', 'residence_status',
                  'contributing_epf', 'birthday')
    def check_emp_epf_condition(self):
        for emp in self:
            if emp.citizen == True and emp.age <= 60 and \
                    emp.contributing_epf == 'yes' and \
                    emp.residence_status == 'resident':
                emp.empr_epf_condition = 'a'
            elif emp.citizen == False and emp.age <= 60 \
                    and emp.contributing_epf == 'yes' and \
                    emp.residence_status == 'resident':
                emp.empr_epf_condition = 'b'
            elif emp.residence_status == 'nonresident' \
                    and emp.contributing_epf == 'yes':
                emp.empr_epf_condition = 'c'
            elif emp.citizen == True and emp.age >= 60 \
                    and emp.contributing_epf == 'yes':
                emp.empr_epf_condition = 'd'
            elif emp.citizen == False and emp.age >= 60 and \
                    emp.contributing_epf == 'yes':
                emp.empr_epf_condition = 'e'
            elif emp.contributing_epf == 'no':
                emp.empr_epf_condition = 'f'
            else:
                emp.empr_epf_condition = 'f'

    @api.multi
    def hr_toggle_active(self):
        for record in self:
            record.active = not record.active
            if record.active:
                record.emp_status = 'active'
            else:
                record.emp_status = 'inactive'

# ============================================
#        HR Employee :On Change Methods
# ============================================

    @api.onchange('cessation_date', 'emp_status')
    def onchange_employee_cessation_date(self):
        if self.emp_status in ['in_notice', 'terminated']:
            contratc_id = self.env['hr.contract'].search([
                ('employee_id', '=', self._origin.id)])
            if contratc_id and self.cessation_date:
                contratc_id.write({'date_end': self.cessation_date})

    @api.onchange('active')
    def onchange_emp_active(self):
        if self.active is True:
            self.emp_status = 'active'
        else:
            self.emp_status = 'inactive'

    @api.onchange('emp_status')
    def onchange_employee_status(self):
        if self.emp_status == 'inactive':
            self.active = False
        else:
            self.active = True

    @api.onchange('physical_stability')
    def onchange_health_yes(self):
        self.physical_stability_no = True
        if self.physical_stability:
            self.physical_stability_no = False

    @api.onchange('physical_stability_no')
    def onchange_health_no(self):
        self.physical_stability = True
        if self.physical_stability_no:
            self.physical_stability = False

    @api.onchange('court_b')
    def onchange_court_yes(self):
        self.court_no = True
        if self.court_b:
            self.court_no = False

    @api.onchange('court_no')
    def onchange_court_no(self):
        self.court_b = True
        if self.court_no:
            self.court_b = False

    @api.onchange('dismissed_b')
    def onchange_dismissed_yes(self):
        self.dismissed_no = True
        if self.dismissed_b:
            self.dismissed_no = False

    @api.onchange('dismissed_no')
    def onchange_dismissed_no(self):
        self.dismissed_b = True
        if self.dismissed_no:
            self.dismissed_b = False

    @api.onchange('bankrupt_b')
    def onchange_bankrupt_yes(self):
        self.bankrupt_no = True
        if self.bankrupt_b:
            self.bankrupt_no = False

    @api.onchange('bankrupt_no')
    def onchange_bankrupt_no(self):
        self.bankrupt_b = True
        if self.bankrupt_no:
            self.bankrupt_b = False

# ============================================
#        HR Employee: ORM Methods
# ============================================

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['employee_leave_ids'] = False
        default['child_ids'] = False
        return super(HrEmployee, self).copy(default=default)

    @api.multi
    def write(self, vals):
        if vals.get('job_id') or vals.get('emp_status') or \
                vals.get('join_date') or vals.get('confirm_date'):
            for emp_rec in self:
                emp_vals = {
                    'job_id': vals.get('job_id') or emp_rec.job_id.id,
                    'history_id': emp_rec.id,
                    'user_id': self._uid,
                    'emp_status': vals.get('emp_status', emp_rec.emp_status),
                    'join_date': vals.get('join_date', emp_rec.join_date),
                    'confirm_date': vals.get('confirm_date',
                                             emp_rec.confirm_date)
                }
                self.env['employee.history'].create(emp_vals)
        if 'active' in vals and self.user_id and self.user_id.id:
            self.user_id.write({'active': vals.get('active')})
        return super(HrEmployee, self).write(vals)

    @api.model
    def create(self, vals):
        employee_id = super(HrEmployee, self).create(vals)
        if vals.get('job_id') or vals.get('emp_status') or \
                vals.get('join_date') or vals.get('confirm_date'):
            self.env['employee.history'].create({
                'job_id': vals.get('job_id'),
                'history_id': employee_id.id,
                'user_id': self._uid,
                'emp_status': vals.get('emp_status', 'active'),
                'join_date': vals.get('join_date', False),
                'confirm_date': vals.get('confirm_date', False)
            })
        active = vals.get('active', False)
        user_obj = self.env['res.users']
        if vals.get('user_id') and not active:
            user_obj.browse(vals.get('user_id')).write({'active': active})
        return employee_id

# ============================================
#        HR Employee: scheduler Methods
# ============================================

    def check_time_zone(self, t_date):
        t_date = str(t_date)
        dt_value = t_date
        if t_date:
            timez = 'Asia/Kuala_Lumpur'
            if self._context and 'tz' in self._context and self._context.get('tz') != False:
                timez = self._context.get('tz')
            rec_date_from = datetime.strptime(
                t_date, DEFAULT_SERVER_DATE_FORMAT)
            src_tz = pytz.timezone('UTC')
            dst_tz = pytz.timezone(timez)
            src_dt = src_tz.localize(rec_date_from, is_dst=True)
            dt_value = src_dt.astimezone(dst_tz)
            dt_value = dt_value.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return dt_value


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        result = super(ResPartner, self).default_get(fields)
        result['lang'] = False
        return result


class EmployeeDocument(models.Model):

    _name = 'employee.document'
    _rec_name = 'document'
    _description = 'Attachment'

    employee_doc_id = fields.Many2one('hr.leave', 'Holiday', invisible=True)
    document_attachment = fields.Binary('Attachment Data')
    document = fields.Char("Documents", size=256)
    file_url = fields.Char('File URL')
    file_id = fields.Char('File ID')

    def create_folder_on_drive(self, folder_name, model_obj=None):
        url = 'https://www.googleapis.com/drive/v3/files'
        g_drive = self.env['google.drive.config']
        access_token = GoogleDrive.get_access_token(g_drive)
        headers = {
            'Authorization': 'Bearer {}'.format(access_token),
            'Content-Type': 'application/json'
        }
        folder_id = self.env['multi.folder.drive'].search([('model_id.model', '=', model_obj)], limit=1).folder_id
        parent_id = folder_id
        if not parent_id:
            parent_id = self.env.user.company_id.drive_folder_id
        metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = requests.post(url, headers=headers, data=json.dumps(metadata))
        if response.status_code == 200:
            des = response.text.encode("utf-8")
            d = json.loads(des)
            return d.get('id')

    def download_document(self):
        return {'url': self.file_url,
                'type': 'ir.actions.act_url',
                'target': 'new'}

    def upload_document(self):
        if self.file_url and self.document_attachment:
            self.env['google.file.upload'].delete_from_google_drive(self.file_id)
        active_model = self._context.get('rec_model') or self._context.get('params')['model']
        active_id = self._context.get('rec_id')
        folder = self.env.user.company_id.folder_type
        parent_id = self.env.user.company_id.drive_folder_id
        if folder == 'single_folder':
            parent_id = parent_id
        if folder == 'multi_folder':
            m_folder_id = self.env['multi.folder.drive'].search([('model_id.model', '=', active_model)], limit=1)
            parent_id = m_folder_id.folder_id if m_folder_id.folder_id else parent_id
        if folder == 'record_wise_folder':
            rec_id = self.env[active_model].browse(active_id)
            folder = self.env['ir.model.fields'].search([('model_id.model', '=', active_model), ('name', '=', 'folder_id')])
            if not folder:
                raise ValidationError(_("Development Error\nPlease define folder_id field in %s" % active_model))
            if rec_id and rec_id.folder_id:
                parent_id = rec_id.folder_id
            else:
                parent_id = self.create_folder_on_drive(
                    rec_id.display_name, active_model)
                rec_id.folder_id = parent_id
        if parent_id:
            file_url = self.env['google.file.upload'].upload_to_google_drive(self.document, self.document_attachment, parent_id)
            if file_url:
                self.document_attachment = False
                self.file_url = file_url.get('url')
                self.file_id = file_url.get('file_id')

    def unlink(self):
        for rec in self:
            if rec.file_id:
                self.env['google.file.upload'].delete_from_google_drive(rec.file_id)
        return super(EmployeeDocument, self).unlink()


class DocumentType(models.Model):

    _name = 'document.type'
    _description = 'Document Type'

    name = fields.Char('Name', size=64, required=True)


class EmployeeImegration(models.Model):

    _name = 'employee.immigration'
    _description = 'Employee Immigration'
    _rec_name = 'documents'

    @api.constrains('issue_date', 'exp_date')
    def check_document_date(self):
        if self.issue_date > self.exp_date:
            raise ValidationError(
                _("Document Issue date must be anterior then Expiry date"))

    documents = fields.Char("Documents", size=256)
    number = fields.Char('Number', size=256)
    employee_id = fields.Many2one('hr.employee', 'Employee Name')
    exp_date = fields.Date('Expiry Date')
    issue_date = fields.Date('Issue Date')
    eligible_status = fields.Char('Eligible Status', size=256)
    issue_by = fields.Many2one('res.country', 'Issue By')
    eligible_review_date = fields.Date('Eligible Review Date')
    doc_type_id = fields.Many2one('document.type', 'Document Type')
    comments = fields.Text("Comments")
    attach_document = fields.Binary('Attach Document')

    @api.onchange('issue_date', 'exp_date')
    def check_document_start_end_date(self):
        if self.issue_date and self.exp_date and \
                self.issue_date > self.exp_date:
            raise ValidationError(
                _("Document Issue date must be anterior then Expiry date."))


class EmployeeCity(models.Model):

    _name = "employee.city"
    _description = "Employee City"

    name = fields.Char('City Name', size=64, required=True)
    code = fields.Char('City Code', size=64, required=True)
    state_id = fields.Many2one('res.country.state', 'State', required=True)


class HrBankDetails(models.Model):

    _name = 'hr.bank.details'
    _rec_name = 'bank_name'
    _description = "Employee Bank Details"

    bank_name = fields.Char('Name Of Bank', size=256)
    bank_code = fields.Char('Bank Code', size=256)
    bank_ac_no = fields.Char('Bank Account Number', size=256)
    bank_emp_id = fields.Many2one('hr.employee', 'Bank Detail')
    branch_code = fields.Char('Branch Code', size=256)
    beneficiary_name = fields.Char('Beneficiary Name', size=256)


class EmployeeIdType(models.Model):

    _name = 'employee.id.type'
    _description = "Employee Id Type"

    name = fields.Char("EP", size=256, required=True)
    s_pass = fields.Selection([('skilled', 'Skilled'),
                               ('unskilled', 'Un Skilled')], 'S Pass')
    wp = fields.Selection([('skilled', 'Skilled'),
                           ('unskilled', 'Un Skilled')], 'Wp')


class EmployeeTraining(models.Model):

    _name = 'employee.training'
    _description = 'Employee Training'
    _rec_name = 'tr_title'

    tr_id = fields.Many2one('hr.employee', 'Employee')
    tr_title = fields.Char('Title of TRAINING/WORKSHOP', size=64,
                           required=True)
    tr_institution = fields.Char('Institution', size=64)
    tr_date = fields.Date('Date')
    comments = fields.Text('Comments')
    training_attachment = fields.Binary('Attachment Data')


class EmployeeHistory(models.Model):

    _name = 'employee.history'
    _description = 'Employee History'
    _rec_name = 'history_id'

    history_id = fields.Many2one('hr.employee', 'History')
    job_id = fields.Many2one('hr.job', 'Job title', readonly=True, store=True)
    date_changed = fields.Datetime('Date Changed', readonly=True,
                                   default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    user_id = fields.Many2one('res.users', "Changed By", readonly=True)
    emp_status = fields.Selection([('probation', 'Probation'),
                                   ('active', 'Active'),
                                   ('in_notice', 'In notice Period'),
                                   ('terminated', 'Terminated'),
                                   ('inactive', 'Inactive'),
                                   ('promoted', 'Promoted')],
                                  'Employment Status')
    join_date = fields.Date('Joined Date')
    confirm_date = fields.Date('Date of Confirmation')
    cessation_date = fields.Date('Cessation Date')


class EmployeeNews(models.Model):

    _name = 'employee.news'
    _description = 'Employee News'
    _rec_name = 'subject'

    subject = fields.Char('Subject', size=255, required=True)
    description = fields.Text('Description')
    date = fields.Datetime('Date')
    department_ids = fields.Many2many('hr.department', 'department_news_rel',
                                      'parent_id', 'news_id', 'Manager News')
    user_ids = fields.Many2many('res.users', 'user_news_rel',
                                'id', 'user_ids',
                                'User News')

# ============================================
#        Employee News: Button Methods
# ============================================

    @api.multi
    def news_update(self):
        emp_obj = self.env["hr.employee"]
        obj_mail_server = self.env['ir.mail_server']
        mail_server_ids = obj_mail_server.search([])
        if not mail_server_ids and mail_server_ids.ids:
            raise ValidationError(_('No mail outgoing mail server specified!')
                                  )
        mail_server_record = mail_server_ids[0]
        email_list = []
        for news in self:
            if news.department_ids and news.department_ids.ids:
                dep_name_ids = [department.id for
                                department in news.department_ids]
                emp_ids = emp_obj.search([('department_id',
                                           'in',
                                           dep_name_ids)])
                for emp_rec in emp_ids:
                    if emp_rec.work_email:
                        email_list.append(emp_rec.work_email)
                    elif emp_rec.user_id and emp_rec.user_id.login:
                        email_list.append(emp_rec.user_id.login)
                if not email_list:
                    raise ValidationError(_("Email not found in employee !"))
            elif news.user_ids:
                for user in news.user_ids:
                    if user.login:
                        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\."
                                    "([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",
                                    user.login) != None:
                            email_list.append(user.login)
                        else:
                            raise ValidationError(_('Invalid Email for %s user'
                                                    ' Please enter a valid '
                                                    'email address'
                                                    ) % (user.login))
                if not email_list:
                    raise ValidationError(_("Email not found in users !"))
            else:
                emp_ids = emp_obj.search([])
                for employee in emp_ids:
                    if employee.work_email:
                        email_list.append(employee.work_email)
                    elif employee.user_id and employee.user_id.login:
                        email_list.append(employee.user_id.login)
                if not email_list:
                    raise ValidationError(_("Email not defined!"))
            if news.date:
                rec_date = news.date
                body = 'Hi,<br/><br/> '\
                    'This is a news update from <b>%s</b> posted at %s<br/>'\
                    '<br/>'\
                    '%s <br/><br/>'\
                    'Thank you.' % (self._cr.dbname,
                                    rec_date.strftime('%d-%m-%Y %H:%M:%S'),
                                    news.description)
                if not mail_server_record.smtp_user:
                    raise ValidationError(_("Please configure User in "
                                            "outgoing mail server!"))
                message = obj_mail_server.build_email(
                    email_from=mail_server_record.smtp_user,
                    email_to=email_list,
                    subject='Notification for news update.',
                    body=body,
                    body_alternative=body,
                    email_cc=None,
                    email_bcc=None,
                    reply_to=mail_server_record.smtp_user,
                    attachments=None,
                    references=None,
                    object_id=None,
                    subtype='html',  # It can be plain or html
                    subtype_alternative=None,
                    headers=None)
                obj_mail_server.send_email(message=message,
                                           mail_server_id=mail_server_record.id)
                return True


class ResCompany(models.Model):

    _inherit = 'res.company'

    department_id = fields.Many2one('hr.department', 'Department')
