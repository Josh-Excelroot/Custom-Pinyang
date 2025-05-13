# See LICENSE file for full copyright and licensing details

import xlwt
import time
import base64
import locale
from datetime import datetime
from dateutil import relativedelta
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class ExcelExportSummay(models.TransientModel):

    _name = "excel.export.summay"
    _description = "Excel Summary"

    file= fields.Binary("Click On Download Link To Download Xls File",
                        readonly=True)
    name= fields.Char("Name" , size=32, default='Bank_summary.xls')


class ViewBankSummaryReportWizard(models.TransientModel):

    _name = 'view.bank.summary.report.wizard'
    _description = "Bank Summary Report"

    employee_ids= fields.Many2many('hr.employee', 'ppm_hr_employee_bank_rel',
                                   'emp_id','employee_id','Employee Name',
                                   required=False)
    date_start = fields.Date('Date Start',
                             default = lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date('Date End',
                           default = lambda *a: str(datetime.now() + \
                    relativedelta.relativedelta(months = +1, day = 1,
                                                days = -1))[:10])
    export_report= fields.Selection([('pdf','PDF'),('excel','Excel')] ,
                                    "Export", default='pdf')
    
    @api.constrains('date_start','date_end')
    def check_date(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def print_bank_summary_report(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(context)
        data = self.read()[0]
        start_date = data.get('date_start', False)
        end_date = data.get('date_end', False)
        emp_ids = data.get('employee_ids', False) or []
        for employee in self.env['hr.employee'].browse(emp_ids):
            if not employee.bank_account_id:
                raise ValidationError(_('There is no Bank Account define for %s employee.' % (employee.name)))
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', emp_ids),
                                                     ('date_from', '>=', start_date),
                                                     ('date_from', '<=', end_date),
                                                     ('pay_by_cheque', '=', False),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
        if not payslip_ids.ids:
            raise ValidationError(_('There is no payslip details available '\
                                    'for bank between selected date %s and %s') % (start_date, end_date))
        res_user = self.env["res.users"].browse(uid)
        if data.get("export_report") == "pdf":
            data.update({'currency': " " + ustr(res_user.company_id.currency_id.symbol), 'company': res_user.company_id.name})
            datas = {
                'ids': [],
                'form': data,
                'model':'hr.payslip',
                'date_from':start_date,
                'date_to':end_date
            }
            return self.env.ref('l10n_my_payroll_report.hr_bank_summary'\
                                '_report').report_action(self, data=datas)
        else:
            context.update({'employee_ids': data['employee_ids'], 'date_from': start_date, 'date_to': end_date})
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Sheet 1')
            font = xlwt.Font()
            font.bold = True
            header = xlwt.easyxf('font: bold 1, height 280')
            res_user = self.env["res.users"].browse(uid)
            start_date = context.get("date_from")
            start_date_formate = start_date.strftime('%d/%m/%Y')
            end_date = context.get("date_to")
            end_date_formate = end_date.strftime('%d/%m/%Y')
            start_date_to_end_date = ustr(start_date_formate) + ' To ' + ustr(end_date_formate)
            style = xlwt.easyxf('align: wrap yes')
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.row(0).height = 500
            worksheet.row(1).height = 500
            worksheet.write(0, 0, "Company Name" , header)
            worksheet.write(0, 1, res_user.company_id.name,header)
            worksheet.write(0, 7, "By Bank",header)
            worksheet.write(1, 0, "Period",header)
            worksheet.write(1, 1, start_date_to_end_date,header)
            worksheet.col(9).width = 5000
            worksheet.col(11).width = 5000
            borders = xlwt.Borders()
            borders.top = xlwt.Borders.MEDIUM
            borders.bottom = xlwt.Borders.MEDIUM
            border_style = xlwt.XFStyle() # Create Style
            border_style.borders = borders
            payslip_obj = self.env['hr.payslip']
            employee_obj = self.env['hr.employee']
            row = 2
            employee_ids = employee_obj.search([('bank_account_id','!=',False),
                                                ('id', 'in', context.get("employee_ids")),
                                                ('department_id', '=', False)
                                                ])
            if employee_ids:
                payslip_ids = payslip_obj.search([('date_from', '>=', context.get("date_from")),
                                                           ('date_from','<=',context.get("date_to")),
                                                           ('employee_id', 'in' , employee_ids.ids),
                                                           ('pay_by_cheque','=',False),
                                                           ('state', 'in', ['draft', 'done', 'verify'])
                                                           ])
                if payslip_ids:
                    row = 4
                    worksheet.write(4, 0, "",border_style)
                    worksheet.write(4, 1, "Employee Name" ,border_style)
                    worksheet.write(4, 2, "",border_style)
                    worksheet.write(4, 3, "Employee Login"  , border_style)
                    worksheet.write(4, 4, "",border_style)
                    worksheet.write(4, 5, "Name Of Bank",border_style)
                    worksheet.write(4, 6, "",border_style)
                    worksheet.write(4, 7, "Bank Code",border_style)
                    worksheet.write(4, 8, "",border_style)
                    worksheet.write(4, 9, "Account Number",border_style)
                    worksheet.write(4, 10, "",border_style)
                    worksheet.write(4, 11, "Branch Code",border_style)
                    worksheet.write(4, 12, "",border_style)
                    worksheet.write(4, 13, "Amount" ,border_style)
                    
                    row += 1
            style = xlwt.easyxf('align: wrap yes',style)
            result = {}
            payslip_data= {}
            department_total_amount = 0.0
            for employee in employee_ids:
                payslip_ids = payslip_obj.search([('date_from', '>=', context.get("date_from")), ('date_from','<=',context.get("date_to")),
                                                  ('employee_id', '=' , employee.id), ('pay_by_cheque','=',False),
                                                  ('state', 'in', ['draft', 'done', 'verify'])
                                                  ])
                net = 0.00
                if not payslip_ids:
                    continue
                for payslip in payslip_ids:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
                net_total = '%.2f' % net
                worksheet.write(row, 1, employee.name )
                worksheet.write(row, 2, "")
                worksheet.write(row, 3, employee and employee.user_id and employee.user_id.login or '' )
                worksheet.write(row, 4, "")
                worksheet.write(row, 5, employee.bank_account_id and employee.bank_account_id[0].bank_name or ''  )
                worksheet.write(row, 6, "")
                worksheet.write(row, 7, employee.bank_account_id and employee.bank_account_id[0].bank_id.bic or '')
                worksheet.write(row, 8, "")
                worksheet.write(row, 9, employee.bank_account_id and employee.bank_account_id[0].acc_number or '' )
                worksheet.write(row, 10, "")
                worksheet.write(row, 11, employee.bank_account_id and employee.bank_account_id[0].branch_id or '')
                worksheet.write(row, 12, "")
                worksheet.write(row, 13, res_user.company_id.currency_id.symbol + ' '+ ustr(locale.format("%.2f", float(net_total), grouping=True)) )
                row+=1
                department_total_amount += net
                if 'Undefine' in result:
                    result.get('Undefine').append(payslip_data)
                else:
                    result.update({'Undefine': [payslip_data]})
            if department_total_amount:
                worksheet.write(row, 0, 'Total Undefine',border_style)
                worksheet.write(row, 1, '',border_style)
                worksheet.write(row, 2, '',border_style)
                worksheet.write(row, 3, '',border_style)
                worksheet.write(row, 4, '',border_style)
                worksheet.write(row, 5, '',border_style)
                worksheet.write(row, 6, '',border_style)
                worksheet.write(row, 7, '',border_style)
                worksheet.write(row, 8, '',border_style)
                worksheet.write(row, 9, '',border_style)
                worksheet.write(row, 10, '',border_style)
                worksheet.write(row, 11, '',border_style)
                worksheet.write(row, 12, '',border_style)
                new_department_total_amount = '%.2f' % department_total_amount
                worksheet.write(row, 13, res_user.company_id.currency_id.symbol + ' '+ ustr(locale.format("%.2f", float(new_department_total_amount), grouping=True)) ,border_style)
                row+=1
            new_department_total_amount1 = '%.2f' % department_total_amount
            department_total = {'total': new_department_total_amount1, 'department_name': 'Total Undefine'}
            department_info = {'Undefine': [department_total]}
    
            for hr_department in self.env['hr.department'].search([]):
                employee_ids = employee_obj.search([('bank_account_id','!=',False),
                                                    ('id', 'in', context.get("employee_ids")),
                                                    ('department_id', '=', hr_department.id)
                                                    ])
                department_total_amount = 0.0
                flag = False
                print_header = True
                for employee in employee_ids:
                    payslip_ids = payslip_obj.search([('date_from', '>=', context.get("date_from")),
                                                      ('date_from','<=',context.get("date_to")),
                                                      ('employee_id', '=' , employee.id), ('pay_by_cheque','=',False),
                                                      ('state', 'in', ['draft', 'done', 'verify'])
                                                      ])
                    net = 0.0
                    if not payslip_ids:
                        continue
                    for payslip in payslip_ids:
                        flag = True
                        for line in payslip.line_ids:
                            if line.code == 'NET':
                                net += line.total
                    if print_header and payslip_ids:
                        row +=2
                        print_header = False
                        worksheet.write(row, 0, "",border_style)
                        worksheet.write(row, 1, "Employee Name" ,border_style)
                        worksheet.write(row, 2, "",border_style)
                        worksheet.write(row, 3, "Employee Login"  , border_style)
                        worksheet.write(row, 4, "",border_style)
                        worksheet.write(row, 5, "Name Of Bank" ,border_style)
                        worksheet.write(row, 6, "",border_style)
                        worksheet.write(row, 7, "Bank Code",border_style)
                        worksheet.write(row, 8, "",border_style)
                        worksheet.write(row, 9, "Account Number",border_style)
                        worksheet.write(row, 10, "",border_style)
                        worksheet.write(row, 11, "Branch Code",border_style)
                        worksheet.write(row, 12, "",border_style)
                        worksheet.write(row, 13, "Amount",border_style)
                        row +=1
                    new_net = '%.2f' % net
                    worksheet.write(row, 1, employee.name or '' )
                    worksheet.write(row, 2, "")
                    worksheet.write(row, 3, employee and employee.user_id and employee.user_id.login or '')
                    worksheet.write(row, 4, "")
                    worksheet.write(row, 5, employee.bank_account_id and employee.bank_account_id[0].bank_name or '' )
                    worksheet.write(row, 6, "")
                    worksheet.write(row, 7, employee.bank_account_id and employee.bank_account_id[0].bank_id.bic or '')
                    worksheet.write(row, 8, "")
                    worksheet.write(row, 9, employee.bank_account_id and employee.bank_account_id[0].acc_number or '')
                    worksheet.write(row, 10, "")
                    worksheet.write(row, 11, employee.bank_account_id and employee.bank_account_id[0].branch_id or '')
                    worksheet.write(row, 12, "")
                    worksheet.write(row, 13, res_user.company_id.currency_id.symbol + ' '+ ustr(locale.format("%.2f", float(new_net), grouping=True)))
                    row+=1
                    department_total_amount += net
                    if hr_department.id in result:
                        result.get(hr_department.id).append(payslip_data)
                    else:
                        result.update({hr_department.id: [payslip_data]})
                if flag:
                    worksheet.write(row, 0, ustr('Total ' + hr_department.name),border_style)
                    worksheet.write(row, 1, '',border_style)
                    worksheet.write(row, 2, '',border_style)
                    worksheet.write(row, 3, '',border_style)
                    worksheet.write(row, 4, '',border_style)
                    worksheet.write(row, 5, '',border_style)
                    worksheet.write(row, 6, '',border_style)
                    worksheet.write(row, 7, '',border_style)
                    worksheet.write(row, 8, '',border_style)
                    worksheet.write(row, 9, '',border_style)
                    worksheet.write(row, 10, '',border_style)
                    worksheet.write(row, 11, '',border_style)
                    worksheet.write(row, 12, '',border_style)
                    new_department_total_amount = '%.2f' % department_total_amount
                    worksheet.write(row, 13, res_user.company_id.currency_id.symbol + ' '+ ustr( locale.format("%.2f", float(new_department_total_amount), grouping=True) ), border_style)
                    row+=1
                new_department_total_amount1 = '%.2f' % department_total_amount
                department_total = {'total': new_department_total_amount1, 'department_name': "Total " + hr_department.name}
                if hr_department.id in department_info:
                    department_info.get(hr_department.id).append(department_total)
                else:
                    department_info.update({hr_department.id: [department_total]})

            row +=1
            worksheet.write(row, 0, "Overall Total",border_style)
            worksheet.write(row, 1, '',border_style)
            worksheet.write(row, 2, '',border_style)
            row +=2
            for key, val in result.items():
                worksheet.write(row, 0, department_info[key][0].get("department_name"))
                worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' '+ ustr(locale.format("%.2f", float(department_info[key][0].get("total")), grouping=True)) )
                row +=1 
            row+=1
            total_ammount = 0
            payslip_ids = payslip_obj.search([('date_from', '>=', context.get("date_from")), ('date_from','<=',context.get("date_to")),
                                              ('employee_id', 'in' , context.get("employee_ids")), ('pay_by_cheque','=',False), ('employee_id.bank_account_id','!=',False),
                                              ('state', 'in', ['draft', 'done', 'verify'])
                                              ])
            if payslip_ids:
                for payslip in payslip_ids:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            total_ammount+=line.total
            new_total_ammount = '%.2f' % total_ammount
            worksheet.write(row, 0, "All")
            worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' '+ ustr(locale.format("%.2f", float(new_total_ammount), grouping=True)))
            fp = BytesIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            res = base64.b64encode(data)
            excel_export_summay_id = self.env['excel.export.summay'].create({'name': 'Bank_summary.xls','file': res})
            return {
              'name': _('Binary'),
              'res_id': excel_export_summay_id.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'excel.export.summay',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context,
              }
