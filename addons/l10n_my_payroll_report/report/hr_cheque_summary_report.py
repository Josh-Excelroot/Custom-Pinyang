# See LICENSE file for full copyright and licensing details

import time
from odoo import api, models


class HrChequeSummaryReport(models.AbstractModel):
    _name = "report.l10n_my_payroll_report.cheque_summary_report_tmp"
    _description = "Cheque Summary Report"

    def get_info(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_end') or False
        name = data.get('employee_ids') or False
        slip_obj = self.env['hr.payslip']
        emp_obj = self.env['hr.employee']
        states = ['draft', 'done', 'verify']
        result = {}
        payslip_data = {}
        department_info = {}
        final_result = {}
        employee_ids = emp_obj.search([('id', 'in', name),
                                       ('department_id', '=', False)])
        department_total_amount = 0.0
        for employee in employee_ids:
            payslip_ids = []
            if employee.bank_account_id:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('pay_by_cheque', '=', True),
                                           ('state', 'in', states)])
                if slip_id:
                    payslip_ids.append(slip_id[0])
            else:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('state', 'in', states)
                                           ])
                if slip_id:
                    payslip_ids.append(slip_id[0])
            net = 0.0
            if not payslip_ids:
                continue
            cheque_number = ''
            for payslip in payslip_ids:
                if not cheque_number:
                    cheque_number = payslip.cheque_number
                if not payslip.employee_id.department_id.id:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
            payslip_data = {
                            'employee_id': employee.user_id and \
                                employee.user_id.login or ' ',
                            'employee_name':employee.name or ' ',
                            'cheque_number':cheque_number,
                            'amount':net,
                            }
            department_total_amount += net
            if 'Undefine' in result:
                result.get('Undefine').append(payslip_data)
            else:
                result.update({'Undefine': [payslip_data]})
        department_total = {'total': department_total_amount,
                            'department_name': "Total Undefine"}
        if 'Undefine' in department_info:
            department_info.get('Undefine').append(department_total)
        else:
            department_info.update({'Undefine': [department_total]})
        for hr_department in self.env['hr.department'].search([]):
            employee_ids = emp_obj.search([('id', 'in', name),
                                           ('department_id', '=',
                                            hr_department.id)])
            department_total_amount = 0.0
            for employee in employee_ids:
                payslip_ids = []
                if employee.bank_account_id:
                    slip = slip_obj.search([('date_from', '>=', date_from),
                                            ('date_from','<=',date_to),
                                            ('employee_id', '=' ,employee.id),
                                            ('pay_by_cheque', '=', True),
                                            ('state', 'in', states)
                                            ])
                    if slip:
                        payslip_ids.append(slip[0])
                else:
                    slip_id = slip_obj.search([('date_from', '>=', date_from),
                                               ('date_from','<=',date_to),
                                               ('state', 'in', states),
                                               ('employee_id', '=',employee.id)
                                               ])
                    if slip_id:
                        payslip_ids.append(slip_id[0])
                net = 0.0
                if not payslip_ids:
                    continue
                cheque_number = ''
                for payslip in payslip_ids:
                    if not cheque_number:
                        cheque_number = payslip.cheque_number
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
                payslip_data = {
                        'employee_id': employee.user_id and \
                            employee.user_id.login or ' ',
                        'employee_name':employee.name or ' ',
                        'cheque_number':cheque_number,
                        'amount':net,
                        }
                department_total_amount += net
                if hr_department.id in result:
                    result.get(hr_department.id).append(payslip_data)
                else:
                    result.update({hr_department.id: [payslip_data]})
            department_total = {'total': department_total_amount,
                                'department_name': "Total "+hr_department.name
                                }
            if hr_department.id in department_info:
                department_info.get(hr_department.id).append(department_total)
            else:
                department_info.update({hr_department.id: [department_total]})
        for key, val in result.items():
            final_result[key] = {'lines': val,
                                 'departmane_total': department_info[key] 
                                 }
        return final_result.values()

    def get_total(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_end') or False
        name = data.get('employee_ids') or False
        slip_obj = self.env['hr.payslip']
        states = ['draft', 'done', 'verify']
        total_ammount = 0
        payslip_ids = []
        for employee in self.env['hr.employee'].search([('id', 'in', name)]):
            if employee.bank_account_id:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('pay_by_cheque', '=', True),
                                           ('state', 'in', states)
                                         ])
                if slip_id:
                    payslip_ids.append(slip_id[0])
            else:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('state', 'in', states)
                                         ])
                if slip_id:
                    payslip_ids.append(slip_id[0])
        if payslip_ids:
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        total_ammount+=line.total
        return total_ammount

    def get_totalrecord(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_end') or False
        name = data.get('employee_ids') or False
        states = ['draft', 'done', 'verify']
        slip_obj = self.env['hr.payslip']
        emp_list = []
        for employee in self.env['hr.employee'].search([('id', 'in', name)]):
            payslip_ids = []
            if employee.bank_account_id:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('pay_by_cheque', '=', True),
                                           ('state', 'in', states)
                                           ])
                if slip_id:
                    payslip_ids.append(slip_id[0])
            else:
                slip_id = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from','<=',date_to),
                                           ('employee_id', '=' , employee.id),
                                           ('state', 'in', states)
                                           ])
                if slip_id:
                    payslip_ids.append(slip_id[0])
            for payslip in payslip_ids:
                if payslip.employee_id.id not in emp_list:
                    emp_list.append(payslip.employee_id.id)
        return len(emp_list)

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        data = docs.read([])[0]
        docargs={
            'doc_ids':self.ids,
            'doc_model':self.model,
            'data':data,
            'docs':docs,
            'time':time,
            'get_info': self.get_info(data),
            'get_totalrecord': self.get_totalrecord(data),
            'get_total': self.get_total(data),
            }
        return docargs
#        return report.render('l10n_my_payroll_report.cheque_summary_report_tmp',
#                             docargs)
