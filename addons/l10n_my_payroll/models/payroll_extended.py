# See LICENSE file for full copyright and licensing details

import calendar
import math
from pytz import timezone
import datetime as dt
from datetime import datetime, time, date
from dateutil import parser, rrule, relativedelta
from dateutil.relativedelta import relativedelta as relative

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


def get_default_month(self):
    return datetime.now().month


def get_default_year(self):
    return datetime.now().year


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'

    id = fields.Integer('ID', readonly=True)
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)],company_dependent=True)
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)],company_dependent=True)

    @api.multi
    def _compute_rule(self, localdict):
        if localdict is None or not localdict:
            localdict = {}
        employee_ids = self.env['hr.employee'].sudo().search_count([
            ('country_id.code', '=', 'MY')])
        localdict.update({
            'datetime': datetime,
            'math': math,
            'malay_emp_ids': employee_ids or 0})
        return super(HrSalaryRule, self)._compute_rule(localdict)


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'
    _order = 'date_from desc,employee_name asc'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    def view_pdf_right(self):
        pass

    @api.multi
    def write(self, vals):
        res = super(HrPayslip, self).write(vals)
        return res


    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee
            that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the
        # date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from),
                    '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), '|', '|'] + \
            clause_1 + clause_2 + clause_3
        contract_ids = self.env['hr.contract'].search(clause_final)
        contract_id = contract_ids and contract_ids[0] and contract_ids[0].id
        return [contract_id]

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        for rec in res:
            if rec.get('code') == 'INPUTCP38':
                rec.update({'sequence': 1})
        return res

    @api.multi
    @api.depends('employee_id.user_id', 'date_from', 'date_to', 'employee_id',
                 'contract_id.prev_empl_add', 'contract_id.prev_empl_ded',
                 'contract_id.prev_empl_epf', 'contract_id.prev_empl_epf',
                 'contract_id.exp11')
    def _get_salary_computation_ytd_total(self):
        for data in self:
            total_ytd_gross = 0.0
            total_ytd_epf_employee = 0.0
            total_ytd_pcb = 0.0
            total_ytd_pcb_ded = 0.0
            total_ytd_zakat = 0.0
            remaining_month = 0
            if data.contract_id and data.contract_id.id and \
                    data.contract_id.is_prev_employments:
                year = data.contract_id.date_start.strftime('%Y')
                cont_end_date = datetime.strptime('%s-12-31' % (year),
                                                  DEFAULT_SERVER_DATE_FORMAT)
                if data.date_from > cont_end_date.date():
                    if data.contract_id.prev_empl_add:
                        total_ytd_gross += data.contract_id.prev_empl_add
                    if data.contract_id.prev_empl_epf:
                        total_ytd_epf_employee += data.contract_id.prev_empl_epf
                    if data.contract_id.exp11:
                        total_ytd_epf_employee += data.contract_id.exp11
                    if data.contract_id.prev_empl_ded:
                        total_ytd_pcb_ded += data.contract_id.prev_empl_ded
                    if data.contract_id.prev_empl_PCB:
                        total_ytd_pcb += data.contract_id.prev_empl_PCB
                    if data.contract_id.prev_empl_zakat:
                        total_ytd_zakat += data.contract_id.prev_empl_zakat
            if data.date_from:
                month = data.date_from.strftime('%m')
                remaining_month = 12 - int(month)
                year = data.date_from.strftime('%Y')
                year_start_date = '%s-01-01' % (year)
                year_end_date = datetime.strptime('%s-12-31' % (year),
                                                  DEFAULT_SERVER_DATE_FORMAT)
                last_day_of_previous_month = (
                    data.date_from - relativedelta.relativedelta(days=1)).\
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
                payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', '=', data.employee_id.id),
                    ('date_from', '>=', year_start_date),
                    ('date_from', '<=', last_day_of_previous_month),
                ])
                for payslip in payslip_ids:
                    if payslip.date_from < year_end_date.date():
                        for line in payslip.line_ids:
                            if line.code in ('GROSS', 'DIR_FEES'):
                                total_ytd_gross += line.amount
    #                       Add benifit in kinds in YTD gross amount
                            if line.category_id and line.category_id.code == 'BIK':
                                total_ytd_gross += line.amount
                            if line.code == 'DEPFE':
                                total_ytd_epf_employee += line.amount
                            if line.code == 'PCBCURRMONTH':
                                total_ytd_pcb += line.amount
                            if line.code == 'PCBAPPROVEDDEDUCTIONS':
                                total_ytd_pcb_ded += line.amount
                            if line.code in ('ZAKAT', 'ZAKAT_TP1'):
                                total_ytd_zakat += line.amount
                        for in_line in payslip.input_line_ids:
                            if in_line.code == 'LHDNDED11':
                                total_ytd_epf_employee += in_line.amount
            data.total_ytd_gross = total_ytd_gross or 0.0
            data.total_ytd_epf_employee = total_ytd_epf_employee or 0.0
            data.total_ytd_pcb = total_ytd_pcb or 0.0
            data.remaining_month = remaining_month or 0
            data.total_ytd_pcb_ded = total_ytd_pcb_ded
            data.total_ytd_zakat = total_ytd_zakat

    # @api.multi
    # @api.depends('employee_id.user_id', 'date_from', 'date_to', 'employee_id',
    #              'input_line_ids', 'contract_id.alw1', 'contract_id.alw2',
    #              'contract_id.alw5', 'contract_id', 'input_line_ids.amount')
    # def _get_non_tax_alw_ytd_total(self):
    #     for data in self:
    #         total_ytd_alw1 = 0.0
    #         total_ytd_alw2 = 0.0
    #         total_ytd_alw5 = 0.0
    #         if data.contract_id and data.contract_id.id and \
    #                 data.contract_id.is_prev_employments:
    #             year = data.contract_id.date_start.strftime('%Y')
    #             cont_end_date = datetime.strptime('%s-12-31' % (year),
    #                                               DEFAULT_SERVER_DATE_FORMAT)
    #             if data.date_from <= cont_end_date.date():
    #                 if data.contract_id.alw1:
    #                     total_ytd_alw1 += data.contract_id.alw1
    #                 if data.contract_id.alw2:
    #                     total_ytd_alw2 += data.contract_id.alw2
    #                 if data.contract_id.alw5:
    #                     total_ytd_alw5 += data.contract_id.alw5
    #         year = data.date_from.strftime('%Y')
    #         year_start_date = datetime.strptime('%s-01-01' % (year),
    #                                             DEFAULT_SERVER_DATE_FORMAT)
    #         year_end_date = datetime.strptime('%s-12-31' % (year),
    #                                           DEFAULT_SERVER_DATE_FORMAT)
    #         last_day_of_previous_month = data.date_from - \
    #             relativedelta.relativedelta(days=1)
    #         payslip_ids = self.env['hr.payslip'].search([
    #             ('employee_id', '=', data.employee_id.id),
    #             ('date_from', '>=', year_start_date.date()),
    #             ('date_from', '<=', last_day_of_previous_month),
    #         ])
    #         for payslip in payslip_ids:
    #             if payslip.date_from < year_end_date.date():
    #                 for line in payslip.line_ids:
    #                     if line.code == 'ALW_NONTAX_1':
    #                         total_ytd_alw1 += line.amount
    #                     if line.code == 'ALW_NONTAX_2':
    #                         total_ytd_alw2 += line.amount
    #                     if line.code == 'ALW_NONTAX_3':
    #                         total_ytd_alw5 += line.amount
    #         if total_ytd_alw1 > 6000:
    #             raise ValidationError(_("Non Taxable Allowances \nYou can not \
    #             apply for Petrol or Travelling allowance expense \
    #             more then 6000."))
    #         else:
    #             data.total_ytd_alw1 = total_ytd_alw1 or 0.0
    #         if total_ytd_alw2 > 2400:
    #             raise ValidationError(_("Non Taxable Allowances \nYou can \
    #             not apply for Child care allowance more then 2400."))
    #         else:
    #             data.total_ytd_alw2 = total_ytd_alw2 or 0.0
    #         if total_ytd_alw5 > 2000:
    #             raise ValidationError(_("Non Taxable Allowances \nYou can \
    #             not apply for Employee Perquisite more then 2000."))
    #         else:
    #             data.total_ytd_alw5 = total_ytd_alw5 or 0.0

    @api.multi
    @api.depends('employee_id.user_id', 'date_from', 'date_to', 'employee_id',
                 'input_line_ids', 'contract_id.exp1', 'contract_id.exp2',
                 'contract_id.exp3', 'contract_id.exp4', 'contract_id.exp5',
                 'contract_id.exp6', 'contract_id.exp7', 'contract_id.exp8',
                 'contract_id.exp9', 'contract_id.exp10', 'contract_id.exp12',
                 'contract_id.exp13', 'contract_id.exp14', 'contract_id.exp15',
                 'contract_id.exp16', 'contract_id.exp17', 'contract_id.exp18',
                 'contract_id.exp19', 'contract_id', 'input_line_ids.amount')
    def _get_medical_computation_ytd_total(self):
        for data in self:
            total_ytd_medical = total_ytd_supp_eqp = total_ytd_edu_fees = 0.0
            total_ytd_md_serious_dis = total_ytd_medical_exam = 0.0
            total_ytd_purchase_book = total_ytd_pur_per_comp = 0.0
            total_ytd_SSPN = total_ytd_sport_equp = 0.0
            total_ytd_former_wife = 0.0
            total_ytd_edmd_ins = total_ytd_annuity_premium = 0.0
            total_ytd_int_house_loan = total_ytd_sosco_pay = 0.0
            total_ytd_tp1_add_1 = total_ytd_tp1_add_2 = 0.0
            total_ytd_lh17 = total_ytd_lh18 = 0.0
            exp1 = exp2 = exp3 = exp4 = exp5 = exp6 = exp7 = exp8 = exp9 = 0.0
            exp10 = exp12 = exp13 = exp14 = exp15 = exp16 = exp17 = 0.0
            exp18 = exp19 = 0.0
            if data.date_from:
                year = data.date_from.strftime('%Y')
                year_start_date = '%s-01-01' % (year)
                year_end_date = datetime.strptime('%s-12-31' % (year),
                                                  DEFAULT_SERVER_DATE_FORMAT)
                payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', '=', data.employee_id.id),
                    ('date_from', '>=', year_start_date),
                    ('date_from', '<=', data.date_from)])
                for payslip in payslip_ids:
                    if payslip.date_from < year_end_date.date():
                        for line in payslip.input_line_ids:
                            if line.code == 'LHDNDED01':
                                total_ytd_medical += line.amount
                            if line.code == 'LHDNDED02':
                                total_ytd_supp_eqp += line.amount
                            if line.code == 'LHDNDED03':
                                total_ytd_edu_fees += line.amount
                            if line.code == 'LHDNDED04':
                                total_ytd_md_serious_dis += line.amount
                            if line.code == 'LHDNDED05':
                                total_ytd_medical_exam += line.amount
                            if line.code == 'LHDNDED06':
                                total_ytd_purchase_book += line.amount
                            if line.code == 'LHDNDED07':
                                total_ytd_pur_per_comp += line.amount
                            if line.code == 'LHDNDED08':
                                total_ytd_SSPN += line.amount
                            if line.code == 'LHDNDED09':
                                total_ytd_sport_equp += line.amount
                            if line.code == 'LHDNDED10':
                                total_ytd_former_wife += line.amount
    #                         if line.code == 'LHDNDED11':
    #                             total_ytd_life_ins += line.amount
                            if line.code == 'LHDNDED12':
                                total_ytd_edmd_ins += line.amount
                            if line.code == 'LHDNDED13':
                                total_ytd_annuity_premium += line.amount
                            if line.code == 'LHDNDED14':
                                total_ytd_int_house_loan += line.amount
                            if line.code == 'LHDNDED15':
                                total_ytd_tp1_add_1 += line.amount
                            if line.code == 'LHDNDED16':
                                total_ytd_tp1_add_2 += line.amount
                            if line.code == 'LHDNDED17':
                                total_ytd_lh17 += line.amount
                            if line.code == 'LHDNDED18':
                                total_ytd_lh18 += line.amount
                            if line.code == 'LHDNDED19':
                                total_ytd_sosco_pay += line.amount
            if data.contract_id and data.contract_id.id and \
                    data.contract_id.is_prev_employments:
                year = data.contract_id.date_start.strftime('%Y')
                cont_end_date = datetime.strptime(
                    '%s-12-31' % (year), DEFAULT_SERVER_DATE_FORMAT)
                if data.date_from <= cont_end_date.date():
                    exp1 = data.contract_id.exp1
                    exp2 = data.contract_id.exp2
                    exp3 = data.contract_id.exp3
                    exp4 = data.contract_id.exp4
                    exp5 = data.contract_id.exp5
                    exp6 = data.contract_id.exp6
                    exp7 = data.contract_id.exp7
                    exp8 = data.contract_id.exp8
                    exp9 = data.contract_id.exp9
                    exp10 = data.contract_id.exp10
