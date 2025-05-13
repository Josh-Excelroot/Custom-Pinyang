# See LICENSE file for full copyright and licensing details

import xlwt
import base64
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.tools import ustr

LEAVE_STATE = {
    'draft': 'New',
    'confirm': 'Waiting Pre-Approval',
    'refuse': 'Refused',
    'validate1': 'Waiting Final Approval',
    'validate': 'Approved',
    'cancel': 'Cancelled'}
LEAVE_REQUEST = {
    'remove': 'Leave Request',
    'add': 'Allocation Request'
    }
PAYSLIP_STATE = {
    "draft": "Draft",
    "verify": "Waiting",
    "done": "Done",
    "cancel": "Rejected"}


class ExportEmployeeDataRecordXls(models.TransientModel):

    _name = 'export.employee.data.record.xls'
    _description = "Export Employee Data Record"

    file = fields.Binary(
        "Click On Download Link To Download File", readonly=True)
    name = fields.Char("Name", size=32, readonly=True, invisible=True,
                       default="Employee Summary.xls")


class ExportEmployeeSummaryWiz(models.TransientModel):

    _name = 'export.employee.summary.wiz'
    _description = "Employee Summary Wizard"

    @api.onchange('employee_information')
    def onchange_employee_information(self):
        if self.employee_information is True and \
                self._context.get('employee_information') is True:
            self.user_id = True
            self.department = True
            self.indirect_manager = True
            self.direct_manager = True
            self.active = True
        elif self.employee_information is False and \
                self._context.get('employee_information') is True:
            self.user_id = False
            self.department = False
            self.indirect_manager = False
            self.direct_manager = False
            self.active = False

    @api.onchange('user_id', 'department', 'indirect_manager',
                  'direct_manager', 'active')
    def onchange_emp_info(self):
        if self.user_id is False or self.department is False or \
            self.indirect_manager is False or self.direct_manager is False or \
                self.active is False and self.employee_information is True:
            self.employee_information = False
        if self.user_id is True and self.department is True and \
            self.indirect_manager is True and self.direct_manager is True and \
                self.active is True and self.employee_information is False:
            self.employee_information = True

    @api.onchange('education_information')
    def onchange_education_information(self):
        if self.education_information is True and \
                self._context.get('education_information') is True:
            self.com_prog_know = True
            self.courses = True
            self.other_know = True
            self.shorthand = True
            self.typing = True
        elif self.education_information is False and self._context.get('education_information') is True:
            self.com_prog_know = False
            self.courses = False
            self.other_know = False
            self.shorthand = False
            self.typing = False

    @api.onchange('com_prog_know', 'courses', 'other_know',
                  'shorthand', 'typing')
    def onchange_edu_info(self):
        if self.com_prog_know == False or self.courses == False or \
        self.other_know == False or self.shorthand == False or \
        self.typing == False and self.education_information == True:
            self.education_information = False
        if self.com_prog_know == True and self.courses == True and \
        self.other_know == True and self.shorthand == True and \
        self.typing == True and self.education_information == False:
            self.education_information = True
            
    @api.onchange('job_information')
    def onchange_job_information(self):
        if self.job_information == True and \
            self._context.get('job_information') == True:
            self.job_title = True
            self.join_date = True
            self.date_changed = True
            self.date_confirm_month = True
            self.emp_status = True
            self.confirm_date = True
            self.changed_by = True
        elif self.job_information == False and \
            self._context.get('job_information') == True:
            self.job_title = False
            self.join_date = False
            self.date_changed = False
            self.date_confirm_month = False
            self.emp_status = False
            self.confirm_date = False
            self.changed_by = False
            
    @api.onchange('job_title', 'join_date', 'date_changed',
                  'date_confirm_month', 'emp_status', 'confirm_date',
                  'changed_by')
    def onchange_job_info(self):
        if self.job_title == False or self.join_date == False or \
        self.date_changed == False or self.date_confirm_month == False or \
        self.emp_status == False or self.confirm_date == False or \
        self.changed_by == False and self.job_information == True:
            self.job_information = False
        if self.job_title == True and self.join_date == True and \
        self.date_changed == True and self.date_confirm_month == True and \
        self.emp_status == True and self.confirm_date == True and \
        self.changed_by == True and self.job_information == False:
            self.job_information = True
            
    @api.onchange('emp_extra_information')
    def onchange_emp_extra_information(self):
        if self.emp_extra_information == True and \
            self._context.get('emp_extra_information') == True:
            self.health_condition = True
            self.bankrupt = True
            self.suspend_employment = True
            self.court_law = True
            self.about = True
        elif self.emp_extra_information == False and \
            self._context.get('emp_extra_information') == True:
            self.health_condition = False
            self.bankrupt = False
            self.suspend_employment = False
            self.court_law = False
            self.about = False
            
    @api.onchange('health_condition', 'bankrupt', 'suspend_employment',
                  'court_law', 'about')
    def onchange_emp_extra_info(self):
        if self.health_condition == False or self.bankrupt == False or \
        self.suspend_employment == False or self.court_law == False or \
        self.about == False and self.emp_extra_information == True:
            self.emp_extra_information = False
        if self.health_condition == True and self.bankrupt == True and \
        self.suspend_employment == True and self.court_law == True and \
        self.about == True and self.emp_extra_information == False:
            self.emp_extra_information = True
            
    @api.onchange('emp_notification_info')
    def onchange_emp_notification_info(self):
        if self.emp_notification_info == True and \
            self._context.get('emp_notification_info') == True:
            self.emp_noty_leave = True
            self.pending_levae_noty = True
        elif self.emp_notification_info == False and \
            self._context.get('emp_notification_info') == True:
            self.emp_noty_leave = False
            self.pending_levae_noty = False
            
    @api.onchange('emp_noty_leave', 'pending_levae_noty')
    def onchange_emp_noti_info(self):
        if self.emp_noty_leave == False or self.pending_levae_noty == False \
        and self.emp_notification_info == True:
            self.emp_notification_info = False
        if self.emp_noty_leave == True and self.pending_levae_noty == True and \
        self.emp_notification_info == False:
            self.emp_notification_info = True
            
    @api.onchange('emp_payroll_info')
    def onchange_emp_payroll_info(self):
        if self.emp_payroll_info == True and \
            self._context.get('emp_payroll_info') == True:
            self.payslip = True
            self.contract = True
        elif self.emp_payroll_info == False and \
            self._context.get('emp_payroll_info') == True:
            self.payslip = False
            self.contract = False
            
    @api.onchange('payslip', 'contract')
    def onchange_payroll_info(self):
        if self.payslip == False or self.contract == False \
        and self.emp_payroll_info == True:
            self.emp_payroll_info = False
        if self.payslip == True and self.contract == True and \
        self.emp_payroll_info == False:
            self.emp_payroll_info = True

    @api.onchange('personal_information')
    def onchange_personal_information(self):
        if self.personal_information == True and \
            self._context.get('personal_information') == True:
            self.identification_id = True
            self.passport_id = True
            self.gender = True
            self.martial = True
            self.nationality = True
            self.dob = True
            self.pob = True
            self.age = True
            self.home_address = True
            self.country_id = True
            self.state_id = True
            self.city_id = True
            self.phone = True
            self.mobile = True
            self.email = True
            self.dialet = True
            self.driving_licence = True
            self.own_car = True
            self.emp_type_id = True
        elif self.personal_information == False and \
            self._context.get('personal_information') == True:
            self.identification_id = False
            self.passport_id = False
            self.gender = False
            self.martial = False
            self.nationality = False
            self.dob = False
            self.pob = False
            self.age = False
            self.home_address = False
            self.country_id = False
            self.state_id = False
            self.city_id = False
            self.phone = False
            self.mobile = False
            self.email = False
            self.dialet = False
            self.driving_licence = False
            self.own_car = False
            self.emp_type_id = False
            
    @api.onchange('identification_id', 'passport_id', 'gender',
                  'martial', 'nationality', 'dob', 'pob', 'age',
                  'home_address', 'country_id', 'state_id', 'city_id', 'phone',
                  'mobile', 'email', 'dialet', 'driving_licence', 'own_car',
                  'emp_type_id')
    def onchange_personal_info(self):
        if self.identification_id == False or self.passport_id == False or \
        self.gender == False or self.martial == False or \
        self.nationality == False or \
        self.dob == False or self.pob == False or \
        self.age == False or self.home_address == False or \
        self.country_id == False or self.state_id == False or \
        self.city_id == False or self.phone == False or \
        self.mobile == False or self.email == False or \
        self.dialet == False or self.driving_licence == False or \
        self.own_car == False or self.emp_type_id == False \
        and self.personal_information == True:
            self.personal_information = False
        if self.identification_id == True and self.passport_id == True and \
        self.gender == True and self.martial == True and \
        self.nationality == True and \
        self.dob == True and self.pob == True and \
        self.age == True and self.home_address == True and \
        self.country_id == True and self.state_id == True and \
        self.city_id == True and self.phone == True and \
        self.mobile == True and self.email == True and \
        self.dialet == True and self.driving_licence == True and \
        self.own_car == True and self.emp_type_id == True and \
        self.personal_information == False:
            self.personal_information = True

    employee_ids = fields.Many2many('hr.employee',
                                   'ihrms_hr_employee_export_summary_rel',
                                   'emp_id', 'employee_id', 'Employee Name',
                                   required=False)
    user_id = fields.Boolean('User')
    active = fields.Boolean('Active')
    department = fields.Boolean('Department')
    direct_manager = fields.Boolean('Direct Manager')
    indirect_manager = fields.Boolean('Indirect Manager')
    personal_information = fields.Boolean('Select All')
    employee_information = fields.Boolean('Select All')
    education_information = fields.Boolean('Select All')
    job_information = fields.Boolean('Select All')
    emp_extra_information = fields.Boolean('Select All')
    emp_notification_info = fields.Boolean('Select All')
    emp_payroll_info = fields.Boolean('Select All')
    identification_id = fields.Boolean('Identification')
    passport_id = fields.Boolean('Passport')
    gender = fields.Boolean('Gender')
    martial = fields.Boolean('Martial Status')
    nationality = fields.Boolean('Nationality')
    dob = fields.Boolean('Date Of Birth')
    pob = fields.Boolean('Place Of Birth')
    age = fields.Boolean('Age')
    home_address = fields.Boolean('Home Address')
    country_id = fields.Boolean('Country')
    state_id = fields.Boolean('State')
    city_id = fields.Boolean('City')
    phone = fields.Boolean('Phone')
    mobile = fields.Boolean('Mobile')
    email = fields.Boolean('Email')
    dialet = fields.Boolean('Dialet')
    driving_licence = fields.Boolean('Driving Licence Class')
    own_car = fields.Boolean('Do Your Own Car')
    emp_type_id = fields.Boolean('Type Of ID')
    com_prog_know = fields.Boolean('Computer Program Knowledge')
    shorthand = fields.Boolean('Shorthand')
    courses = fields.Boolean('Courses Taken')
    typing = fields.Boolean('Typing')
    other_know = fields.Boolean('Other Knowledge & Skills')
    job_title = fields.Boolean('Job Title')
    emp_status = fields.Boolean('Employment Status')
    join_date = fields.Boolean('Joined Date')
    confirm_date = fields.Boolean('Confirmation Date')
    date_changed = fields.Boolean('Date Changed')
    changed_by = fields.Boolean('Changed By')
    date_confirm_month = fields.Boolean('Date Confirm Month')
    category_ids = fields.Boolean('Categories')
    immigration_ids = fields.Boolean('Immigration')
    tarining_ids = fields.Boolean('Training Workshop')
    emp_leave_ids = fields.Boolean('Leave History')
    health_condition = fields.Boolean('Are you suffering from any physical \
        disability or illness that requires you to be medication for a \
        prolonged period?')
    court_law = fields.Boolean('Have you ever been convicted in a court of \
        law in any country?')
    suspend_employment = fields.Boolean('Have you ever been dismissed or \
        suspended from employement?')
    bankrupt = fields.Boolean('Have you ever been declared a bankrupt?')
    about = fields.Boolean('About Yourself')
    emp_noty_leave = fields.Boolean('Receiving email notifications of \
        employees who are on leave?')
    pending_levae_noty = fields.Boolean('Receiving email notifications of \
        Pending Leaves Notification Email?')
    receive_mail_manager = fields.Boolean('Receiving email notifications of \
        2nd Reminder to Direct / Indirect Managers?')
    bank_detail_ids = fields.Boolean('Bank Details')
    notes = fields.Boolean('Notes')
    payslip = fields.Boolean('Payslips')
    contract = fields.Boolean('Contract')
    
    @api.constrains('user_id', 'active', 'department', 'direct_manager',
                    'indirect_manager', 'identification_id', 'passport_id',
                    'gender', 'martial', 'nationality', 'dob', 'pob', 'age',
                    'home_address', 'country_id', 'state_id', 'city_id',
                    'phone', 'mobile', 'email', 'dialet', 'driving_licence',
                    'own_car', 'emp_type_id', 'com_prog_know',
                    'courses', 'other_know', 'shorthand', 'typing', 'job_title',
                    'join_date', 'date_changed', 'date_confirm_month',
                    'emp_status', 'confirm_date', 'changed_by',
                    'category_ids', 'immigration_ids', 'tarining_ids',
                    'emp_leave_ids', 'health_condition', 'bankrupt',
                    'suspend_employment', 'court_law', 'about',
                    'bank_detail_ids',
                    'notes', 'emp_noty_leave', 'pending_levae_noty',
                    'receive_mail_manager', 'payslip', 'contract')
    def onchange_emp_detail(self):
        if not self.user_id and not self.active and not self.direct_manager and not self.indirect_manager and not self.identification_id and not self.passport_id and not self.gender and \
        not self.martial and not self.nationality and not self.dob and not self.pob and not self.age and not self.home_address and not self.country_id\
        and not self.dob and not self.pob and not self.age and not self.home_address and not self.country_id and not self.state_id and not self.city_id and not self.phone \
        and not self.state_id and not self.city_id and not self.phone and not self.mobile and not self.email and not self.dialet \
        and not self.driving_licence and not self.own_car and not self.emp_type_id and not self.com_prog_know and not self.courses and not self.other_know \
        and not self.shorthand and not self.typing and not self.join_date and not self.date_changed and not self.date_confirm_month and not self.emp_status \
        and not self.confirm_date and not self.changed_by and not self.category_ids and not self.immigration_ids and not self.tarining_ids and not self.emp_leave_ids \
        and not self.health_condition and not self.bankrupt and not self.suspend_employment and not self.court_law and not self.about and not self.bank_detail_ids \
        and not self.notes and not self.emp_noty_leave and not self.pending_levae_noty and not self.receive_mail_manager and not self.payslip and not self.contract:
            raise ValidationError("Please select atleast one from \n *Employee Information \n * Personal Information \n * Educational Information\
            \n * Job \n *Categories \n * Immigration \n * Training \n * Leave History \n * Extra Information \n * Bank Details \n * Notes.")

    @api.multi
    def export_employee_summary_xls(self):
        context = dict(self._context)
        if context is None:
            context = {}
        data = self.read()[0]
        context.update({'datas': data})
        workbook = xlwt.Workbook()
        font = xlwt.Font()
        font.bold = True
        user_lang = self.env['res.users'].browse(self._uid).lang
        lang_ids = self.env['res.lang'].search([('code', '=', user_lang)])
        date_format = "%d/%m/%Y"
        month_year_format = "%m/%Y"
        if lang_ids:
            date_format = lang_ids[0].date_format
        header = xlwt.easyxf('font: name Arial, bold on,height 200; align: wrap off;')
        style = xlwt.easyxf('align: wrap off')
        number_format = xlwt.easyxf('align: wrap off')
        number_format.num_format_str = '#,##0.00'
        personal_information = False
        emp_payslip_row = emp_contract_row = emp_note_row = emp_edu_skill_row = emp_extra_info_row = emp_notification_row = \
            emp_info_row = emp_per_info_row = emp_bank_row = emp_leave_row = emp_training_row = emp_job_row = \
            emp_immigration_row = emp_categories_row = emp_info_col = \
            emp_per_info_col = emp_notification_col = emp_extra_info_col = 0
        if not context.get('datas')['employee_ids']:
            raise Warning('Please Select Employee')
        if context and context.get('datas') and context.get('datas')['employee_ids']:
            if context.get('datas')['user_id'] or context.get('datas')['active'] or context.get('datas')['department'] or \
                 context.get('datas')['direct_manager'] or context.get('datas')['indirect_manager']:
                emp_info_ws = workbook.add_sheet('Employee Information')
                emp_info_ws.col(emp_info_col).width = 6000
                emp_info_ws.write(emp_info_row, emp_info_col, 'Employee Name', header)
                if context.get('datas')['user_id']:
                    emp_info_col += 1
                    emp_info_ws.col(emp_info_col).width = 5000
                    emp_info_ws.write(emp_info_row, emp_info_col, 'User', header)
                if context.get('datas')['active']:
                    emp_info_col += 1
                    emp_info_ws.col(emp_info_col).width = 5000
                    emp_info_ws.write(emp_info_row, emp_info_col, 'Active', header)
                if context.get('datas')['department']:
                    emp_info_col += 1
                    emp_info_ws.col(emp_info_col).width = 5000
                    emp_info_ws.write(emp_info_row, emp_info_col, 'Department', header)
                if context.get('datas')['direct_manager']:
                    emp_info_col += 1
                    emp_info_ws.col(emp_info_col).width = 5000
                    emp_info_ws.write(emp_info_row, emp_info_col, 'Direct Manager', header)
                if context.get('datas')['indirect_manager']:
                    emp_info_col += 1
                    emp_info_ws.col(emp_info_col).width = 5000
                    emp_info_ws.write(emp_info_row, emp_info_col, 'Indirect Manager', header)

            # Employee Personal Information
            if context.get('datas').get('identification_id') or context.get('datas').get('passport_id')\
                or context.get('datas').get('gender') or context.get('datas').get('martial') or context.get('datas').get('nationality') \
                or context.get('datas').get('dob') or context.get('datas').get('pob') or context.get('datas').get('age') \
                or context.get('datas').get('home_address') or context.get('datas').get('country_id') or context.get('datas').get('state_id') \
                or context.get('datas').get('city_id') or context.get('datas').get('phone') or context.get('datas').get('mobile') \
                or context.get('datas').get('email') or context.get('datas').get('dialet') \
                or context.get('datas').get('driving_licence') or context.get('datas').get('own_car') \
                or context.get('datas').get('emp_type_id'):
                personal_information = True
            if personal_information:
                emp_personal_info_ws = workbook.add_sheet('Personal Information')
                emp_per_info_col = 0
                emp_personal_info_ws.col(emp_per_info_col).width = 6000
                emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Employee Name : ', header)
                if context.get('datas')['identification_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Identification', header)
                if context.get('datas')['passport_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Passport No', header)
                if context.get('datas')['gender']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Gender', header)
                if context.get('datas')['martial']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Marital Status', header)
                if context.get('datas')['nationality']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Nationality', header)
                if context.get('datas')['dob']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Birthdate', header)
                if context.get('datas')['pob']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Place Of Birht', header)
                if context.get('datas')['age']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Age', header)
                if context.get('datas')['home_address']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Home Address', header)
                if context.get('datas')['country_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Country', header)
                if context.get('datas')['state_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'State', header)
                if context.get('datas')['city_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'City', header)
                if context.get('datas')['phone']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Phone', header)
                if context.get('datas')['mobile']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Mobile', header)
                if context.get('datas')['email']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Email', header)
                if context.get('datas')['dialet']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Dialet', header)
                if context.get('datas')['driving_licence']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Driving Licence', header)
                if context.get('datas')['own_car']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Car', header)
                if context.get('datas')['emp_type_id']:
                    emp_per_info_col += 1
                    emp_personal_info_ws.col(emp_per_info_col).width = 6000
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, 'Type Of ID', header)
            # Notification
            if context.get('datas')['emp_noty_leave'] or context.get('datas')['pending_levae_noty'] :  # or context.get('datas')['receive_mail_manager']:
                emp_notification_ws = workbook.add_sheet('Notification')
                emp_notification_ws.col(emp_notification_col).width = 6000
                emp_notification_ws.write(emp_notification_row, emp_notification_col, 'Employee Name', header)
                if context.get('datas')['emp_noty_leave']:
                    emp_notification_col += 1
                    emp_notification_ws.col(emp_notification_col).width = 15000
                    emp_notification_ws.write(emp_notification_row, emp_notification_col, 'Receiving email notifications of employees who are on leave? :', header)
                if context.get('datas')['pending_levae_noty']:
                    emp_notification_col += 1
                    emp_notification_ws.col(emp_notification_col).width = 15000
                    emp_notification_ws.write(emp_notification_row, emp_notification_col, 'Receiving email notifications of Pending Leaves Notification Email? :', header)
            # Extra Information
            if context.get('datas')['health_condition'] or context.get('datas')['bankrupt'] or context.get('datas')['suspend_employment'] or context.get('datas')['court_law'] or context.get('datas')['about']:
                emp_extra_info_ws = workbook.add_sheet('Extra Information')
                emp_extra_info_ws.col(emp_extra_info_col).width = 6000
                emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'Employee Name', header)
                if context.get('datas')['health_condition']:
                    emp_extra_info_col += 1
                    emp_extra_info_ws.col(emp_extra_info_col).width = 15000
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'Are you suffering from any physical disability or illness that requires you to be medication for a prolonged period? ', header)
                if context.get('datas')['bankrupt']:
                    emp_extra_info_col += 1
                    emp_extra_info_ws.col(emp_extra_info_col).width = 15000
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'Have you ever been declared a bankrupt?', header)
                if context.get('datas')['suspend_employment']:
                    emp_extra_info_col += 1
                    emp_extra_info_ws.col(emp_extra_info_col).width = 15000
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'Have you ever been dismissed or suspended from employement? ', header)
                if context.get('datas')['court_law']:
                    emp_extra_info_col += 1
                    emp_extra_info_ws.col(emp_extra_info_col).width = 15000
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'Have you ever been convicted in a court of law in any country? ', header)
                if context.get('datas')['about']:
                    emp_extra_info_col += 1
                    emp_extra_info_ws.col(emp_extra_info_col).width = 15000
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, 'About Yourself', header)
            if context.get('datas')['com_prog_know'] or context.get('datas')['shorthand'] or context.get('datas')['courses'] or context.get('datas')['typing'] or context.get('datas')['other_know']:
                emp_edu_skill_ws = workbook.add_sheet('Computer Knowledge and Skills')
                emp_edu_skill_ws.col(0).width = 6000
                emp_edu_skill_ws.write(emp_edu_skill_row, 0, 'Employee Name', header)
                if context.get('datas')['com_prog_know']:
                    emp_edu_skill_ws.col(1).width = 6000
                    emp_edu_skill_ws.write(emp_edu_skill_row, 1, 'Computer Program Knowledge ', header)
                if context.get('datas')['shorthand']:
                    emp_edu_skill_ws.col(2).width = 6000
                    emp_edu_skill_ws.write(emp_edu_skill_row, 2, 'Shorthand', header)
                if context.get('datas')['courses']:
                    emp_edu_skill_ws.col(3).width = 6000
                    emp_edu_skill_ws.write(emp_edu_skill_row, 3, 'Courses ', header)
                if context.get('datas')['typing']:
                    emp_edu_skill_ws.col(4).width = 6000
                    emp_edu_skill_ws.write(emp_edu_skill_row, 4, 'Typing', header)
                if context.get('datas')['other_know']:
                    emp_edu_skill_ws.col(5).width = 6000
                    emp_edu_skill_ws.write(emp_edu_skill_row, 5, 'Other Knowledge & Skills', header)
            if context.get('datas')['job_title'] or context.get('datas')['emp_status'] \
                or context.get('datas')['join_date'] \
                or context.get('datas')['confirm_date'] \
                or context.get('datas')['date_changed'] \
                or context.get('datas')['changed_by'] \
                or context.get('datas')['date_confirm_month']:
                emp_job_ws = workbook.add_sheet('Job')
                emp_job_col = 0
                emp_job_ws.col(emp_job_col).width = 6000
                emp_job_ws.write(emp_job_row, emp_job_col, 'Employee Name', header)
                if context.get('datas')['job_title']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Job Title', header)
                if context.get('datas')['emp_status']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Employment Status', header)
                if context.get('datas')['join_date']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Join Date', header)
                if context.get('datas')['confirm_date']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Date Confirmation', header)
                if context.get('datas')['date_changed']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Date Changed', header)
                if context.get('datas')['changed_by']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Changed By', header)
                if context.get('datas')['date_confirm_month']:
                    emp_job_col += 1
                    emp_job_ws.col(emp_job_col).width = 6000
                    emp_job_ws.write(emp_job_row, emp_job_col, 'Date Confirmation Month', header)
            if context.get('datas')['category_ids']:
                emp_categories_ws = workbook.add_sheet('Categories')
                emp_categories_ws.col(0).width = 6000
                emp_categories_ws.col(1).width = 6000
                emp_categories_ws.col(2).width = 6000
                emp_categories_ws.write(emp_categories_row, 0, 'Employee Name', header)
                emp_categories_ws.write(emp_categories_row, 1, 'Category', header)
            # Immigration
            if context.get('datas')['immigration_ids']:
                emp_immigration_ws = workbook.add_sheet('Immigration')
                emp_immigration_ws.col(0).width = 6000
                emp_immigration_ws.col(1).width = 6000
                emp_immigration_ws.col(2).width = 6000
                emp_immigration_ws.col(3).width = 6000
                emp_immigration_ws.col(4).width = 6000
                emp_immigration_ws.col(5).width = 6000
                emp_immigration_ws.col(6).width = 6000
                emp_immigration_ws.col(7).width = 6000
                emp_immigration_ws.col(8).width = 6000
                emp_immigration_ws.write(emp_immigration_row, 0, 'Employee Name', header)
                emp_immigration_ws.write(emp_immigration_row, 1, 'Document', header)
                emp_immigration_ws.write(emp_immigration_row, 2, 'Number', header)
                emp_immigration_ws.write(emp_immigration_row, 3, 'Issue Date', header)
                emp_immigration_ws.write(emp_immigration_row, 4, 'Expiry Date', header)
                emp_immigration_ws.write(emp_immigration_row, 5, 'Eligible Status', header)
                emp_immigration_ws.write(emp_immigration_row, 6, 'Eligible Review Date', header)
                emp_immigration_ws.write(emp_immigration_row, 7, 'Issue By', header)
                emp_immigration_ws.write(emp_immigration_row, 8, 'Comment', header)

            # Trainig Workshop
            if context.get('datas')['tarining_ids']:
                emp_training_ws = workbook.add_sheet('Training Workshop')
                emp_training_ws.col(0).width = 6000
                emp_training_ws.col(1).width = 6000
                emp_training_ws.col(2).width = 6000
                emp_training_ws.col(3).width = 6000
                emp_training_ws.col(4).width = 15000
                emp_training_ws.write(emp_training_row, 0, 'Employee Name', header)
                emp_training_ws.write(emp_training_row, 1, 'Training Workshop', header)
                emp_training_ws.write(emp_training_row, 2, 'Institution', header)
                emp_training_ws.write(emp_training_row, 3, 'Date', header)
                emp_training_ws.write(emp_training_row, 4, 'Comment', header)

            # Leave History
            if context.get('datas')['emp_leave_ids']:
                emp_leave_ws = workbook.add_sheet('Leave History')
                emp_leave_ws.col(0).width = 6000
                emp_leave_ws.col(1).width = 9000
                emp_leave_ws.col(2).width = 3000
                emp_leave_ws.col(3).width = 6000
                emp_leave_ws.col(4).width = 6000
                emp_leave_ws.col(5).width = 6000
                emp_leave_ws.col(6).width = 6000
                emp_leave_ws.write(emp_leave_row, 0, 'Employee Name', header)
                emp_leave_ws.write(emp_leave_row, 1, 'Description', header)
                emp_leave_ws.write(emp_leave_row, 2, 'Year', header)
                emp_leave_ws.write(emp_leave_row, 3, 'Start Date', header)
                emp_leave_ws.write(emp_leave_row, 4, 'End Date', header)
                emp_leave_ws.write(emp_leave_row, 5, 'Request Type', header)
                emp_leave_ws.write(emp_leave_row, 6, 'Leave Type', header)
                emp_leave_ws.write(emp_leave_row, 7, 'Number Of Days', header)
                emp_leave_ws.write(emp_leave_row, 8, 'State', header)
                emp_leave_ws.write(emp_leave_row, 9, 'Reason', header)
            # Bank Details
            if context.get('datas')['bank_detail_ids']:
                emp_bank_ws = workbook.add_sheet('Bank Details')
                emp_bank_ws.col(0).width = 6000
                emp_bank_ws.col(1).width = 6000
                emp_bank_ws.col(2).width = 6000
                emp_bank_ws.col(3).width = 6000
                emp_bank_ws.col(4).width = 6000
                emp_bank_ws.write(emp_bank_row, 0, 'Employee Name', header)
                emp_bank_ws.write(emp_bank_row, 1, 'Name Of Bank', header)
                emp_bank_ws.write(emp_bank_row, 2, 'Bank Code', header)
                emp_bank_ws.write(emp_bank_row, 3, 'Branch Code', header)
                emp_bank_ws.write(emp_bank_row, 4, 'Bank Account Number', header)

            # Notes
            if context.get('datas')['notes']:
                emp_note_ws = workbook.add_sheet('Notes')
                emp_note_ws.col(0).width = 6000
                emp_note_ws.col(1).width = 15000
                emp_note_ws.write(emp_note_row, 0, 'Employee Name', header)
                emp_note_ws.write(emp_note_row, 1, 'Note', header)

            # Payslip
            if context.get('datas')['payslip']:
                emp_payslip_ws = workbook.add_sheet('Payroll - Payslips')
                emp_payslip_ws.col(0).width = 6000
                emp_payslip_ws.col(2).width = 16000
                emp_payslip_ws.write(emp_payslip_row, 0, 'Employee Name', header)
                emp_payslip_ws.write(emp_payslip_row, 1, 'Reference', header)
                emp_payslip_ws.write(emp_payslip_row, 2, 'Description', header)
                emp_payslip_ws.write(emp_payslip_row, 3, 'Date from', header)
                emp_payslip_ws.write(emp_payslip_row, 4, 'Date to', header)
                emp_payslip_ws.write(emp_payslip_row, 5, 'Amount', header)
                emp_payslip_ws.write(emp_payslip_row, 6, 'State', header)

            # Contract
            if context.get('datas')['contract']:
                emp_contract_ws = workbook.add_sheet('Contract')
                emp_contract_ws.col(0).width = 6000
                emp_contract_ws.col(1).width = 6000
                emp_contract_ws.col(5).width = 6000
                emp_contract_ws.write(emp_contract_row, 0, 'Employee Name', header)
                emp_contract_ws.write(emp_contract_row, 1, 'Reference', header)
                emp_contract_ws.write(emp_contract_row, 2, 'Wage', header)
                emp_contract_ws.write(emp_contract_row, 3, 'Start date', header)
                emp_contract_ws.write(emp_contract_row, 4, 'End date', header)
                emp_contract_ws.write(emp_contract_row, 5, 'Salary structure', header)

            for emp in self.env['hr.employee'].browse(context.get('datas')['employee_ids']):
                if context.get('datas')['user_id'] or context.get('datas')['active'] or context.get('datas')['department'] \
                        or context.get('datas')['direct_manager'] or context.get('datas')['indirect_manager']:
                    emp_info_row += 1
                    emp_info_col = emp_per_info_col = 0
                    emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.name or ''), style)
                    if context.get('datas')['user_id']:
                        emp_info_col += 1
                        emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.user_id.name or ''), style)
                    if context.get('datas')['active']:
                        emp_info_col += 1
                        emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.active or ''), style)
                    if context.get('datas')['department']:
                        emp_info_col += 1
                        emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.department_id.name or ''), style)
                    if context.get('datas')['direct_manager']:
                        emp_info_col += 1
                        emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.parent_id.name or ''), style)
                    if context.get('datas')['indirect_manager']:
                        emp_info_col += 1
                        emp_info_ws.write(emp_info_row, emp_info_col, ustr(emp.parent_id2.name or ''), style)
                # Employee Personal Information
                if personal_information:
                    emp_per_info_row += 1
                    emp_per_info_col = 0
                    emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.name or ''), style)
                    if context.get('datas')['identification_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.identification_id or ''), style)
                    if context.get('datas')['passport_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.passport_id or ''), style)

                    if context.get('datas')['gender']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.gender or ''), style)
                    if context.get('datas')['martial']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.marital or ''), style)
                    if context.get('datas')['nationality']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.emp_country or ''), style)
                    if context.get('datas')['dob']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.birthday or ''), style)
                    if context.get('datas')['pob']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.place_of_birth or ''), style)
                    if context.get('datas')['age']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.age or ''), style)

                    if context.get('datas')['home_address']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.address_home_id.name or ''), style)
                    if context.get('datas')['country_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.country_id.name or ''), style)
                    if context.get('datas')['state_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.emp_state_id.name or ''), style)
                    if context.get('datas')['city_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.emp_city_id.name or ''), style)
                    if context.get('datas')['phone']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.work_phone or ''), style)
                    if context.get('datas')['mobile']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.mobile_phone or ''), style)
                    if context.get('datas')['email']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.work_email or ''), style)

                    if context.get('datas')['dialet']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.dialect or ''), style)
                    if context.get('datas')['driving_licence']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.driving_licence or ''), style)
                    if context.get('datas')['own_car']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.car or ''), style)
                    if context.get('datas')['emp_type_id']:
                        emp_per_info_col += 1
                        emp_personal_info_ws.write(emp_per_info_row, emp_per_info_col, ustr(emp.employee_type_id.name or ''), style)
                # Notification
                if context.get('datas')['emp_noty_leave'] or context.get('datas')['pending_levae_noty']:  # or context.get('datas')['receive_mail_manager']:
                    emp_notification_row += 1
                    emp_notification_col = 0
                    emp_notification_ws.write(emp_notification_row, emp_notification_col, ustr(emp.name or ''), style)
                    if context.get('datas')['emp_noty_leave']:
                        emp_notification_col += 1
                        emp_notification_ws.write(emp_notification_row, emp_notification_col, ustr(emp.is_daily_notificaiton_email_send or ''), style)
                    if context.get('datas')['pending_levae_noty']:
                        emp_notification_col += 1
                        emp_notification_ws.write(emp_notification_row, emp_notification_col, ustr(emp.is_pending_leave_notificaiton or ''), style)
                # Extra Information
                if context.get('datas')['health_condition'] or context.get('datas')['bankrupt'] or context.get('datas')['suspend_employment'] or context.get('datas')['court_law'] or context.get('datas')['about']:
                    emp_extra_info_col = 0
                    emp_extra_info_row += 1
                    emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(emp.name or ''), style)
                    if context.get('datas')['health_condition']:
                        emp_extra_info_col += 1
                        helath_condition = ''
                        if emp.physical_stability:
                            helath_condition = 'Yes'
                        if emp.physical_stability_no:
                            helath_condition = 'No'
                        emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(helath_condition or ''), style)
                    if context.get('datas')['bankrupt']:
                        emp_extra_info_col += 1
                        bankrupt = ''
                        if emp.bankrupt_b:
                            bankrupt = 'Yes'
                        if emp.bankrupt_no:
                            bankrupt = 'No'
                        emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(bankrupt or ''), style)
                    if context.get('datas')['suspend_employment']:
                        emp_extra_info_col += 1
                        supspend = ''
                        if emp.dismissed_b:
                            supspend = 'Yes'
                        if emp.dismissed_no:
                            supspend = 'No'
                        emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(supspend or ''), style)
                    if context.get('datas')['court_law']:
                        emp_extra_info_col += 1
                        court = ''
                        if emp.court_b:
                            court = "Yes"
                        if emp.court_no:
                            court = "No"
                        emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(court or ''), style)
                    if context.get('datas')['about']:
                        emp_extra_info_col += 1
                        emp_extra_info_ws.write(emp_extra_info_row, emp_extra_info_col, ustr(emp.about or ''), style)

                # Educational Information
                if context.get('datas')['com_prog_know'] or context.get('datas')['shorthand'] or context.get('datas')['courses'] or context.get('datas')['typing'] or context.get('datas')['other_know']:
                    emp_edu_skill_row += 1
                    emp_edu_skill_ws.write(emp_edu_skill_row, 0, ustr(emp.name or ''), style)
                    if context.get('datas')['com_prog_know']:
                        emp_edu_skill_ws.write(emp_edu_skill_row, 1, ustr(emp.comp_prog_knw or ''), style)
                    if context.get('datas')['shorthand']:
                        emp_edu_skill_ws.write(emp_edu_skill_row, 2, ustr(emp.shorthand or ''), style)
                    if context.get('datas')['courses']:
                        emp_edu_skill_ws.write(emp_edu_skill_row, 3, ustr(emp.course or ''), style)
                    if context.get('datas')['typing']:
                        emp_edu_skill_ws.write(emp_edu_skill_row, 4, ustr(emp.typing or ''), style)
                    if context.get('datas')['other_know']:
                        emp_edu_skill_ws.write(emp_edu_skill_row, 5, ustr(emp.other_know or ''), style)
                # Job
                if context.get('datas')['job_title'] or context.get('datas')['emp_status'] \
                    or context.get('datas')['join_date'] \
                    or context.get('datas')['confirm_date'] \
                    or context.get('datas')['date_changed'] \
                    or context.get('datas')['changed_by'] \
                    or context.get('datas')['date_confirm_month']:
                    for job in emp.history_ids:
                        emp_job_col = 0
                        emp_job_row += 1
                        emp_job_ws.write(emp_job_row, emp_job_col, ustr(emp.name or ''), style)
                        if context.get('datas')['job_title']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, ustr(job.job_id.name or ''), style)
                        if context.get('datas')['emp_status']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, ustr(job.emp_status or ''), style)
                        if context.get('datas')['join_date']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, job.join_date and job.join_date.strftime(date_format) or '', style)
                        if context.get('datas')['confirm_date']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, job.confirm_date and job.confirm_date.strftime(date_format) or '', style)
                        if context.get('datas')['date_changed']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, job.date_changed and job.date_changed.strftime(date_format) or '', style)
                        if context.get('datas')['changed_by']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, ustr(job.user_id.name or ''), style)
                        if context.get('datas')['date_confirm_month']:
                            emp_job_col += 1
                            emp_job_ws.write(emp_job_row, emp_job_col, job.confirm_date and job.confirm_date.strftime(month_year_format) or '', style)
                # Categories
                if context.get('datas')['category_ids']:
                    for category in emp.category_ids:
                        emp_categories_row += 1
                        emp_categories_ws.write(emp_categories_row, 0, ustr(emp.name or ''), style)
                        emp_categories_ws.write(emp_categories_row, 1, ustr(category.name or ''), style)
                # Immigration
                if context.get('datas')['immigration_ids']:
                    for immigration in emp.immigration_ids:
                        emp_immigration_row += 1
                        emp_immigration_ws.write(emp_immigration_row, 0, ustr(emp.name or ''), style)
                        emp_immigration_ws.write(emp_immigration_row, 1, ustr(immigration.documents or ''), style)
                        emp_immigration_ws.write(emp_immigration_row, 2, ustr(immigration.number or ''), style)
                        emp_immigration_ws.write(emp_immigration_row, 3, immigration.issue_date and immigration.issue_date.strftime(date_format) or '', style)
                        emp_immigration_ws.write(emp_immigration_row, 4, immigration.exp_date and immigration.exp_date.strftime(date_format) or '', style)
                        emp_immigration_ws.write(emp_immigration_row, 5, ustr(immigration.eligible_status or ''), style)
                        emp_immigration_ws.write(emp_immigration_row, 6, immigration.eligible_review_date and immigration.eligible_review_date.strftime(date_format) or '', style)
                        emp_immigration_ws.write(emp_immigration_row, 7, ustr(immigration.issue_by or ''), style)
                        emp_immigration_ws.write(emp_immigration_row, 8, ustr(immigration.comments or ''), style)
                # Trainig Workshop
                if context.get('datas')['tarining_ids']:
                    for training in emp.training_ids:
                        emp_training_row += 1
                        emp_training_ws.write(emp_training_row, 0, ustr(emp.name or ''), style)
                        emp_training_ws.write(emp_training_row, 1, ustr(training.tr_title or ''), style)
                        emp_training_ws.write(emp_training_row, 2, ustr(training.tr_institution or ''), style)
                        emp_training_ws.write(emp_training_row, 3, training.tr_date and training.tr_date.strftime(date_format) or '', style)
                        emp_training_ws.write(emp_training_row, 4, ustr(training.comments or ''), style)
                # Leave History
                if context.get('datas')['emp_leave_ids']:
                    for leave in emp.employee_leave_ids:
                        emp_leave_row += 1
                        emp_leave_ws.write(emp_leave_row, 0, ustr(emp.name or ''), style)
                        emp_leave_ws.write(emp_leave_row, 1, ustr(leave.name or ''), style)
                        emp_leave_ws.write(emp_leave_row, 2, ustr(leave.hr_year_id and leave.hr_year_id.name or ''), style)
                        emp_leave_ws.write(emp_leave_row, 3, leave.date_from and leave.date_from.date().strftime(date_format) or '', style)
                        emp_leave_ws.write(emp_leave_row, 4, leave.date_to and leave.date_to.date().strftime(date_format) or '', style)
                        emp_leave_ws.write(emp_leave_row, 5, ustr('Leave Request'), style)
                        emp_leave_ws.write(emp_leave_row, 6, ustr(leave.holiday_status_id.code or ''), style)
                        emp_leave_ws.write(emp_leave_row, 7, ustr(leave.number_of_days or ''), style)
                        emp_leave_ws.write(emp_leave_row, 8, ustr(LEAVE_STATE.get(leave.state, '')), style)
                        emp_leave_ws.write(emp_leave_row, 9, ustr(leave.rejection or ''), style)
                # Bank Details
                if context.get('datas')['bank_detail_ids']:
                    for bank in emp.bank_detail_ids:
                        emp_bank_row += 1
                        emp_bank_ws.write(emp_bank_row, 0, ustr(emp.name or ''), style)
                        emp_bank_ws.write(emp_bank_row, 1, ustr(bank.bank_name or ''), style)
                        emp_bank_ws.write(emp_bank_row, 2, ustr(bank.bank_code or ''), style)
                        emp_bank_ws.write(emp_bank_row, 3, ustr(bank.branch_code or ''), style)
                        emp_bank_ws.write(emp_bank_row, 4, ustr(bank.bank_ac_no or ''), style)

                # Notes
                if context.get('datas')['notes']:
                    emp_note_row += 1
                    emp_note_ws.write(emp_note_row, 0, ustr(emp.name or ''), style)
                    emp_note_ws.write(emp_note_row, 1, ustr(emp.notes or ''), style)

                # Payslip
                if context.get('datas')['payslip']:
                    payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', emp.id)])
                    for payslip in payslip_ids:
                        net_amount = 0.0
                        for line in payslip.line_ids:
                            if line.code == "NET":
                                net_amount = line.amount
                        emp_payslip_row += 1
                        emp_payslip_ws.write(emp_payslip_row, 0, ustr(emp.name or ''), style)
                        emp_payslip_ws.write(emp_payslip_row, 1, ustr(payslip.number or ''), style)
                        emp_payslip_ws.write(emp_payslip_row, 2, ustr(payslip.name or ''), style)
                        emp_payslip_ws.write(emp_payslip_row, 3, payslip.date_from and payslip.date_from.strftime(date_format) or '', style)
                        emp_payslip_ws.write(emp_payslip_row, 4, payslip.date_to and payslip.date_to.strftime(date_format) or '', style)
                        emp_payslip_ws.write(emp_payslip_row, 5, net_amount, number_format)
                        emp_payslip_ws.write(emp_payslip_row, 6, ustr(PAYSLIP_STATE.get(payslip.state, '')), style)

                if context.get('datas')['contract']:
                    contract_ids = self.env['hr.contract'].search([('employee_id', '=', emp.id)])
                    for contract in contract_ids:
                        emp_contract_row += 1
                        emp_contract_ws.write(emp_contract_row, 0, ustr(emp.name or ''), style)
                        emp_contract_ws.write(emp_contract_row, 1, ustr(contract.name or ''), style)
                        emp_contract_ws.write(emp_contract_row, 2, contract.wage, number_format)
                        emp_contract_ws.write(emp_contract_row, 3, contract.date_start and contract.date_start.strftime(date_format) or '', style)
                        emp_contract_ws.write(emp_contract_row, 4, contract.date_end and contract.date_end.strftime(date_format) or '', style)
                        emp_contract_ws.write(emp_contract_row, 5, ustr(contract.struct_id and contract.struct_id.name or ''), style)
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.b64encode(data)
        # Create record for Binary data.
        emp_excell_rec = self.env['export.employee.data.record.xls'].create(
            {
             'name': 'Employee Summary.xls',
             'file': res,
             })

        return {
            'name': _('Employee Summary'),
            'res_id': emp_excell_rec.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'export.employee.data.record.xls',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
