# See LICENSE file for full copyright and licensing details

from datetime import datetime
from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrPayslipDetailsReport(models.AbstractModel):
    _name = "report.l10n_my_payroll_report.hr_payslip_detail_template"
    _description = "Pay Slip Details"

    @api.model
    def get_detail_data(self, employee_ids, date_from, date_to):
        if employee_ids:
            employee_ids = self.env['hr.employee'].browse(employee_ids)
            payslip_ids = self.env['hr.payslip'].search(
                [('employee_id', 'in', employee_ids.ids),
                 ('date_from', '>=', date_from),
                 ('date_to', '<=', date_to)])
            if payslip_ids:
                rec = []
                for payslip in payslip_ids:
                    unpaid = payslip.worked_days_line_ids.filtered(lambda self: self.code == 'Unpaid')
                    basic_list = []
                    basic = []
                    deduction = []
                    contribution = []
                    NO_OF_RECORDS = 7
                    overtime_manual_hours = 0
                    meal_allowance = 0
                    travelling_allowance = 0
                    how_many_hours = 0
                    # payslip_start = datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)
                    start_month = payslip.date_from.strftime('%B %Y')
                    payslip_start = payslip.date_from.strftime('%d %b %Y')
                    # payslip_end = datetime.strptime(payslip.date_to, DEFAULT_SERVER_DATE_FORMAT)
                    payslip_end = payslip.date_to.strftime('%d %b %Y')
                    for input in payslip.input_line_ids:
                        if input.code == 'INPUTOTMANUAL':
                            overtime_manual_hours = input.amount
                        elif input.code == 'IMEAL':
                            meal_allowance = input.amount
                        elif input.code == 'ITRAVELLING':
                            travelling_allowance = input.amount
                        elif input.code == 'PART_TIMER':
                            how_many_hours = input.amount
                    net = 0.0
                    for line in payslip.line_ids:
                        if line.code in ['NET', 'net']:
                            net = line.total
                        if line.category_id.code in ['BASIC', 'ALW', 'ADDT', 'CATBONUS', 'EXP', 'CD']:
                            if len(basic) <= NO_OF_RECORDS and line.total > 0.0:
                                salary_rule_code = line.name
                                if line.code == 'ADDOT':
                                    salary_rule_code = 'OT'
                                    basic.append({'code': salary_rule_code,
                                                  'total': overtime_manual_hours})
                                elif line.code == 'ALW':
                                    other_allowance = line.total
                                    if meal_allowance > 0:
                                        other_allowance -= meal_allowance
                                        basic.append({'code': 'Meal Allowance',
                                                      'total': meal_allowance})
                                    if travelling_allowance > 0:
                                        other_allowance -= travelling_allowance
                                        basic.append({'code': 'Travelling Allowance',
                                                      'total': travelling_allowance})
                                    if other_allowance > 0:
                                        basic.append({'code': salary_rule_code,
                                                      'total': other_allowance})
                                else:
                                    basic.append({'code': salary_rule_code,
                                                  'total': line.total})
                        if line.category_id.code in ['DEDT', 'DEPFE', 'EIS_E', 'SCS_E',
                                                     'CATLHDN', 'ZAKAT', 'DED']:
                            a = 1
                            if len(deduction) <= NO_OF_RECORDS and line.total != 0.0:
                                deduction.append({'dcode': line.name + '(' + str(
                                    unpaid.number_of_days) + ')' if unpaid and line.code == 'UNPAIDLEAVE' else line.name,
                                                  'dtotal': line.total})
                        if line.category_id.code in ['EPF_Y', 'SOCSO_Y', 'COMP', 'EIS_Y', 'HRDF_EMY']:
                            if len(contribution) <= NO_OF_RECORDS and line.total > 0.0:
                                contribution.append({'ccode': line.name,
                                                     'ctotal': line.total})
                    if len(basic) < NO_OF_RECORDS:
                        for res in range(0, NO_OF_RECORDS - len(basic)):
                            basic.append({'code': '', 'total': ''})
                    if len(deduction) < NO_OF_RECORDS:
                        for res in range(0, NO_OF_RECORDS - len(deduction)):
                            deduction.append({'dcode': '', 'dtotal': ''})
                    if len(contribution) < NO_OF_RECORDS:
                        for res in range(0, NO_OF_RECORDS - len(contribution)):
                            contribution.append({'ccode': '', 'ctotal': ''})
                    for res in range(0, NO_OF_RECORDS):
                        result = {'code': basic[res]['code'],
                                  'total': basic[res]['total'] or 0.0,
                                  'dcode': deduction[res]['dcode'],
                                  'dtotal': deduction[res]['dtotal'] or 0.0,
                                  'ccode': contribution[res]['ccode'],
                                  'ctotal': contribution[res]['ctotal'] or 0.0
                                  }
                        basic_list.append(result)
                    annual_leave = self.env['hr.leave.type'].search(
                        [('code', '=', 'AL')], limit=1)
                    sick_leave = self.env['hr.leave.type'].search(
                        [('code', '=', 'SL')], limit=1)
                    annual_days = annual_leave.get_days(
                        payslip.employee_id.id)
                    sick_days = sick_leave.get_days(
                        payslip.employee_id.id)
                    rec.append({
                        'payslip': str(payslip_start) + ' TO ' + str(payslip_end),
                        'login': payslip.employee_id.user_id.login or '',
                        'name': payslip.employee_id.name or '',
                        'emp_no': payslip.employee_id.emp_reg_no or '',
                        'department': payslip.employee_id.department_id.name or '',
                        'post': payslip.employee_id.job_id.name or '',
                        'icno': payslip.employee_id.identification_id or '',
                        'bank': payslip.employee_id.bank_account_id.bank_id.name or '',
                        'account_no': payslip.employee_id.bank_account_id.acc_number or '',
                        'pay_rate': payslip.contract_id.schedule_pay or '',
                        'pay_mode': payslip.contract_id.schedule_pay or '',
                        'basic_rate': payslip.contract_id.wage,
                        'net': net,
                        'basic_list': basic_list,
                        'epf_no': payslip.employee_id.epf_no or '',
                        'hourly_rate_and_hours': "(" + str(how_many_hours) + ' Hours X ' + str(payslip.contract_id.rate_per_hour) + ')' if payslip.employee_id.is_non_permanent_employee else '',
                        'pcb_no': payslip.employee_id.pcb_number or '',
                        'socso': payslip.employee_id.company_id.sosco_number or '',
                        'gender': 'Female' if payslip.employee_id.gender == 'female' else 'Male',
                        'get_date': start_month,
                        'a_total': annual_days[annual_leave.id]['max_leaves'],
                        'a_taken': annual_days[annual_leave.id]['leaves_taken'],
                        'a_bal': annual_days[annual_leave.id]['remaining_leaves'],
                        's_total': sick_days[sick_leave.id]['max_leaves'],
                        's_taken': sick_days[sick_leave.id]['leaves_taken'],
                        's_bal': sick_days[sick_leave.id]['remaining_leaves']})
                return rec

    @api.model
    def _get_report_values(self, docids, data):
        if 'active_model' in self._context and self._context.get('active_model') == 'payslip.details.report.wizard':
            if docids:
                docids = self.env['payslip.details.report.wizard'
                ].browse(docids[0])
            employee_ids = data['form'].get('employee_ids')
            date_from = data['form'].get('date_from')
            date_to = data['form'].get('date_to')
            docargs = {
                'doc_ids': docids,
                'doc_model': self.env.context.get('active_model'),
                'docs': docids,
                'data': data,
                'get_detail_data': self.get_detail_data(employee_ids, date_from, date_to),
            }
            return docargs
        else:
            if docids:
                docids = self.env['hr.payslip'
                ].browse(docids[0])
            employee_ids = docids.employee_id.id
            date_from = docids.date_from
            date_to = docids.date_to
            docargs = {
                'doc_ids': docids,
                'doc_model': 'hr.payslip',
                'docs': docids,
                'data': data,
                'get_detail_data': self.get_detail_data(employee_ids, date_from, date_to),
            }
            return docargs
#        return report.render('l10n_my_payroll_report.hr_payslip_detail_template',
#                             docargs)