#                         exp11 = data.contract_id.exp11
                    exp12 = data.contract_id.exp12
                    exp13 = data.contract_id.exp13
                    exp14 = data.contract_id.exp14
                    exp15 = data.contract_id.exp15
                    exp16 = data.contract_id.exp16
                    exp17 = data.contract_id.exp17
                    exp18 = data.contract_id.exp18
                    exp19 = data.contract_id.exp19
            total_ytd_medical = total_ytd_medical + exp1 or 0.0
            total_ytd_supp_eqp = total_ytd_supp_eqp + exp2 or 0.0
            total_ytd_edu_fees = total_ytd_edu_fees + exp3 or 0.0
            total_ytd_md_serious_dis = total_ytd_md_serious_dis + exp4 or 0.0
            total_ytd_medical_exam = total_ytd_medical_exam + exp5 or 0.0
            total_ytd_purchase_book = total_ytd_purchase_book + exp6 or 0.0
            total_ytd_pur_per_comp = total_ytd_pur_per_comp + exp7 or 0.0
            total_ytd_SSPN = total_ytd_SSPN + exp8 or 0.0
            total_ytd_sport_equp = total_ytd_sport_equp + exp9 or 0.0
            total_ytd_former_wife = total_ytd_former_wife + exp10 or 0.0
