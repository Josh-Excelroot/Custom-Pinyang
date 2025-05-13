# _*_ coding: utf-8
from odoo import models, fields, api, _
from datetime import datetime

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object


def get_MMM_month(month_int):
    return {
        1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
        7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
    }[month_int]


class BankBulkPaymentReportXlsx(models.AbstractModel):
    _name = 'report.l10n_my_payroll_report.bank_bulk_payment_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def set_vars(self):
        self.vars = {
            'headers_data': [],
            'headers_data_row_col': (0, 0),
            'rows_data': [],
            'rows_data_row_col': (1, 0),
            'sheet_name': 'Bulk Salary Payment',
            'print_report_name': "'%s - %s_%s' % (object.bulk_payment_file_bank_id.name, object.date_start, object.end_date)",
            'sql_columns': '',
            'sql_joins': """LEFT JOIN hr_payslip slip ON slip.id = slip_line.slip_id
            LEFT JOIN hr_employee emp ON emp.id = slip.employee_id
            LEFT JOIN res_partner_bank bank_account ON bank_account.id = emp.bank_account_id
            LEFT JOIN res_bank bank ON bank.id = bank_account.bank_id"""
        }
        if self.bank == 1:  # MBB
            payment_description = f'Salary {get_MMM_month(self.record.date_start.month)}'
            self.vars.update({
                'headers_data': [
                    'Beneficiary Name', 'Beneficiary Bank', 'Beneficiary Account No', 'ID Type', 'ID Number',
                    'Payment Amount', 'Payment Reference', 'Payment Description'
                ],
                'headers_data_row_col': (7, 0),
                'rows_data_row_col': (8, 0),
                'sql_columns': f"emp.name, bank.name, bank_account.acc_number, 'NRIC' as id_type_name, emp.identification_id, slip_line.amount, '', '{payment_description}'",
                'sql_joins': self.vars['sql_joins'] + """\nLEFT JOIN employee_id_type id_type ON id_type.id = emp.employee_type_id"""
            })
        elif self.bank == 2:  # AB
            self.vars.update({
                'headers_data': [
                    'Payment Mode', 'Beneficiary Name', 'Beneficiary Account / DuitNow ID Number',
                    'Beneficiary Bank Code / DuitNow ID Type', 'Amount', 'Payment Description', 'Payment Reference',
                    'Beneficiary New IC No', 'Beneficiary Old IC No', 'Beneficiary Business Registration',
                    'Beneficiary Others'
                ],
                'print_report_name': "'SBP_%s_%s' % (object.date_start, object.end_date)",
                'sql_columns': "'', emp.name, bank_account.acc_number, bank.bic, slip_line.amount, '', '', emp.identification_id, emp.emp_old_ic, '', ''"
            })


    def generate_xlsx_report(self, workbook, data, record):
        valid_banks = {'MBB': 1, 'AB': 2}
        self.bank_name = record.bulk_payment_file_bank_id.name
        if self.bank_name not in valid_banks:
            raise UserError(f'No format specified for bank {self.bank_name}')
        self.bank = valid_banks.get(self.bank_name)
        self.record = record

        self.set_vars()

        self.workbook = workbook
        self.sheet = self.workbook.add_worksheet(self.vars['sheet_name'])

        self.set_content()
        self.env.ref('l10n_my_payroll_report.action_bank_bulk_payment_report_xlsx').sudo().print_report_name = self.vars['print_report_name']
        self.generate()

    def set_content(self):
        sql = f"""SELECT {self.vars['sql_columns']} FROM hr_payslip_line slip_line 
        {self.vars['sql_joins']}
        where slip.id in {str(tuple(self.record.payslip_ids.ids))} and slip_line.code = 'NET';"""

        self.env.cr.execute(sql)
        self.vars['rows_data'] = self.env.cr.fetchall()

    def generate(self):
        row, col = self.vars['headers_data_row_col']
        for header in self.vars['headers_data']:
            self.sheet.set_column(col, col, 20)
            self.sheet.write_string(row, col, header)
            col += 1

        row, col = self.vars['rows_data_row_col']
        for data in self.vars['rows_data']:
            for d in data:
                self.sheet.write_string(row, col, str(d or ''))
                col += 1
            row += 1
            col = self.vars['rows_data_row_col'][1]

        if self.bank == 1:
            self.extra_for_maybank()

    def extra_for_maybank(self):
        self.sheet.merge_ranbasicge(1, 0, 1, 1, 'Employer Info :')
        self.sheet.write_string(2, 0, 'Crediting Date (eg. dd/MM/yyyy)')
        self.sheet.write_string(2, 1, datetime.now().strftime('%d/%m/%Y'))
        self.sheet.write_string(3, 0, 'Payment Reference')
        self.sheet.write_string(4, 0, 'Payment Description')
        self.sheet.write_string(4, 1, f'Salary {get_MMM_month(self.record.date_start.month)}')
        self.sheet.write_string(5, 0, 'Bulk Payment Type')
        self.sheet.write_string(5, 1, 'Salary')

        self.sheet.merge_range(2, 3, 2, 6, 'Please save this template to .csv (comma delimited) file before uploading the file via M2U Biz')


