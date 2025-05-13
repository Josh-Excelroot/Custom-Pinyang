# See LICENSE file for full copyright and licensing details

import time
import xlwt
import base64
import locale
from datetime import datetime
from io import BytesIO
from dateutil import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, ustr


class BankListExportSummay(models.TransientModel):

    _name = 'bank.list.export.summay'
    _description = "Bank List Export Summary"

    file = fields.Binary(
        "Click On Download Link To Download Xls File", readonly=True)
    name = fields.Char("Name", size=32, default="Bank List.xls")


class BankListXls(models.TransientModel):

    _name = 'bank.list.xls'
    _description = "Bank List"

    employee_ids = fields.Many2many(
        'hr.employee', 'ppm_hr_emp_bank_list_xls_rel', 'emp_id', 'employee_id',
        'Employee Name')
    date_start = fields.Date(
        'Date Start', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date('Date End',
                           default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    @api.constrains('date_start', 'date_end')
    def check_date(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def download_bank_list_xls_file(self):
        context = dict(self._context) or {}
        data = self.read()[0]
        context.update({
            'employee_ids': data['employee_ids'],
            'date_start': data['date_start'],
            'date_stop': data['date_end']
            })
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True

        style_header = xlwt.easyxf('font: name Courier New, bold on, color black, height 196; align: wrap off;')
        style_header_underline = xlwt.easyxf('font: name Courier New, bold on, color black, height 196, underline single; align: wrap off;')
        style_header_underline_bold_off = xlwt.easyxf('font: name Courier New, bold off, color black, height 196, underline single; align: wrap off;')
        style_simple = xlwt.easyxf('font: name Courier New, bold off, color black, height 198; align: wrap off;')
        style_simple1 = xlwt.easyxf('font: name Courier New, bold off, color black, height 198; align: wrap off, vert centre, horiz left;')
        style_simple2 = xlwt.easyxf('font: name Courier New, bold off, color black, height 198; align: wrap off, vert centre, horiz right;')

        date_from = context.get('date_start')
        date_to = context.get('date_stop')
        date_formate = datetime.strptime(str(date_to), DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        month_year = datetime.strptime(str(date_to), DEFAULT_SERVER_DATE_FORMAT).strftime('%m/%y')

        row = 0
        worksheet.col(0).width = 2650
        worksheet.col(1).width = 2650
        worksheet.col(2).width = 2650
        worksheet.col(3).width = 2650
        worksheet.col(4).width = 2650
        worksheet.col(5).width = 2650
        worksheet.col(6).width = 2650
        worksheet.col(7).width = 2650
        worksheet.col(8).width = 2650
        worksheet.col(9).width = 2650
        worksheet.col(10).width = 2650
        worksheet.col(11).width = 2650
        worksheet.col(12).width = 3500

        company_name = self.env.user.company_id.name
        worksheet.write(row, 0, company_name, style_header)
        row += 2
        worksheet.write(row, 0, 'NAME', style_header)
        worksheet.write(row, 3, ':', style_header)
        worksheet.write(row, 4, 'BANK ADVICE LISTING', style_header)
        row += 1
        worksheet.write(row, 0, 'PAGE NO. ', style_header)
        worksheet.write(row, 3, ':', style_header)
        worksheet.write(row, 4, '1.00', style_header)
        row += 2
        worksheet.write(row, 0, 'DATE PRINTED', style_header)
        worksheet.write(row, 3, ':', style_header)
        worksheet.write(row, 4, ustr(date_formate or ''), style_header)
        row += 1
        worksheet.write(row, 0, 'PAYROLL FOR MONTH', style_header)
        worksheet.write(row, 3, ':', style_header)
        worksheet.write(row, 4, ustr(month_year or ''), style_header)
        row += 1
        worksheet.write(row, 0, 'PAYMODE', style_header)
        worksheet.write(row, 3, ':', style_header)
        worksheet.write(row, 4, 'Monthly', style_header)
        row += 3
        worksheet.write(row, 0, 'NO.', style_header_underline)
        worksheet.write(row, 1, 'EMPNO', style_header_underline)
        worksheet.write(row, 3, 'NAME', style_header_underline)
        worksheet.write(row, 7, 'IC NO.', style_header_underline)
        worksheet.write(row, 9, 'BANK ACCOUNT', style_header_underline)
        worksheet.write(row, 12, 'AMOUNT', style_header_underline)
        row += 2
        worksheet.write(row, 0, 'Bank : HSBC - HSBC BANK MALAYSIA BERHAD',
                        style_header)
        row += 2
        head_count_row = row
        row += 1
        sequence = 0
        total_net_amount = 0.0
        for emp in self.env['hr.employee'].browse(context.get('employee_ids')):
            payslip_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', emp.id),
                 ('date_from', '>=', date_from),
                 ('date_to', '<=', date_to),
                 ('state', 'in', ['draft', 'done', 'verify'])])
            net_amount = 0.00
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        net_amount += line.total
                        total_net_amount += line.total
            if net_amount:
                sequence += 1
                worksheet.write(row, 0, int(sequence), style_simple1)
                worksheet.write(row, 1, ustr(emp.user_id and emp.user_id.login or ''), style_simple)
                worksheet.write(row, 3, ustr(emp.name or ''), style_simple)
                worksheet.write(row, 7, ustr(emp.identification_id or ''), style_simple)
                worksheet.write(row, 9, ustr(emp.bank_account_id.acc_number or ''), style_simple)
                worksheet.write(row, 12, ustr(locale.format("%.2f", float(net_amount), grouping=True)), style_simple2)
                row += 1

        row += 4
        worksheet.write(head_count_row, 0, '{Head Count - ' + ustr(int(sequence)) + '}', style_header)
        worksheet.write(row, 0, 'Total No. of Records', style_header)
        worksheet.write(row, 3, int(sequence), style_simple1)
        row += 1
        worksheet.write(row, 0, 'GRAND TOTAL :', style_header)
        worksheet.write(row, 12, ustr(locale.format("%.2f", float(total_net_amount), grouping=True)), style_simple2)
        row += 1
        worksheet.write(row, 0, 'Kindly debit our Account Number ', style_simple)
        worksheet.write(row, 4, '303216642001', style_header_underline_bold_off)
        worksheet.write(row, 7, 'to the following amount RM', style_simple)
        worksheet.write(row, 9, ustr(locale.format("%.2f", float(total_net_amount), grouping=True)), style_simple)
        row += 4
        worksheet.write(row, 0, 'Authorised Signature : _______________________', style_simple)
        worksheet.write(row, 9, 'Prepared By : ____________________', style_simple)
        row += 4
        worksheet.write(row, 0, 'Company Chop', style_simple)
        worksheet.write(row, 9, 'Checked By : ____________________', style_simple)
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.b64encode(data)
        summary_vals = {'name': 'Bank List.xls', 'file': res}
        excel_bank_list_export_summay_id = self.env['bank.list.export.summay'
                                                    ].create(summary_vals)
        return {
          'name': _('Binary'),
          'res_id': excel_bank_list_export_summay_id.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'bank.list.export.summay',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
          }