#             total_ytd_life_ins = total_ytd_life_ins + exp11 or 0.0
            total_ytd_edmd_ins = total_ytd_edmd_ins + exp12 or 0.0
            total_ytd_annuity_premium = total_ytd_annuity_premium + exp13 or 0.0
            total_ytd_int_house_loan = total_ytd_int_house_loan + exp14 or 0.0
            total_ytd_lh17 = total_ytd_lh17 + exp17 or 0.0
            total_ytd_lh18 = total_ytd_lh18 + exp18 or 0.0
            total_ytd_sosco_pay = total_ytd_sosco_pay + exp19
            data.total_ytd_tp1_add_1 = total_ytd_tp1_add_1 + exp15 or 0.0
            data.total_ytd_tp1_add_2 = total_ytd_tp1_add_2 + exp16 or 0.0

            if total_ytd_medical > 0:
                if total_ytd_lh17 > 0 or total_ytd_lh18 > 0:
                    raise ValidationError(_("LHDN - Medical expenses for own \
                    parents, special need and parent care” cannot \
                    input amount ."))
                elif total_ytd_medical > 5000:
                    raise ValidationError(_("You can not apply for medical \
                    expense more then 5000 in basis year."))
                else:
                    data.total_ytd_medical = total_ytd_medical

            if total_ytd_lh17 > 1500:
                raise ValidationError(_("You can not apply for Parental \
                care - mother more then 1500 in basis year."))
            else:
                data.total_ytd_lh17 = total_ytd_lh17

            if total_ytd_lh18 > 1500:
                raise ValidationError(_("You can not apply for Parental \
                care - father more then 1500 in basis year."))
            else:
                data.total_ytd_lh18 = total_ytd_lh18

            if total_ytd_supp_eqp > 6000:
                raise ValidationError(_("You can not apply for basic "
                                        "supporting equipment more then 6000 in basis year."))
            else:
                data.total_ytd_supp_eqp = total_ytd_supp_eqp
            if total_ytd_edu_fees > 7000:
                raise ValidationError(_("You can not apply for Annual "
                                        "Education Fees more then 7000."))
            else:
                data.total_ytd_edu_fees = total_ytd_edu_fees
            if total_ytd_md_serious_dis > 6000:
                raise ValidationError(_("You can not apply for medical expense \
                for serious diseases more then 6000."))
            else:
                data.total_ytd_md_serious_dis = total_ytd_md_serious_dis
            if total_ytd_medical_exam > 500:
                raise ValidationError(_("You can not apply for medical exam \
                more then 500."))
            else:
                data.total_ytd_medical_exam = total_ytd_medical_exam
            if total_ytd_purchase_book > 2500:
                raise ValidationError(_("You can not apply for Tax Deduction \
                For Lifestyle more then 2500."))
            else:
                data.total_ytd_purchase_book = total_ytd_medical_exam
            if total_ytd_pur_per_comp > 1000:
                raise ValidationError(_("You can not apply for Purchase Of \
                Breastfeeding Equipment more then 1000."))
            else:
                data.total_ytd_pur_per_comp = total_ytd_pur_per_comp
            if total_ytd_SSPN > 6000:
                raise ValidationError(_("You can not apply for Net Deposit in \
                Skim Simpanan Pendidikan Nasional more then 6000."))
            else:
                data.total_ytd_SSPN = total_ytd_SSPN
            if total_ytd_sport_equp > 1000:
                raise ValidationError(_("You can not apply Tax Deduction For \
                Fees Paid To Child Care Centres And Kindergartens \
                more then 1000."))
            else:
                data.total_ytd_sport_equp = total_ytd_sport_equp
            if total_ytd_former_wife > 4000:
                raise ValidationError(_("You can not apply for Payment of \
                Alimony to Former Wife more then 4000."))
            else:
                data.total_ytd_former_wife = total_ytd_former_wife

            if total_ytd_edmd_ins > 3000:
                raise ValidationError(_("You can not apply for Education and \
                Medical Insurance more then 3000."))
            else:
                data.total_ytd_edmd_ins = total_ytd_edmd_ins
            if total_ytd_annuity_premium > 3000:
                raise ValidationError(_("You can not apply for Deferred "
                                        "annuity premium or contribution to private retirement"
                                        " scheme more then 3000."))
            else:
                data.total_ytd_annuity_premium = total_ytd_annuity_premium
            if total_ytd_int_house_loan > 10000:
                raise ValidationError(_("You can not apply for Interest on "
                                        "Housing Loan more then 10,000."))
            else:
                data.total_ytd_int_house_loan = total_ytd_int_house_loan

            if total_ytd_sosco_pay > 250:
                raise ValidationError(_("You can not apply for SOCSO Payment"
                                        "more then 250."))
            else:
                data.total_ytd_sosco_pay = total_ytd_sosco_pay

    @api.constrains('employee_id.user_id', 'date_from', 'date_to',
                    'employee_id', 'contract_id.alw3', 'contract_id.alw4')
    def _check_prev_allowance_one_unit(self):
        for data in self:
            year = data.date_from.strftime('%Y')
            year_start_date = datetime.strptime('%s-01-01' % (year),
                                                DEFAULT_SERVER_DATE_FORMAT)
            year_end_date = datetime.strptime('%s-12-31' % (year),
                                              DEFAULT_SERVER_DATE_FORMAT)
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', data.employee_id.id),
                ('date_from', '>=', year_start_date),
                ('date_from', '<=', year_end_date)])
            tot_gift = 0
            tot_monthly_bills = 0
            for payslip in payslip_ids:
                if payslip.date_from < year_end_date.date():
                    for line in payslip.line_ids:
                        if line.code == 'ALW_NONTAX_3':
                            tot_gift += 1
                        if line.code == 'ALW_NONTAX_4':
                            tot_monthly_bills += 1
            if tot_gift > 1:
                raise ValidationError(_("Non Taxable Allowances \nYou can not \
                apply Gift of fixed line telephone, mobile etc. more than \
                1 units per year"))
            if tot_monthly_bills > 1:
                raise ValidationError(_("Non Taxable Allowances \nYou can not \
                apply Monthly bills for subscription more than 1 units \
                per year"))
        return True

    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True, states={'draft': [('readonly', False)]}, ondelete='restrict',
                                help='Defines the rules that have to be applied to this payslip,'
                                ' accordingly to the contract chosen. If you let empty the field '
                                'contract, this field isn\'t mandatory anymore and thus the rules '
                                'applied will be all the rules set on the '
                                'structure of all contracts of the employee valid for the'
                                ' chosen period')
    cheque_number = fields.Char("Cheque Number", size=64)
    active = fields.Boolean('Pay', default=True)
    pay_by_cheque = fields.Boolean('Pay By Cheque')
    employee_name = fields.Char(related='employee_id.name', size=256,
                                string="Employee Name", store=True)
    total_ytd_gross = fields.Float(compute=_get_salary_computation_ytd_total,
                                   string='Total YTD Gross',
                                   multi="salary_computation_all",
                                   help="Total YTD(Year To Date) Gross amount")
    total_ytd_epf_employee = fields.Float(compute=_get_salary_computation_ytd_total,
                                          string='YTD EPF & Life Insurance',
                                          multi="salary_computation_all",
                                          help="Total YTD(Year To Date) EPFE amount and Life Insurance Deductions")
    total_ytd_pcb = fields.Float(compute=_get_salary_computation_ytd_total,
                                 string='Total YTD PCB',
                                 multi="salary_computation_all",
                                 help="Total YTD(Year To Date) PCB amount")
    remaining_month = fields.Integer(compute=_get_salary_computation_ytd_total,
                                     string='Remaining Month',
                                     multi="salary_computation_all")
    total_ytd_pcb_ded = fields.Float(compute=_get_salary_computation_ytd_total,
                                     string='Total YTD PCB Deduction',
                                     multi="salary_computation_all",
                                     help="Total YTD(Year To Date) PCB approval deduction amount")
    total_ytd_zakat = fields.Float(compute=_get_salary_computation_ytd_total,
                                   string='Total YTD Zakat',
                                   multi="salary_computation_all",
                                   help="Total YTD(Year To Date) Zakat amount")
    total_ytd_medical = fields.Float(compute=_get_medical_computation_ytd_total,
                                     multi='input_line_all',
                                     string='Total YTD Medical',
                                     help='Total YTD(Year To Date) Medical \
                                     amount', store=True)
    total_ytd_supp_eqp = fields.Float(compute=_get_medical_computation_ytd_total,
                                      multi='input_line_all',
                                      string="Total YTD Basic Support Equipment",
                                      help='Total YTD(Year To Date) \
                                      Support Equipment amount', store=True)
    total_ytd_edu_fees = fields.Float(compute=_get_medical_computation_ytd_total,
                                      multi='input_line_all',
                                      string="Total YTD Education Fees",
                                      help='Total YTD(Year To Date) \
                                      Education Fees', store=True)
    total_ytd_md_serious_dis = fields.Float(compute=_get_medical_computation_ytd_total,
                                            multi='input_line_all',
                                            string="Total YTD Medical Expense Serious Diseases",
                                            help='Total YTD(Year To Date) Medical Expense Serious Diseases', store=True)
    total_ytd_medical_exam = fields.Float(compute=_get_medical_computation_ytd_total,
                                          multi='input_line_all',
                                          string="Total YTD Medical Exam",
                                          help='Total YTD(Year To Date) Medical Exam', store=True)
    total_ytd_purchase_book = fields.Float(compute=_get_medical_computation_ytd_total,
                                           multi='input_line_all',
                                           string="Tax Deduction For Lifestyle",
                                           help='Total YTD(Year To Date) Tax Deduction For Lifestyle', store=True)
    total_ytd_pur_per_comp = fields.Float(compute=_get_medical_computation_ytd_total,
                                          multi='input_line_all',
                                          string="Tax Deduction For Purchase Of Breastfeeding Equipment",
                                          help='Total YTD(Year To Date) Tax Deduction For Purchase Of Breastfeeding Equipment', store=True)
    total_ytd_SSPN = fields.Float(compute=_get_medical_computation_ytd_total,
                                  multi='input_line_all',
                                  string="Net Deposit in Skim Simpanan Pendidikan Nasional",
                                  help='Total YTD(Year To Date) Net Deposit in Skim Simpanan Pendidikan Nasional', store=True)
    total_ytd_sport_equp = fields.Float(compute=_get_medical_computation_ytd_total,
                                        multi='input_line_all',
                                        string="Tax Deduction For Fees Paid To Child Care Centres And Kindergartens",
                                        help='Total YTD(Year To Date) Tax Deduction For Fees Paid To Child Care Centres And Kindergartens', store=True)
    total_ytd_former_wife = fields.Float(compute=_get_medical_computation_ytd_total,
                                         multi='input_line_all',
                                         string="Payment of Alimony to Former Wife",
                                         help='Total YTD(Year To Date) Payment of Alimony to Former Wife', store=True)
