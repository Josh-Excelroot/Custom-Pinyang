# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    @api.multi
    @api.depends('e_number', 'e_number1', 'e_number2')
    def _get_e_no(self):
        for rec in self:
            e_number = e_number1 = e_number2 = ""
            if rec.e_number:
                e_number = rec.e_number
            if rec.e_number1:
                e_number1 = rec.e_number1
            if rec.e_number2:
                e_number2 = "-" + rec.e_number2
            rec.employer_e_no = e_number + " " + e_number1 + e_number2

    e_number = fields.Char('Company Tax number (E No)', size=1)
    e_number1 = fields.Char("E number 1", size=8)
    e_number2 = fields.Char("E number 2", size=2)
    employer_e_no = fields.Char(
        "Original E Number", compute="_get_e_no", store=True)
    c_number = fields.Char('Employer Tax number (C No)',
                           size=64, help="Income Tax number")
    epf_number = fields.Char('EPF Number', size=8)
    sosco_number = fields.Char('SOCSO Number', size=64)
    zakat_number = fields.Char('Zakat Number', size=64)
    acc_passwd = fields.Char('Account Password', size=64)
    cmp_type = fields.Selection([('type1', 'Self-employed or Business'),
                                 ('type2', 'Partnership'),
                                 ('type3', 'Private Company (Sdn Bhd)'),
                                 ('type4', 'Association'),
                                 ('type5', "Deceased Person's Estate"),
                                 ('type6', 'Trust Body'),
                                 ('type7', "Unit/Real Property Trust"),
                                 ('type8', 'Co-Operative Society')],
                                string="Company Type", default='type3')
    pcb_epf_limit = fields.Float('PCB EPF Limit', default=4000)
    hrdf = fields.Boolean("HRDF")
    accrual_account_id = fields.Many2one('account.account', 'Accrual-Salary')
    accrual_epf_id = fields.Many2one('account.account', 'Accrual-EPF')
    accrual_socso_id = fields.Many2one('account.account', 'Accrual-SOCSO')
    accrual_eis_id = fields.Many2one('account.account', 'Accrual-EIS')
    accrual_pcb_id = fields.Many2one('account.account', 'Accrual-PCB')
    day_of_generate_payslip = fields.Selection([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (
        11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21),
        (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30)],
        string="Month-End Payslip Generation Day")
    enable_pro_data_sal = fields.Boolean(string="Enable Pro Rata Salary")
    working_days_month = fields.Selection([('every_days', 'Every Days'), ('work_days', 'Only Work Days'), ('26', '26'), ('22', '22')], string="Working Days In a Month")
    public_holiday_paid = fields.Boolean(string="Public holidays are not paid")
    accraul_type = fields.Selection([('all_in_one', 'All in one Accrual'), ('diff_accrual', 'Different Accrual')], string="Accrual Type")

    @api.onchange('e_number1', 'e_number2', 'e_number')
    def _check_e_number1(self):
        for number in self:
            e_no = number.e_number
            e_no1 = number.e_number1
            e_no2 = number.e_number2
            if e_no and not e_no.isalpha():
                raise ValidationError('First field must be alphabet in '
                                      'E Number number!')
            if e_no1:
                if not e_no1.isdigit():
                    raise ValidationError('Second field must be numeric'
                                          ' for E number')
                else:
                    e_no = '%0*d' % (8, (int(e_no1)))
                    number.e_number1 = e_no
            if e_no2:
                if not e_no2.isdigit():
                    raise ValidationError('Second field must be numeric '
                                          'for E number')
                else:
                    e_no = '%0*d' % (2, (int(e_no2)))
                    number.e_number2 = e_no

    @api.onchange('hrdf')
    def onchange_hrdf(self):
        employee_ids = self.env['hr.employee'].sudo().search(
            [('active', '=', True), ('company_id.name', '=', self.name)])
        if self.hrdf:
            for employee in employee_ids:
                if employee.residence_status == 'nonresident':
                    employee.write({
                        'hrdf_boolean': False
                    })
                else:
                    employee.write({
                        'hrdf_boolean': True
                    })
        else:
            for employee in employee_ids:
                employee.write({
                    'hrdf_boolean': False
                })
        print(employee_ids)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    salary_account_id = fields.Many2one('account.account', 'Salary Account')
