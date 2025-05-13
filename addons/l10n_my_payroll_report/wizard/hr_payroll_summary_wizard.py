# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil import relativedelta
import xlwt
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class HrPayrollSummaryWizard(models.TransientModel):

    _name = 'hr.payroll.summary.wizard'
    _description = "Payroll Summary Wizard"

    employee_ids = fields.Many2many(
        'hr.employee', 'ppm_hr_employe_rel', 'empl_id', 'employee_id',
        'Employee', required=False)
    salary_rule_ids = fields.Many2many(
        'hr.salary.rule', 'ppm_hr_employe_salary_rule_rel', 'salary_rule_id',
        'employee_id', 'Employee payslip')
    date_from = fields.Date(
        'Date From', default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(
        'Date To', default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    file = fields.Binary()
    file_name = fields.Char()

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        if self.date_from > self.date_to:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def print_hr_payroll(self):
        data = self.read()[0]
        start_date = data['date_from']
        end_date = data['date_to']
        emp_ids = data.get('employee_ids', False) or []
        payslip_ids = self.env['hr.payslip'].search([
            ('employee_id', 'in', emp_ids),
            ('date_from', '>=', start_date),
            ('date_from', '<=', end_date),
            ('state', 'in', ['draft', 'done', 'verify'])
        ])
        if not payslip_ids.ids:
            raise ValidationError(
                _('There is no payslip details available between selected date %s and %s') % (start_date, end_date))
        res_user = self.env["res.users"].browse(self._uid)
        data.update({'currency': " " + ustr(res_user.company_id.currency_id.symbol),
                     'company': res_user.company_id.name,
                     'date_from': start_date,
                     'date_to': end_date
                     })
        datas = {
            'ids': [],
            'form': data,
            'model': 'hr.payslip',
        }
        return self.env.ref('l10n_my_payroll_report.hr_payroll_summary_'
                            'receipt_report').report_action(self, data=datas)

    @api.multi
    def print_hr_payroll_xlsx(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Payroll Summary')
        font = xlwt.Font()
        font.bold = True
        style = xlwt.easyxf('align: wrap yes')
        style_string = "font: bold 1"
        style = xlwt.easyxf(style_string)
        style1 = xlwt.easyxf('pattern: pattern solid, fore_colour green;')
        date_format = '%Y-%m-%d'
        date_form = '%b-%y'
        worksheet.col(0).width = 3500
        worksheet.col(1).width = 3500
        worksheet.col(2).width = 3500
        worksheet.col(3).width = 3500
        worksheet.col(4).width = 3500
        worksheet.col(5).width = 3500
        worksheet.col(6).width = 3500
        worksheet.col(7).width = 3500
        worksheet.col(8).width = 3500
        worksheet.col(9).width = 3500
        worksheet.col(10).width = 3500
        worksheet.col(11).width = 3500
        worksheet.col(12).width = 3500
        worksheet.col(13).width = 3500
        worksheet.col(14).width = 3500
        worksheet.col(15).width = 3500
        worksheet.row(0).height = 520
        worksheet.row(1).height = 520
        worksheet.row(2).height = 520
        worksheet.row(3).height = 520
        worksheet.row(4).height = 520
        worksheet.row(5).height = 520
        worksheet.row(6).height = 520
        worksheet.row(7).height = 520
        worksheet.row(8).height = 520
        worksheet.row(9).height = 520
        worksheet.row(10).height = 520
        worksheet.row(11).height = 520
        worksheet.row(12).height = 520
        worksheet.row(13).height = 520
        worksheet.row(14).height = 520
        worksheet.row(15).height = 520
        data = self.read()[0]
        start_date = data['date_from']
        end_date = data['date_to']
        emp_ids = data.get('employee_ids', False) or []
        payslip_ids = self.env['hr.payslip'].search([
            ('employee_id', 'in', emp_ids),
            ('date_from', '>=', start_date),
            ('date_from', '<=', end_date),
            ('state', 'in', ['draft', 'done', 'verify'])
        ])
        row = 1
        col = 0
        worksheet.write_merge(
            col, col,  7, 8, 'Payroll Summary Report', style=style)
        worksheet.write(row, col, 'Period', style=style)
        col += 1
        worksheet.write_merge(row, col, 1, 2, str(self.date_from.strftime(
            date_format)) + ' To ' + str(self.date_to.strftime(date_format)), style=style)
        row += 1
        col = 0
        worksheet.write(row, col, 'Employee Name', style=style1)
        col += 1
        worksheet.write(row, col, 'Month-Year', style=style1)
        col += 1
        worksheet.write(row, col, 'Basic Wage', style=style1)
        col += 1
        worksheet.write(row, col, 'EPF Employer', style=style1)
        col += 1
        worksheet.write(row, col, 'SOCSO Employer', style=style1)
        col += 1
        worksheet.write(row, col, 'EIS Employer', style=style1)
        col += 1
        worksheet.write(row, col, 'HRDF', style=style1)
        col += 1
        worksheet.write(row, col, 'Bonus/Commission', style=style1)
        col += 1
        worksheet.write(row, col, 'Expense/Reimbursement', style=style1)
        col += 1
        worksheet.write(row, col, 'Allowance', style=style1)
        col += 1
        worksheet.write(row, col, 'Overtime', style=style1)
        col += 1
        worksheet.write(row, col, 'Total Payout', style=style1)
        col += 1
        worksheet.write(row, col, 'EPF Employee', style=style1)
        col += 1
        worksheet.write(row, col, 'SOCSO Employee', style=style1)
        col += 1
        worksheet.write(row, col, 'EIS Employee', style=style1)
        col += 1
        worksheet.write(row, col, 'PCB/ZAKAT', style=style1)
        col += 1
        worksheet.write(row, col, 'Net by/Employee', style=style1)
        col += 1
        row += 1
        total_sum = net = twage = exa = exd = gross = cpf = pf = overtime = oth_alw = epfy = scsy = eisy = hrdf = comm = exp = eise = pcb = zkt = exa_com = pcb_zkt = 0.0
        total_pay = total_pcb_zkt = total_exa_com = total_wage = total_net = total_exa = total_comm = total_exd = total_gross = total_cpf = 0.0
        total_pf = total_ot = total_oth_awe = total_epfy = total_scsy = total_eisy = total_hrdf = total_exp = total_eise = total_pcb = total_zkt = 0.0
        for payslip in payslip_ids:
            for rule in payslip.line_ids:
                if rule.code == 'BASIC':
                    twage = rule.total
                    total_wage += twage
                elif rule.code == 'NET':
                    net = rule.total
                    total_net += net
                elif rule.code == 'BONUS':
                    exa = rule.total
                    total_exa += exa
                elif rule.code == 'COMM':
                    comm = rule.total
                    total_comm += comm
                elif rule.category_id.code == 'DED':
                    exd = rule.total
                    total_exd += exd
                elif rule.code == 'GROSS':
                    gross = rule.total
                    total_gross += gross
                elif rule.code == 'DEPFE':
                    cpf = rule.total
                    total_cpf += cpf
                elif rule.code == 'SCSE':
                    pf = rule.total
                    total_pf += pf
                elif rule.code in ['ADDOT', 'OTPH']:
                    overtime = rule.total
                    total_ot += overtime
                elif rule.category_id.code == 'ALW':
                    oth_alw = rule.total
                    total_oth_awe += oth_alw
                elif rule.code == 'EPF_Y_NORMAL':
                    epfy = rule.total
                    total_epfy += epfy
                elif rule.code == 'SCSY':
                    scsy = rule.total
                    total_scsy += scsy
                elif rule.code == 'EISY':
                    eisy = rule.total
                    total_eisy += eisy
                elif rule.code == 'HRDF':
                    hrdf = rule.total
                    total_hrdf += hrdf
                elif rule.code == 'EXP':
                    exp = rule.total
                    total_exp += exp
                elif rule.code == 'EISE':
                    eise = rule.total
                    total_eise += eise
                elif rule.code == 'PCBCURRMONTH':
                    pcb = rule.total
                    total_pcb += pcb
                elif rule.code == ' ZAKAT':
                    zkt = rule.total
                    total_zkt += zkt
                total_sum = twage + epfy + scsy + eisy + \
                    hrdf + exa + comm + exp + oth_alw + overtime
                total_pay = total_wage + total_epfy + total_scsy + total_eisy + \
                    total_hrdf + total_exa + total_comm + total_exp + total_oth_awe + total_ot
                exa_com = (exa + comm)
                pcb_zkt = pcb + zkt
                total_exa_com = total_exa + total_comm
                total_pcb_zkt = total_pcb + total_zkt
            date = payslip.date_from
            col = 0
            worksheet.write(row, col, payslip.employee_id.name, style=style)
            col += 1
            worksheet.write(row, col, str(
                date.strftime(date_form)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(twage)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(epfy)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(scsy)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(eisy)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(hrdf)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(exa_com)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(exp)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(oth_alw)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(overtime)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(total_sum)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(cpf)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(pf)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(eise)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(pcb_zkt)), style=style)
            col += 1
            worksheet.write(row, col, '{0:,.2f}'.format(
                float(net)), style=style)
            col += 1
            row += 1
            col = 0
        worksheet.write(row, col, 'Grand Total', style=style)
        col += 1
        worksheet.write(row, col, '')
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_wage)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_epfy)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_scsy)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_eisy)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_hrdf)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_exa_com)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_exp)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_oth_awe)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_ot)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_pay)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_cpf)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_pf)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_eise)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_pcb_zkt)))
        col += 1
        worksheet.write(row, col, '{0:,.2f}'.format(float(total_wage)))
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.b64encode(data)
        self.write({'file': res})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=hr.payroll.summary.wizard&field=file&download=true&id=%s&filename=Employee Salary Report.xls' % (self.id),
            'target': 'new',
        }