#     total_ytd_life_ins = fields.Float(compute=_get_medical_computation_ytd_total,
#                                       multi='input_line_all',
#                                       string="Life Insurance",
# help='Total YTD(Year To Date Life Insurance)', store=True)
    total_ytd_edmd_ins = fields.Float(compute=_get_medical_computation_ytd_total,
                                      multi='input_line_all',
                                      string="Education and Medical Insurance",
                                      help='Total YTD(Year To Date) Education and Medical Insurance', store=True)
    total_ytd_annuity_premium = fields.Float(compute=_get_medical_computation_ytd_total,
                                             multi='input_line_all',
                                             string="Deferred annuity premium",
                                             help='Total YTD(Year To Date) Deferred annuity premium', store=True)
    total_ytd_int_house_loan = fields.Float(compute=_get_medical_computation_ytd_total,
                                            multi='input_line_all',
                                            string="Interest on Housing Loan",
                                            help='Total YTD(Interest on Housing Loan)', store=True)

    total_ytd_sosco_pay = fields.Float(compute=_get_medical_computation_ytd_total,
                                       multi='input_line_all',
                                       string="SOCSO Payment",
                                       help='Total YTD(SOCSO Payment)', store=True)

    total_ytd_tp1_add_1 = fields.Float(compute=_get_medical_computation_ytd_total,
                                       multi='input_line_all',
                                       string="TP1 add me 1", store=True)
    total_ytd_tp1_add_2 = fields.Float(compute=_get_medical_computation_ytd_total,
                                       multi='input_line_all',
                                       string="TP1 add me 2", store=True)
    total_ytd_lh17 = fields.Float(compute=_get_medical_computation_ytd_total,
                                  multi='input_line_all',
                                  string="Parental care - mother",
                                  store=True)
    total_ytd_lh18 = fields.Float(compute=_get_medical_computation_ytd_total,
                                  multi='input_line_all',
                                  string="Parental care - father",
                                  store=True)

    # total_ytd_alw1 = fields.Float(compute=_get_non_tax_alw_ytd_total,
    #                               multi='input_line_nontax',
    #                               string='Total YTD alw1',
    #                               help='Total YTD(Year To Date) Medical \
    #                                  amount', store=True)
    # total_ytd_alw2 = fields.Float(compute=_get_non_tax_alw_ytd_total,
    #                               multi='input_line_nontax',
    #                               string='Total YTD alw2',
    #                               help='Total YTD(Year To Date) Medical \
    #                                  amount', store=True)
    # total_ytd_alw5 = fields.Float(compute=_get_non_tax_alw_ytd_total,
    #                               multi='input_line_nontax',
    #                               string='Total YTD alw5',
    #                               help='Total YTD(Year To Date) Medical \
    #                                  amount', store=True)
    refund = fields.Boolean("Refund")
    expense_amount = fields.Float()
    expense_ids = fields.Many2many('hr.expense', string="Expense")
    sheet_id = fields.Many2many('hr.expense.sheet')
    date_from_month = fields.Char()
    date_from_year = fields.Char()
    leave_days = fields.Float('Leave Days')
    leave_type = fields.Selection([('unpaid','Un-Paid Leave'),('paid','Paid Leave')],
                                  string='Leave Type')
    unpaid_leave = fields.Many2one('hr.leave','UnPaid Leave Selection')
    other_allowance_sum = fields.Float('Other Allowance Sum',default=0.0)
    non_taxable_allowance_sum = fields.Float('Non Taxable Allowance Sum',default=0.0)
    gross_salary = fields.Float('Gross Salary', default=0.0)
    net_salary = fields.Float('Net Salary', default=0.0)

    @api.onchange('leave_type','date_from')
    def onchange_leave_type(self):
        if self.date_from_year and self.date_from_month and self.leave_type == 'paid':
            end_date = datetime(int(self.date_from.year), int(self.date_from.month), 1).date()
            start_date = (end_date - relative(months=1))
            # Search for records with expiry dates in March 2024
            allocation_record = self.env['hr.leave.allocation'].search([
                ('expiry_date', '>=', start_date),
                ('expiry_date', '<', end_date),
                ('expiry_done', '=', True),
                ('employee_id.id', '=', self.employee_id.id)
            ])
            self.leave_days = allocation_record.remaining_leaves_for_payslip
        else:
            self.leave_days = 0


    @api.model
    def day_of_generate_payslip_sch(self):
        employee = self.env['hr.employee'].search([('active', '=', True)])
        date_from = datetime.today() + relativedelta.relativedelta(day=1, months=-1)
        date_to = date_from + relativedelta.relativedelta(months=+1, days=-1)
        today_date = datetime.today().day
        today_month = datetime.today().month
        payslip_day = self.env.user.company_id.day_of_generate_payslip
        if today_month == 2 and payslip_day > 28:
            payslip_day = 28
        if today_date == payslip_day:
            for emp in employee:
                vals = {
                    'employee_id': emp and emp.id or False,
                    'date_start': date_from,
                    'date_end': date_to,
                }
                payslip = self.create(vals)
                contract = payslip.get_contract(emp, date_from, date_to)
                payslip.contract_id = contract and contract[0] or False
                payslip.struct_id = payslip.contract_id.struct_id and payslip.contract_id.struct_id.id or False
                payslip.onchange_employee()
                payslip.onchange_employee_id(
                    date_from, date_to, emp.id, payslip.contract_id.id)
                result = payslip.onchange_employee_id_new()
                payslip.worked_days_line_ids = result['value']['worked_days_line_ids']
                payslip.compute_sheet()
        return True

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            payslip.refund = True
            copied_payslip = payslip.copy(
                {'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    @api.constrains('employee_id', 'contract_id', 'date_from', 'date_to')
    def check_contract(self):
        for rec in self:
            if rec.contract_id.state == 'close':
                raise ValidationError(
                    "You can note generate payslip for Expired contract")

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(
                fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(
                fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.with_context(without_public_holiday=True).list_leaves(
                day_from, day_to, calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave[:1].holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                    'is_unpaid': True if holiday.holiday_status_id.unpaid else False
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

#             compute worked days
            work_data = contract.employee_id.get_work_days_data(
                day_from, day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
 
            res.append(attendances)
            res.extend(leaves.values())
        return res

    @api.onchange('sheet_id')
    def onchange_expense_ids(self):
        self.expense_amount = sum(self.sheet_id.mapped('total_amount'))

    @api.onchange('date_from')
    def onchange_date_from(self):
        given_date = self.date_from
        first_day_of_month = date(given_date.year, given_date.month, 1)

        # Add a timedelta of one day to the first day of the month
        # and subtract one day to get the last day of the month
        last_day_of_month = first_day_of_month + dt.timedelta(
            days=(calendar.monthrange(given_date.year, given_date.month)[1] - 1))
        self.date_to = last_day_of_month

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_get_expense_ids(self):
        employee_id = self.employee_id and self.employee_id.id or self._context.get(
            'employee_id', False)
        date_from = self.date_from or self._context.get('date_from', False)
        date_to = self.date_to or self._context.get('date_to', False)
        month = date_from.month
        year = date_from.year
        expense_rec = self.env['hr.expense.sheet'].search([('employee_id', '=', employee_id),
                                                     ('state', 'in', ('approve', 'post')),
                                                     ('month','=', month),
                                                     ('year', '=', year)])
        for rec in self:
            rec.date_from_month = month
            rec.date_from_year = date_from.strftime('%y')
            rec.sheet_id = None
            domain = {'sheet_id': [('id', 'in', expense_rec.ids)]}
            # rec.expense_amount = rec.expense_ids and sum(rec.expense_ids.mapped(
            #     'total_amount')) if rec.expense_ids else 0
            return {'domain':domain}

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_id_new(self):
        employee_id = self.employee_id and self.employee_id.id or self._context.get(
            'employee_id', False)
        date_from = self.date_from or self._context.get('date_from', False)
        date_to = self.date_to or self._context.get('date_to', False)
        contract_id = self.contract_id and self.contract_id.id or self._context.get(
            'contract_id', False)
        unpaid_hours = 0
        for work in self.get_worked_day_lines(self.contract_id, date_from, date_to):
            if work.get('is_unpaid'):
                unpaid_hours += work['number_of_days']
        result = super(HrPayslip, self).onchange_employee_id(
            date_from, date_to, employee_id, contract_id)
        result['value']['worked_days_line_ids'] = []

        if 'value' in result and 'contract_id' in result['value']:
            contract_id = result['value'].get('contract_id', False)
        if date_from and date_to:
            current_date_from = date_from
            current_date_to = date_to
            date_from_cur = date_from

            first_day_of_current_month = date_from_cur + \
                relativedelta.relativedelta(day=1)
            last_day_of_current_month = first_day_of_current_month + \
                relativedelta.relativedelta(months=1, days=-1)
            first_date_from = datetime.strftime(
                first_day_of_current_month, DEFAULT_SERVER_DATE_FORMAT)
            first_date_to = datetime.strftime(
                last_day_of_current_month, DEFAULT_SERVER_DATE_FORMAT)
            first_dates = list(rrule.rrule(
                rrule.DAILY, dtstart=parser.parse(first_date_from),
                until=parser.parse(first_date_to)))
            # month = date_from.month
            # year = date_from.year
            # expense_rec = self.env['hr.expense'].search([('employee_id', '=', employee_id),
            #                                              ('sheet_id.state',
            #                                               'in', ('approve', 'post')),
            #                                              ('payment_mode',
            #                                               '=', 'own_account'),
            #                                              ('sheet_id.month',
            #                                               '=', month),
            #                                              ('type_of_expense', '=',
            #                                               'subjected_to_pcb'),
            #                                              ('sheet_id.year', '=', year)])
            # for rec in self:
            #     rec.date_from_month = month
            #     rec.date_from_year = date_from.strftime('%y')
            #     rec.expense_ids = [(5, 0, 0)]
            #     domain = {'expense_ids': [('id', 'in', expense_rec.ids)]}
            #     rec.expense_amount = rec.expense_ids and sum(rec.expense_ids.mapped(
            #         'total_amount')) if rec.expense_ids else 0

            fsunday = fsaturday = fweekdays = 0
            for day in first_dates:
                if day.weekday() == 5:
                    fsaturday += 1
                elif day.weekday() == 6:
                    fsunday += 1
                else:
                    fweekdays += 1
            count = 0
            holiday_brw = self.env['hr.holiday.public'].search(
                [('state', '=', 'validated')])
            if holiday_brw and holiday_brw.ids:
                for line in holiday_brw:
                    for holiday in line.holiday_line_ids:
                        holidyz_mnth = holiday.holiday_date.month
                        holiday_year = holiday.holiday_date.year
                        if current_date_to.year == holiday_year and holidyz_mnth == current_date_to.month:
                            count = count + 1
            new = {'code': 'PUBLICHOLIDAYS', 'name': 'Total Public Holidays in current month',
                   'number_of_days': count, 'sequence': 2, 'contract_id': contract_id}
            result.get('value').get('worked_days_line_ids').append(new)
            previous_month_obj = date_from_cur - \
                relativedelta.relativedelta(months=1)
            total_days = calendar.monthrange(previous_month_obj.year,
                                             previous_month_obj.month)[1]
            first_day_of_previous_month = datetime.strptime(
                "1-" + str(previous_month_obj.month) + "-" + str(previous_month_obj.year), '%d-%m-%Y')
            last_day_of_previous_month = datetime.strptime(str(total_days) + "-" + str(
                previous_month_obj.month) + "-" + str(previous_month_obj.year), '%d-%m-%Y')
            date_from1 = datetime.strftime(first_day_of_previous_month,
                                          DEFAULT_SERVER_DATE_FORMAT)
            date_to1 = datetime.strftime(last_day_of_previous_month,
                                        DEFAULT_SERVER_DATE_FORMAT)
            dates = list(rrule.rrule(rrule.DAILY,
                                     dtstart=parser.parse(date_from1),
                                     until=parser.parse(date_to1)))

            sunday = saturday = weekdays = 0
            for day in dates:
                if day.weekday() == 5:
                    saturday += 1
                elif day.weekday() == 6:
                    sunday += 1
                else:
                    weekdays += 1

            res = {'code': 'TTLPREVDAYINMTH',
                   'name': 'Total number of days for previous month',
                   'number_of_days': len(dates), 'sequence': 3,
                   'contract_id': contract_id}
#             result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TTLPREVSUNINMONTH',
                   'name': 'Total sundays in previous month',
                   'number_of_days': sunday, 'sequence': 3,
                   'contract_id': contract_id}
#             result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TTLPREVSATINMONTH',
                   'name': 'Total saturdays in previous month',
                   'number_of_days': saturday, 'sequence': 4,
                   'contract_id': contract_id}
#             result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TTLPREVWKDAYINMTH',
                   'name': 'Total weekdays in previous month',
                   'number_of_days': weekdays, 'sequence': 5,
                   'contract_id': contract_id}


#             result.get('value').get('worked_days_line_ids').append(res)
            dates = list(rrule.rrule(rrule.DAILY,
                                     dtstart=current_date_from,
                                     until=current_date_to))
            res = {'code': 'TTLCURRDAYINMTH',
                   'name': 'Total number of days for current month',
                   'number_of_days': len(first_dates), 'sequence': 2,
                   'contract_id': contract_id}
            result.get('value').get('worked_days_line_ids').append(res)
            total_wagedays = 0
            if self.company_id.enable_pro_data_sal:
                if self.company_id.public_holiday_paid and self.company_id.working_days_month == 'every_days':
                    total_wagedays = len(dates) - count
                elif self.company_id.public_holiday_paid and self.company_id.working_days_month == '26':
                    total_wagedays = 26 - count
                elif self.company_id.public_holiday_paid and self.company_id.working_days_month == '22':
                    total_wagedays = 22 - count
                elif self.company_id.public_holiday_paid and self.company_id.working_days_month == 'work_days':
                    total_wagedays = fweekdays - count
                elif self.company_id.working_days_month == 'every_days':
                    total_wagedays = len(dates)
                elif self.company_id.working_days_month == '26':
                    total_wagedays = 26
                elif self.company_id.working_days_month == '22':
                    total_wagedays = 22
                elif self.company_id.working_days_month == 'work_days':
                    total_wagedays = fweekdays
            else:
                total_wagedays = fweekdays
            
            for work in self.worked_days_line_ids:
                if first_day_of_current_month == date_from and last_day_of_current_month == date_to:
                    if work.code == 'WORK100':
                        work.number_of_days = total_wagedays - unpaid_hours
            
            res = {'code': 'TTLCURRWKDAYINMTH',
                   'name': 'Total weekdays in current month',
                   'number_of_days': total_wagedays - unpaid_hours, 'sequence': 5,
                   'contract_id': contract_id}
            result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TOTALWAGEDAYS',
                   'name': 'Total number of days',
                   'number_of_days': total_wagedays, 'sequence': 2,
                   'contract_id': contract_id
                   }
            result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TTLCURRSUNINMONTH',
                   'name': 'Total sundays in current month',
                   'number_of_days': sunday, 'sequence': 3,
                   'contract_id': contract_id}
#             result.get('value').get('worked_days_line_ids').append(res)
            res = {'code': 'TTLCURRSATINMONTH',
                   'name': 'Total saturdays in current month',
                   'number_of_days': saturday, 'sequence': 4,
                   'contract_id': contract_id}
#             result.get('value').get('worked_days_line_ids').append(res)
            contract_record = self.env['hr.contract'].browse(contract_id)
            cur_month_weekdays = 0
            if contract_record:
                contract_start_date = contract_record.date_start
                contract_end_date = contract_record.date_end
                if contract_start_date and contract_end_date:

                    if current_date_from <= contract_start_date and contract_end_date <= current_date_to:
                        current_month_days = list(rrule.rrule(rrule.DAILY, dtstart=parser.parse(
                            contract_start_date), until=parser.parse(contract_end_date)))
                        for day in current_month_days:
                            if day.weekday() not in [5, 6]:
                                cur_month_weekdays += 1

                    elif current_date_from <= contract_start_date and current_date_to <= contract_end_date:
                        current_month_days = list(rrule.rrule(
                            rrule.DAILY, dtstart=contract_start_date, until=current_date_to))
                        for day in current_month_days:
                            if day.weekday() not in [5, 6]:
                                cur_month_weekdays += 1

                    elif contract_start_date <= current_date_from and contract_end_date <= current_date_to:
                        current_month_days = list(rrule.rrule(
                            rrule.DAILY, dtstart=current_date_from, until=contract_end_date))
                        for day in current_month_days:
                            if day.weekday() not in [5, 6]:
                                cur_month_weekdays += 1
            if cur_month_weekdays:
                new = {'code': 'TTLCURCONTDAY', 'name': 'Total current contract days in current month',
                       'number_of_days': cur_month_weekdays, 'sequence': 6, 'contract_id': contract_record.id}
#                 result.get('value').get('worked_days_line_ids').append(new)
            else:
                new = {'code': 'TTLCURCONTDAY', 'name': 'Total current contract days in current month',
                       'number_of_days': weekdays, 'sequence': 6, 'contract_id': contract_record.id}
#                 result.get('value').get('worked_days_line_ids').append(new)
        result['value']['input_line_ids'] = []
        return result

    @api.multi
    def compute_sheet(self):
        if self.struct_id:
            all_allowance_rule = self.env['hr.salary.rule'].sudo().search([('name','like','Allowance')])
            all_allowances = self.contract_id.contract_allowance_id
            allowance_lst = all_allowances.mapped('name')
            existing_allowances = [
                allowance for allowance in allowance_lst
                if any(rule.name == allowance for rule in all_allowance_rule)
            ]
            unique_allowance = list(set(allowance_lst) ^ set(existing_allowances))
            allowance_to_add_ids = self.contract_id.contract_allowance_id.filtered(lambda x: x.name in unique_allowance)
            total_sum = sum(allowance_to_add_ids.mapped('allowance_amount'))
            non_taxable_total_sum = sum(self.contract_id.contract_nontaxable_allowance_id.mapped('allowance_amount'))
            self.other_allowance_sum = total_sum
            self.non_taxable_allowance_sum = non_taxable_total_sum
        result = super(HrPayslip, self).compute_sheet()
        lines = []
        for payslip in self:
            from_month = payslip.date_from.month
            from_year = payslip.date_from.strftime('%y')
            inputs = payslip.input_line_ids.filtered(
                lambda x: x.code == 'INPUTCP38')
            if inputs and payslip.contract_id.default_pcb_amount > 0:
                inputs.write(
                    {'amount': payslip.contract_id.default_pcb_amount, 'sequence': 1})
            payslips = self.env['hr.payslip'].search([('active', '=', True),
                                                      ('date_from_month',
                                                       '=', from_month),
                                                      ('date_from_year',
                                                       '=', from_year),
                                                      ('id', '!=', payslip.id)])
            last_num = []
            for pay in payslips:
                number = pay.number and pay.number.split('/') or False
                if number:
                    last_num += [int(number[-1])]
            if last_num:
                latest_no = max(last_num) + 1
            else:
                latest_no = 1
            payslip.number = 'SLIP/' + \
                str('%%0%sd' % 2 % from_month) + '/' + str(from_year) + \
                '/' + str('%%0%sd' % 4 % latest_no)

            for line in payslip.line_ids:
                if line.amount == 0 and line.code != 'PCBCURRMONTH':
                    lines.append(line.id)
                if not payslip.expense_ids:
                    payslip.expense_amount = 0.0
                else:
                    payslip.expense_amount = sum(payslip.expense_ids.mapped(
                        'total_amount'))
                    if line.code == 'EXP':
                        total = sum(payslip.expense_ids.mapped(
                            'total_amount')) if payslip.expense_ids else 0
                        payslip.expense_ids and payslip.expense_ids.mapped(
                            'sheet_id').write({'payslip_ids': [(6, 0, payslip.ids)]})
                        line.total = total
        if lines:
            self.env['hr.payslip.line'].browse(lines).unlink()
        if self.leave_type == 'unpaid' and self.unpaid_leave:
            self.unpaid_leave.payslip_status = True
        self.gross_salary = self.line_ids.filtered(lambda x: x.name == 'Gross').amount
        self.net_salary = self.line_ids.filtered(lambda x: x.name == 'Net').amount
        return result

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        res = super(HrPayslip,self)._get_payslip_lines(contract_ids, payslip_id)
        all_allowances = self.contract_id.contract_allowance_id
        allowance_lst = all_allowances.mapped('name')
        existing_allowances = [
            allowance for allowance in allowance_lst
            if any(rule['name'] == allowance for rule in res)
        ]

        result_template = 'result = {}'
        # Replace the placeholder with actual values
        result_1 = result_template.format(400.0)
        # Filter data based on existing allowances
        unique_allowances = list(set(allowance_lst) ^ set(existing_allowances))
        allowance_to_add = []
        salary_rule_id = self.env['hr.salary.rule'].sudo().search([('name','=','ALL_ALLOWANCES')])
        non_taxable_allowance_salary_rule_id = self.env['hr.salary.rule'].sudo().search([
            ('name', '=', 'Non Taxable Allowance')])
        non_taxable_allowance = self.contract_id.contract_nontaxable_allowance_id
        if unique_allowances:
            allowance_to_add = self.contract_id.contract_allowance_id.filtered(lambda x: x.name in unique_allowances)
            total_amount_sum = sum(allowance_to_add.mapped('allowance_amount'))
            for allowance in allowance_to_add:
                new_dict = {
                    'salary_rule_id': None,
                    'contract_id': None,
                    'name': None,
                    'code': None,
                    'category_id': None,
                    'sequence': None,
                    'appears_on_payslip': None,
                    'condition_select': None,
                    'condition_python': None,
                    'condition_range': None,
                    'condition_range_min': None,
                    'condition_range_max': None,
                    'amount_select': None,
                    'amount_fix': None,
                    'amount_python_compute': None,
                    'amount_percentage': None,
                    'amount_percentage_base': None,
                    'register_id': None,
                    'amount': None,
                    'employee_id': None,
                    'quantity': None,
                    'rate': None
                }
                if allowance.allowance_amount:
                    new_dict['salary_rule_id'] = salary_rule_id.id
                    new_dict['contract_id'] = self.contract_id.id
                    new_dict['name'] = allowance.name
                    new_dict['code'] = str(salary_rule_id.code)
                    new_dict['category_id'] = salary_rule_id.category_id.id
                    new_dict['sequence'] = 2
                    new_dict['employee_id'] = self.employee_id.id
                    new_dict['condition_select'] = 'none'
                    new_dict['appears_on_payslip'] = True
                    new_dict['condition_python'] = "\n# Available variables:\n#----------------------\n# payslip: object containing the payslips\n# employee: hr.employee object\n# contract: hr.contract object\n# rules: object containing the rules code (previously computed)\n# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).\n# worked_days: object containing the computed worked days\n# inputs: object containing the computed inputs\n\n# Note: returned value have to be set in the variable 'result'\n\n"
                    new_dict['amount_python_compute'] = 'result=0.0',
                    new_dict['amount_select'] = 'fix'
                    new_dict['amount_fix'] = allowance.allowance_amount
                    new_dict['amount'] = allowance.allowance_amount
                    new_dict['quantity'] = 1.0
                    new_dict['rate'] = 100.0
                    res.append(new_dict)
        if non_taxable_allowance:
            for allowance in non_taxable_allowance:
                new_dict = {
                    'salary_rule_id': None,
                    'contract_id': None,
                    'name': None,
                    'code': None,
                    'category_id': None,
                    'sequence': None,
                    'appears_on_payslip': None,
                    'condition_select': None,
                    'condition_python': None,
                    'condition_range': None,
                    'condition_range_min': None,
                    'condition_range_max': None,
                    'amount_select': None,
                    'amount_fix': None,
                    'amount_python_compute': None,
                    'amount_percentage': None,
                    'amount_percentage_base': None,
                    'register_id': None,
                    'amount': None,
                    'employee_id': None,
                    'quantity': None,
                    'rate': None
                }
                if allowance.allowance_amount:
                    new_dict['salary_rule_id'] = non_taxable_allowance_salary_rule_id.id
                    new_dict['contract_id'] = self.contract_id.id
                    new_dict['name'] = allowance.name
                    new_dict['code'] = str(non_taxable_allowance_salary_rule_id.code)
                    new_dict['category_id'] = non_taxable_allowance_salary_rule_id.category_id.id
                    new_dict['sequence'] = 2
                    new_dict['employee_id'] = self.employee_id.id
                    new_dict['condition_select'] = 'none'
                    new_dict['appears_on_payslip'] = True
                    new_dict[
                        'condition_python'] = "\n# Available variables:\n#----------------------\n# payslip: object containing the payslips\n# employee: hr.employee object\n# contract: hr.contract object\n# rules: object containing the rules code (previously computed)\n# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).\n# worked_days: object containing the computed worked days\n# inputs: object containing the computed inputs\n\n# Note: returned value have to be set in the variable 'result'\n\n"
                    new_dict['amount_python_compute'] = 'result=0.0',
                    new_dict['amount_select'] = 'fix'
                    new_dict['amount_fix'] = allowance.allowance_amount
                    new_dict['amount'] = allowance.allowance_amount
                    new_dict['quantity'] = 1.0
                    new_dict['rate'] = 100.0
                    res.append(new_dict)

        return res


    @api.multi
    def action_payslip_done(self):
        for slip in self:
            if not self.env.context.get('without_compute_sheet'):
                slip.compute_sheet()
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            eis_total = 0.0
            scs_total = 0.0
            epf_total = 0.0
            pcb_total = 0.0
            date = slip.date or slip.date_to
            currency = slip.company_id.currency_id or slip.journal_id.company_id.currency_id

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            credit_account_id = slip.company_id.accrual_account_id.id
            accrual_epf_id = slip.company_id.accrual_epf_id.id
            accrual_socso_id = slip.company_id.accrual_socso_id.id
            accrual_eis_id = slip.company_id.accrual_eis_id.id
            accrual_pcb_id = slip.company_id.accrual_pcb_id.id
            if not credit_account_id:
                raise ValidationError(_("Please Add Accrual Account!!!"))
            if slip.company_id.accraul_type == 'diff_accrual':
                if not accrual_epf_id:
                    raise ValidationError(
                        _("Please Add Accrual-EPF Account!!!"))
                if not accrual_socso_id:
                    raise ValidationError(
                        _("Please Add Accrual-SOCSO Account!!!"))
                if not accrual_eis_id:
                    raise ValidationError(
                        _("Please Add Accrual-EIS Account!!!"))
                if not accrual_pcb_id:
                    raise ValidationError(
                        _("Please Add Accrual-PCB Account!!!"))
            for line in slip.details_by_salary_rule_category:
                if line.code == 'EPF_Y_NORMAL':
                    credit_sum += line.total
                if line.code == 'DEPFE':
                    eis_total += line.total
                if line.code == 'SCSY':
                    credit_sum += line.total
                if line.code == 'SCSE':
                    scs_total += line.total
                if line.code == 'EISY':
                    credit_sum += line.total
                if line.code == 'EISE':
                    epf_total += line.total
                if line.code == 'PCBCURRMONTH':
                    pcb_total += line.total
                amount = currency.round(
                    slip.credit_note and -line.total or line.total)
                if currency.is_zero(amount):
                    continue

                debit_account_id = line.salary_rule_id.account_debit.id

                if not slip.employee_id.address_home_id.salary_account_id:
                    raise ValidationError(
                        _("Please Configure Salary Account in Employee's Work Address!!"))
                if slip.employee_id.address_home_id.salary_account_id.id and line.code == 'GROSS':
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': slip.employee_id.address_home_id.salary_account_id.id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - \
                        debit_line[2]['credit']

                if line.code == 'SCSY':
                    if not debit_account_id:
                        raise ValidationError(
                            _("Please Configure Account In SOCSO!!"))
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - \
                        debit_line[2]['credit']

                if line.code == 'EPF_Y_NORMAL':
                    if not debit_account_id:
                        raise ValidationError(
                            _("Please Configure Account In EPF!!"))
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - \
                        debit_line[2]['credit']

                if line.code == 'EISY':
                    if not debit_account_id:
                        raise ValidationError(
                            _("Please Configure Account In EIS!!"))
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - \
                        debit_line[2]['credit']

                if line.code == 'NET':
                    if not debit_account_id:
                        raise ValidationError(
                            _("Please Configure Account In NET!!!"))
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': line.salary_rule_id.account_credit.id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': line.total < 0.0 and -line.total or 0.0,
                        'credit': line.total > 0.0 and line.total or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
            if slip.company_id.accraul_type == 'all_in_one':
                total = credit_sum + eis_total + scs_total + pcb_total + epf_total
                if credit_account_id and total > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - Salary',
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': total < 0.0 and -total or 0.0,
                        'credit': total > 0.0 and total or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
            if slip.company_id.accraul_type == 'diff_accrual':
                if credit_account_id and credit_sum > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - Salary',
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': credit_sum < 0.0 and -credit_sum or 0.0,
                        'credit': credit_sum > 0.0 and credit_sum or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
                if accrual_epf_id and epf_total > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - EPF',
                        'account_id': accrual_epf_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': epf_total < 0.0 and -epf_total or 0.0,
                        'credit': epf_total > 0.0 and epf_total or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
                if accrual_socso_id and scs_total > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - SOCSO',
                        'account_id': accrual_socso_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': scs_total < 0.0 and -scs_total or 0.0,
                        'credit': scs_total > 0.0 and scs_total or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
                if accrual_eis_id and eis_total > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - EIS',
                        'account_id': accrual_eis_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': eis_total < 0.0 and -eis_total or 0.0,
                        'credit': eis_total > 0.0 and eis_total or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
                if accrual_pcb_id and pcb_total > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - PCB',
                        'account_id': accrual_pcb_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': pcb_total < 0.0 and -pcb_total or 0.0,
                        'credit': pcb_total > 0.0 and pcb_total or 0.0,
                        'analytic_account_id': slip.contract_id.analytic_account_id.id,
                    })
                    line_ids.append(credit_line)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date, 'state': 'done'})
            move.post()


