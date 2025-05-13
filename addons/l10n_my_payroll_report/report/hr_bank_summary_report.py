# See LICENSE file for full copyright and licensing details

import time
from odoo import api, models


class HrBankSummaryReport(models.AbstractModel):

    _name = "report.l10n_my_payroll_report.hr_bank_summary_report_tmp"
    _description = "Bank Summary Report"

    @api.model
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
        employee_ids = emp_obj.search([('bank_account_id', '!=', False),
                                       ('id', 'in', name),
                                       ('department_id', '=', False)])
        department_total_amount = 0.0
        for employee in employee_ids:
            payslip_ids = slip_obj.search([('date_from', '>=', date_from),
                                           ('date_from', '<=', date_to),
                                           ('employee_id', '=', employee.id),
                                           ('pay_by_cheque', '=', False),
                                           ('state', 'in', states)
                                           ])
            net = 0.0
            if not payslip_ids:
                continue
            for payslip in payslip_ids:
                if not payslip.employee_id.department_id.id:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
            payslip_data = {
                'bank_name': employee.bank_account_id and
                employee.bank_account_id.bank_name or '',
                'bank_id': employee.bank_account_id
                and employee.bank_account_id.bank_id.bic or '',
                'branch_id': employee.bank_account_id
                and employee.bank_account_id.branch_id or '',
                'employee_id': employee and employee.user_id
                and employee.user_id.login or ' ',
                'employee_name': employee.name,
                'account_number': employee.bank_account_id
                and employee.bank_account_id.acc_number or '',
                'amount': net,
            }
            department_total_amount += net
            if 'Undefine' in result:
                result.get('Undefine').append(payslip_data)
            else:
                result.update({'Undefine': [payslip_data]})
        department_total = {'total': department_total_amount,
                            'department_name': 'Total Undefine'}
        if 'Undefine' in department_info:
            department_info.get('Undefine').append(department_total)
        else:
            department_info.update({'Undefine': [department_total]})
        for hr_department in self.env['hr.department'].search([]):
            employee_ids = emp_obj.search([('bank_account_id', '!=', False),
                                           ('id', 'in', name),
                                           ('department_id', '=',
                                            hr_department.id)
                                           ])
            department_total_amount = 0.0
            for employee in employee_ids:
                slip_ids = slip_obj.search([('date_from', '>=', date_from),
                                            ('date_from', '<=', date_to),
                                            ('employee_id', '=', employee.id),
                                            ('pay_by_cheque', '=', False),
                                            ('state', 'in', states)
                                            ])
                net = 0.0
                if not slip_ids:
                    continue
                for payslip in slip_ids:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
                payslip_data = {
                    'bank_name': employee.bank_account_id
                    and employee.bank_account_id.bank_name or '',
                    'bank_id': employee.bank_account_id
                    and employee.bank_account_id.bank_id.bic or '',
                    'branch_id': employee.bank_account_id
                    and employee.bank_account_id.branch_id or '',
                    'employee_id': employee and employee.user_id
                    and employee.user_id.login or ' ',
                    'employee_name': employee.name,
                    'account_number': employee.bank_account_id
                    and employee.bank_account_id.acc_number or '',
                    'amount': net,
                }
                department_total_amount += net
                if hr_department.id in result:
                    result.get(hr_department.id).append(payslip_data)
                else:
                    result.update({hr_department.id: [payslip_data]})
            department_total = {'total': round(department_total_amount, 2),
                                'department_name': "Total " + hr_department.name}
            if hr_department.id in department_info:
                department_info.get(hr_department.id).append(department_total)
            else:
                department_info.update({hr_department.id: [department_total]})
        for key, val in result.items():
            final_result[key] = {'lines': val,
                                 'departmane_total': department_info[key]}
        return final_result.values()

    @api.model
    def get_total(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_end') or False
        name = data.get('employee_ids') or False
        total_ammount = 0
        domain = [('date_from', '>=', date_from),
                  ('pay_by_cheque', '=', False),
                  ('employee_id.bank_account_id', '!=', False),
                  ('date_from', '<=', date_to),
                  ('employee_id', 'in', name),
                  ('state', 'in', ['draft', 'done', 'verify'])
                  ]
        payslip_ids = self.env['hr.payslip'].search(domain)
        if payslip_ids:
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        total_ammount += line.total
        return total_ammount

    @api.model
    def get_totalrecord(self, data):
        emp_list = []
        date_from = data.get('date_start') or False
        date_to = data.get('date_end') or False
        name = data.get('employee_ids') or False
        states = ['draft', 'done', 'verify']
        employee_ids = self.env['hr.employee'
                                ].search([('bank_account_id', '!=', False),
                                          ('id', 'in', name)])
        for employee in employee_ids:
            slip_ids = self.env['hr.payslip'
                                ].search([('date_from', '>=', date_from),
                                          ('date_from', '<=', date_to),
                                          ('employee_id', '=', employee.id),
                                          ('pay_by_cheque', '=', False),
                                          ('state', 'in', states)
                                          ])
            if slip_ids and slip_ids.ids:
                emp_list.append(employee.id)
        return len(emp_list)

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        data = docs.read([])[0]
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
            'time': time,
            'get_info': self.get_info(data),
            'get_totalrecord': self.get_totalrecord(data),
            'get_total': self.get_total(data),
        }
        return docargs