class HrContract(models.Model):

    _inherit = 'hr.contract'

    @api.constrains('date_end', 'date_start')
    def _check_date(self):
        for contract in self:
            domain = [('date_start', '<=', contract.date_end),
                      ('date_end', '>=', contract.date_start),
                      ('employee_id', '=', contract.employee_id.id),
                      ('id', '!=', contract.id)]
            contract_ids = self.search(domain, count=True)
            if contract_ids:
                raise ValidationError('You can not have 2 contract that \
                overlaps on same date!')
        return True

    @api.constrains('exp1', 'exp2', 'exp3', 'exp4', 'exp5', 'exp6', 'exp7', 'exp8',
                    'exp9', 'exp10', 'exp12', 'exp13', 'exp14', 'exp17',
                    'exp18', 'exp19')
    def _check_prev_employment_exp(self):
        for contract in self:
            if contract.exp1 and contract.exp1 > 5000:
                raise ValidationError(_("You can not apply for medical \
                expense more then 5000."))
            if contract.exp2 and contract.exp2 > 6000:
                raise ValidationError(_("You can not apply for basic \
                supporting equipment more then 6000."))
            if contract.exp3 and contract.exp3 > 7000:
                raise ValidationError(_("You can not apply for Annual \
                Education Fees more then 7000."))
            if contract.exp4 and contract.exp4 > 6000:
                raise ValidationError(_("You can not apply for medical \
                expense for serious diseases more then 6000."))
            if contract.exp5 and contract.exp5 > 500:
                raise ValidationError(_("You can not apply for medical exam \
                more then 500."))
            if contract.exp6 and contract.exp6 > 2500:
                raise ValidationError(_("You can not apply for Tax Deduction \
                For Lifestyle more then 2500."))
            if contract.exp7 and contract.exp7 > 1000:
                raise ValidationError(_("You can not apply Tax Deduction For \
                Purchase Of Breastfeeding Equipment more then 1000."))
            if contract.exp8 and contract.exp8 > 6000:
                raise ValidationError(_("You can not apply for Net Deposit \
                in Skim Simpanan Pendidikan Nasional more then 6000."))
            if contract.exp9 and contract.exp9 > 1000:
                raise ValidationError(_("You can not apply Tax Deduction For \
                Fees Paid To Child Care Centres And Kindergartens \
                more then 1000."))
            if contract.exp10:
                if contract.exp10 > 4000:
                    raise ValidationError(_("You can not apply for Payment of \
                    Alimony to Former Wife more then 4000."))
                if contract.employee_id and contract.employee_id.marital and \
                    contract.employee_id.marital not in ('divorced', 'married'
                                                         ):
                    raise ValidationError(_("Employees who are Divorced, \
                        Widowed or Married and Spouse is Working are able to\
                        add this input."))
#             if contract.exp11 and contract.exp11 > 6000:
#                 raise ValidationError(_("You can not apply for Life \
#                 Insurance more then 6000."))
            if contract.exp12 and contract.exp12 > 3000:
                raise ValidationError(_("You can not apply for Education \
                and Medical Insurance more then 3000."))
            if contract.exp13 and contract.exp13 > 3000:
                raise ValidationError(_("You can not apply for Deferred \
                annuity premium or contribution to private returement \
                scheme more then 3000."))
            if contract.exp14 and contract.exp14 > 10000:
                raise ValidationError(_("You can not apply for Interest on \
                Housing Loan more then 10,000."))
            if contract.exp17 and contract.exp17 > 1500:
                raise ValidationError(_("You can not apply for Parental \
                care - Mother deduction more then 1500."))
            if contract.exp18 and contract.exp18 > 1500:
                raise ValidationError(_("You can not apply for Parental \
                care - Father deduction more then 1500."))
            if contract.exp19 and contract.exp19 > 250:
                raise ValidationError(_("You can not apply for \
                SOCSO Payment more then 250."))
        return True

    # @api.constrains('alw1', 'alw2', 'alw5')
    # def _check_prev_allowance_exp(self):
    #     for contract in self:
    #         if contract.alw1 and contract.alw1 > 6000:
    #             raise ValidationError(_("You can not Petrol or \
    #             Travelling allowance expense more then 6000."))
    #         if contract.alw2 and contract.alw2 > 2400:
    #             raise ValidationError(_("You can not apply for \
    #             Child care allowance more then 2400."))
    #         if contract.alw5 and contract.alw5 > 2000:
    #             raise ValidationError(_("You can not apply for Employee \
    #             Perquisite more then 2000."))
    #     return True

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
                                ondelete='restrict')
    dsc_category1 = fields.Selection([
        ('cat1', 'Single'),
        ('cat2', 'Married and spouse is not working'),
        ('cat3', 'Married and spouse is working'),
    ], 'Category DSC')
    d_amount = fields.Float('(D) Deduction for individual')
    s_amount = fields.Float('(S) Deduction for spouse')
    c_amount = fields.Float('(C) Number of qualifying children')
    category_mrb = fields.Many2one('contract.category.mrb', 'Category PCB')
    rate_per_hour = fields.Float('Rate per hour for part timer')
    prev_empl_ded = fields.Float('Previous Employment Deductions',
                                 help="Deductions paid by previous employer.")
    prev_empl_zakat = fields.Float('Previous Employment Zakat',
                                   help="Zakat paid by previous employer.")
    prev_empl_add = fields.Float('Previous Employment Gross',
                                 help="Gross remuneration paid by previous employer.")
    prev_empl_epf = fields.Float('Previous Employment EPF',
                                 help="EPF paid by previous employer.")
    prev_empl_PCB = fields.Float('Previous Employment PCB',
                                 help="PCB paid by previous employer.")
    exp1 = fields.Float('1) Medical expenses for own parents, special need \
    and parent care', help="Maximum amount per Year: 5000.")
    exp2 = fields.Float('2) Basic supporting equipment for disabled self, \
    spouse, child or parent', help="Maximum amount per Year: 6000.")
    exp3 = fields.Float('3) Education fees',
                        help="Maximum amount per Year: 7000.")
    exp4 = fields.Float('4) Medical expenses on serious diseases for self, \
    spouse or child', help="Maximum amount per Year: 6000.")
    exp5 = fields.Float('5) Complete medical examination for self, \
    spouse or child', help="Maximum amount per Year: 500.")
    exp6 = fields.Float('6) Tax deduction for lifestyle',
                        help="Maximum amount per Year: 2500.")
    exp7 = fields.Float('7) Tax Deduction For Purchase Of Breastfeeding \
    Equipment', help="Maximum amount per Year: 1000.")
    exp9 = fields.Float('9) Tax Deduction For Fees Paid To Child Care \
    Centres And Kindergartens', help="Maximum amount per Year: 1000.")
    exp8 = fields.Float('8) Net deposit in Skim Simpanan Pendidikan \
    National (SSPN)', help="Maximum amount per Year: 6000.")
    exp10 = fields.Float('10) Payment of alimony to former wife',
                         help="Maximum amount per Year: 4000.")
    exp11 = fields.Float('11) Life insurance and provident fund',
                         help="Maximum amount per Year: 6000.")
    exp12 = fields.Float('12) Education and medical insurance premium',
                         help="Maximum amount per Year: 3000.")
    exp13 = fields.Float('13) Deferred annuity premium or contribution to \
    private returement scheme', help="Maximum amount per Year: 3000.")
    exp14 = fields.Float('14) Interest on Housing Loan',
                         help="Maximum amount per Year: 10,000.")
    exp15 = fields.Float('15) TP1 - edit me', help="Extra Deduction")
    exp16 = fields.Float('16) TP1 - edit me', help="Extra Deduction")
    exp17 = fields.Float('17) Parental care - Mother')
    exp18 = fields.Float('18) Parental care - Father')
    exp19 = fields.Float('19) SOCSO Payment',
                         help="Maximum amount per Year: 250.")

    contract_allowance_id = fields.One2many('contract.allowance',string='Contract Allowance',
                                            inverse_name='hr_contract_id')
    contract_nontaxable_allowance_id = fields.One2many('contract.nontaxable.allowance',string='Contract Non-Taxable Allowance',
                                            inverse_name='hr_contract_id')
    # alw1 = fields.Float("1) Petrol card, petrol allowance, travelling allowance \
    # or toll payment or any of its combination for official duties.")
    #
    # alw2 = fields.Float("2) Child care allowance in respect of children up to \
    # 12 years of age.")
    #
    # alw3 = fields.Float("3) Gift of fixed line telephone, mobile phone, pager \
    # or PDA including cost of registration and installation.")
    #
    # alw4 = fields.Float("4) Monthly bills for subscription of broadband, \
    # fixed line telephone, mobile phone,pager and PDA including cost of \
    # registration and installation.")
    #
    # alw5 = fields.Float("5) Perquisite (whether in money or otherwise) provided \
    # to the employee pursuant to his employment.")
    #
    # alw6 = fields.Float("6) Parking rate and parking allowance. This includes \
    # parking rate paid by the employer directly to the parking operator.")
    #
    # alw7 = fields.Float("7) Meal allowance received on a regular basis and \
    # given at the same rate to all employees.")
    #
    # alw8 = fields.Float("8) Subsidised interest for housing, education or \
    # car loan.")

    is_prev_employments = fields.Boolean("Previous Employment")
    prev_empl_mnth = fields.Selection([('1', 'January'), ('2', 'February'),
                                       ('3', 'March'), ('4', 'April'),
                                       ('5', 'May'), ('6', 'June'),
                                       ('7', 'July'), ('8', 'August'),
                                       ('9', 'September'), ('10', 'October'),
                                       ('11', 'November'), ('12', 'December')
                                       ], "Employment Month")

    wage_to_pay = fields.Float('Wage To Pay')
    bik_vola_emp = fields.Float('BIK(Monthly)', help="Employee who has \
    benefits-in-kind (BIK)\n as part \
    of his monthly remuneration shall deduct PCB as per normal remuneration.")
    vola_emp = fields.Float('Vola (Monthly)',
                            help="Employee who has value of living "
                            "accommodation (VOLA) as part of his monthly"
                            " remuneration shall deduct PCB as per normal"
                            " remuneration.")
    esos_emp = fields.Float(
        "ESOS", help="Employee who has value of share option scheme")
    default_pcb_amount = fields.Float(string="Default PCB")
    # not_applicable = fields.Char("N/A", default="N/A")
    # applicable_boolean = fields.Boolean("Applicable ?", default=False)
        # @api.onchange('employee_id')
    # def onchange_employee_contract(self):
    #     self.struct_id = None
    #     all_structure_id = self.env['hr.payroll.structure'].search([]).ids
    #     if self.employee_id.is_non_permanent_employee:
    #         structure_ids = self.env['hr.payroll.structure'].search([('name', 'ilike', 'Non-Permanent Employee')]).ids
    #         return {'domain': {'struct_id': [('id', 'in', structure_ids)]}}
    #     else:
    #         return {'domain': {'struct_id': [('id', 'in',all_structure_id)]}}


    @api.model
    def create(self, vals):
        allowance_list = ['Car Allowance','Fuel Allowance','Insurance Allowance','Rental Allowance']
        vals.update({
            'name': self.env['ir.sequence'].next_by_code('hr.contract')})
        res = super(HrContract, self).create(vals)
        for allowance in allowance_list:
            self.env['contract.allowance'].create({
                'hr_contract_id': res.id,
                'name': allowance,
                'allowance_amount': 0
            })
        return res


    @api.model
    def reminder_to_change_year_number(self):
        sequence_brw = self.env['ir.sequence'].search([
            ('code', '=', 'hr.contract')])
        sequence_brw.write({'number_next': 1})
        return True



class HrPayslipRun(models.Model):

    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'

    @api.constrains('date_start', 'date_end')
    def _check_payslip_date(self):
        if self.date_start > self.date_end:
            raise ValidationError("Date From' must be before 'Date To")

    @api.multi
    def open_payslip_employee(self):
        context = dict(self._context) or {}
        if not self.ids:
            return True
        context.update({
            'default_date_start': self.date_start,
            'default_date_end': self.date_end
        })
        return {'name': ('Payslips by Employees'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.payslip.employees',
                'type': 'ir.actions.act_window',
                'target': 'new',
                }


class HrPayslipEmployees(models.TransientModel):

    _inherit = 'hr.payslip.employees'

    date_start = fields.Date('Date From')
    date_end = fields.Date('Date To')

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'
                                  ].browse(active_id).read(['date_start',
                                                            'date_end',
                                                            'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) \
                                to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'
                                 ].with_context(date_from=from_date,
                                                date_to=to_date,
                                                employee_id=employee.id,
                                                contract_id=False
                                                ).onchange_employee_id_new()
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].
                                   get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].
                                         get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}


class ContractCategoryMrb(models.Model):

    _name = 'contract.category.mrb'
    _description = "Contract Category PCB"

    name = fields.Char('Name', size=64)
    con_cat_line_ids = fields.One2many('contract.category.mrb.line',
                                       'con_catg_mrb_id', "PCB Lines")


class ContractCategoryMrbLine(models.Model):

    _name = 'contract.category.mrb.line'
    _description = "Contract Category PCB Line"

    from_amount = fields.Float('From Amount')
    to_amount = fields.Float('To Amount')
    m_amount = fields.Float('M (RM)')
    r_amount = fields.Float('R (%)')
    b13_amount = fields.Float('B (Category 1 & 3) Amount')
    b2_amount = fields.Float('B (Category 2) Amount')
    con_catg_mrb_id = fields.Many2one('contract.category.mrb', "Category")


class PcbSalaryRule(models.Model):

    _name = 'pcb.salary.rule'
    _description = "PCB Salary Rule"

    p_from = fields.Float('From')
    to = fields.Float('To')
    k = fields.Float('K')
    ka1 = fields.Float('KA1')
    ka2 = fields.Float('KA2')
    ka3 = fields.Float('KA3')
    ka4 = fields.Float('KA4')
    ka5 = fields.Float('KA5')
    ka6 = fields.Float('KA6')
    ka7 = fields.Float('KA7')
    ka8 = fields.Float('KA8')
    ka9 = fields.Float('KA9')
    ka10 = fields.Float('KA10')
    ka11 = fields.Float('KA11')
    ka12 = fields.Float('KA12')
    ka13 = fields.Float('KA13')
    ka14 = fields.Float('KA14')
    ka15 = fields.Float('KA15')
    ka16 = fields.Float('KA16')
    ka17 = fields.Float('KA17')
    ka18 = fields.Float('KA18')
    ka19 = fields.Float('KA19')
    ka20 = fields.Float('KA20')


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('slip_id', 'slip_id.state')
    def _check_slip_state(self):
        for slip in self:
            if slip.slip_id.state == 'done':
                slip.done_state = True

    done_state = fields.Boolean(compute="_check_slip_state", string="Done")


class HrPayslipInput(models.Model):

    _inherit = 'hr.payslip.input'
    _order = 'sequence asc'

    @api.constrains('code')
    def check_input_code(self):
        for line in self:
            input_ids = line.search([('code', '=', line.code),
                                     ('payslip_id', '=', line.payslip_id.id)])
            for ele in input_ids:
                if input_ids and len(input_ids) > 1:
                    raise ValidationError("You can not add same input"
                                          " code: %s" % ele.name)


class HrExpenseSheet(models.Model):

    _inherit = 'hr.expense.sheet'

    payslip_ids = fields.Many2many('hr.payslip', string="Payslips")
    month = fields.Selection([(1, 'Jan'),
                              (2, 'Feb'),
                              (3, 'Mar'),
                              (4, 'Apr'),
                              (5, 'May'),
                              (6, 'Jun'),
                              (7, 'Jul'),
                              (8, 'Aug'),
                              (9, 'Sep'),
                              (10, 'Oct'),
                              (11, 'Nov'),
                              (12, 'Dec')], string='Month', required=True,
                             default=get_default_month)
    year = fields.Selection([(num, str(num)) for num in range(((datetime.now(
    ).year) - 1), ((datetime.now().year) + 100))], default=get_default_year, string="Year")

    @api.multi
    def view_payslip(self):
        action = self.env.ref(
            'hr_payroll.action_view_hr_payslip_form').read()[0]
        action['views'] = [
            (self.env.ref('hr_payroll.view_hr_payslip_tree').id, 'tree'),
            (self.env.ref('hr_payroll.view_hr_payslip_form').id, 'form')]
        action['domain'] = [
            ('id', 'in', self.payslip_ids and self.payslip_ids.ids or [])]
        return action

    @api.constrains('expense_line_ids', 'employee_id')
    def _check_employee(self):
        for sheet in self:
            if not self.env.user.has_group('hr_expense.group_hr_expense_manager'):
                employee_ids = sheet.expense_line_ids.mapped('employee_id')
                if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
                    raise ValidationError(
                        _('You cannot add expenses of another employee.'))


class HrExpense(models.Model):

    _inherit = 'hr.expense'

    type_of_expense = fields.Selection(
        [('subjected_to_pcb', 'Subjected to PCB'),
         ('not_subjected_to_pcb', 'Not Subjected to PCB')],
        string="Type of Expense", default='not_subjected_to_pcb')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(HrExpense, self)._onchange_product_id()
        if self.product_id:
            self.type_of_expense = self.product_id.type_of_expense


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    type_of_expense = fields.Selection(
        [('subjected_to_pcb', 'Subjected to PCB'),
         ('not_subjected_to_pcb', 'Not Subjected to PCB')],
        string="Type of Expense", default='not_subjected_to_pcb')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    type_of_expense = fields.Selection(
        [('subjected_to_pcb', 'Subjected to PCB'),
         ('not_subjected_to_pcb', 'Not Subjected to PCB')],
        string="Type of Expense", default='not_subjected_to_pcb')


class ContractAllowance(models.Model):

    _name = 'contract.allowance'
    _description = "Contract Allowance"

    hr_contract_id = fields.Many2one('hr.contract','Contract Id')
    name = fields.Char('Name',required=True,track_visibility='onchange')
    allowance_amount = fields.Float('Allowance Amount',required=True,track_visibility='onchange',digits=(6,2))
    # allowance_amount = fields.Integer('Allowance Amount',required=True,track_visibility='onchange')

    @api.model
    def create(self, vals):
        res = super(ContractAllowance, self).create(vals)
        return res


class ContractNonTaxableAllowance(models.Model):

    _name = 'contract.nontaxable.allowance'
    _description = "Contract Allowance"

    hr_contract_id = fields.Many2one('hr.contract','Contract Id')
    name = fields.Char('Name',required=True,track_visibility='onchange')
    allowance_amount = fields.Float('Allowance Amount',required=True,track_visibility='onchange',digits=(6,2))

    @api.model
    def create(self, vals):
        res = super(ContractNonTaxableAllowance, self).create(vals)
        return res
