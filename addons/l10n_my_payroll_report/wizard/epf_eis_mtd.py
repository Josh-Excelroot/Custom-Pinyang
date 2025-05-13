
import time
import xlwt
import base64
import locale
from datetime import datetime
from io import BytesIO
import xlsxwriter
from odoo.exceptions import UserError
from dateutil import relativedelta
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, ustr


class masterReportOut(models.TransientModel):
    _name = 'master.report.out'

    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)


class EpfSocsoEisMtdDownload(models.TransientModel):

    _name = 'epf.socso.eis.mtd.download'
    _description = 'EPF/SOCSO/EIS/MTD Download'

    type = fields.Selection([('EPF', 'EPF'), ('SOCSO/EIS', 'SOCSO/EIS'),('MTD','PCB(MTD)')], string="Download For")
    date_start = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # def download_csv_file(self):
    #     if self:
    #         print(self)

    def download_csv_file(self):
        data = base64.encodebytes(self.generate_xlsx_reports())
        name=""
        if self.type == "EPF":
            name="EPF"
        elif self.type == "SOCSO/EIS":
            name="SOCSO/EIS"
        else:
            name="PCB/MTD"
        report_name = name+'.xlsx'
        
        report_id = self.env['master.report.out'].create(
            {'filedata': data, 'filename': report_name})

        return {
            'name': _('Dowaload CSV'),
            'res_id': report_id.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'master.report.out',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def generate_xlsx_reports(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': 1})
        main_heading = workbook.add_format({
            "bold": 1,
            "border": 1,
            "align": 'center',
            "valign": 'vcenter',
            "font_color": 'black',
            "bg_color": 'white',
            'font_size': '9',
        })
        main_heading2 = workbook.add_format({
            "bold": 1,
            "border": 2,
            "align": 'center',
            "valign": 'vcenter',
            "font_color": 'black',
            "bg_color": 'white',
            'font_size': '9',
        })
        work_heading = workbook.add_format({
            "border": 1,
            "align": 'center',
            "valign": 'vcenter',
            "font_color": 'black',
            "bg_color": 'white',
            'font_size': '9',
        })
        # Adjust the column width.
        worksheet.set_column(1, 1, 15)
        if self.type == "EPF":
            ####   Label Information of Class  ####
            # worksheet.write('A1', 'Member No', main_heading)
            # worksheet.write('B1', 'IC No', main_heading)
            # worksheet.write('C1', 'Name', main_heading)
            # worksheet.write('D1', 'Wages', main_heading)
            # worksheet.write('E1', 'EM Share', main_heading)
            # worksheet.write('F1', 'EMP Share', main_heading)

            if self.date_start and self.end_date:
                payslip_record = self.env['hr.payslip'].sudo().search(
                    [('date_from', '>=', self.date_start), ('date_to', '<=', self.end_date)])

                row = 1
                col = 1
                for record in payslip_record:
                    employee_epf_no = record.employee_id.epf_no if record.employee_id.epf_no else ''
                    employee_name = record.employee_id.name
                    employee_id_no = record.employee_id.identification_id if record.employee_id.identification_id else ''
                    worksheet.write(row, col-1, str(employee_epf_no))
                    worksheet.write(row, col, str(employee_id_no))
                    worksheet.write(row, col + 1, str(employee_name))
                    for line_id in record.line_ids:
                        em_share = 0
                        emp_share = 0
                        basic_wages = 0
                        if line_id.name == "EPF (Employer)":
                            emp_share = line_id.total
                            # print(line_id.total,emp_share)  ## employee share em_share                        worksheet.write(row,col+4,str(emp_share))
                            worksheet.write(row,col+4,str(emp_share))
                        if line_id.name == "EPF (Employee)":
                            em_share = line_id.total
                            worksheet.write(row, col + 3, str(em_share))
                            # print(line_id.total,em_share)  ## employer share emp_share
                        if line_id.code == 'BASIC':
                            basic_wages = round(line_id.total,2)
                            worksheet.write(row, col + 2, str(basic_wages))
                    row += 1
            else:
                raise UserError("No Data Found")

            workbook.close()
            fp.seek(0)
            result = fp.read()
            return result
        elif self.type == "SOCSO/EIS":
            ####   Label Information of Class  ####
            # worksheet.write('A1', 'Employer No', main_heading)
            # worksheet.write('B1', 'MyCoID', main_heading)
            # worksheet.write('C1', 'Identification Number / SOCSO Foreign Worker Number', main_heading)
            # worksheet.write('D1', 'Employee Name', main_heading)
            # worksheet.write('E1', 'Month Contribution', main_heading)
            # worksheet.write('F1', 'Employee Salary', main_heading)
            # worksheet.write('G1', 'Contribution Amount SOCSO (Employer share)', main_heading)
            # worksheet.write('H1', 'Contribution Amount SOCSO (Employee share)', main_heading)
            # worksheet.write('I1', 'Contribution Amount EIS (Employer share)', main_heading)
            # worksheet.write('J1', 'Contribution Amount EIS (Employee share)', main_heading)
            # worksheet.write('K1', 'Filler 1', main_heading)

            if self.date_start and self.end_date:
                payslip_record = self.env['hr.payslip'].sudo().search(
                    [('date_from', '>=', self.date_start), ('date_to', '<=', self.end_date)])

                row = 1
                col = 1
                for record in payslip_record:
                    employee_no = record.employee_id.id
                    employee_socso_no = record.employee_id.no_perkeso
                    employee_name = record.employee_id.name
                    worksheet.write(row, col - 1, str(employee_no))
                    worksheet.write(row, col, record.employee_id.company_id.company_registry)
                    worksheet.write(row, col + 1, str(employee_socso_no))
                    worksheet.write(row, col + 2, str(employee_name))
                    worksheet.write(row, col + 3, str(record.date_from.month)) ## MONTH CONTIBUTION
                    for line_id in record.line_ids:
                        em_share_socso = 0
                        emp_share_socso = 0
                        emp_share_eis = 0
                        em_share_eis = 0
                        basic_wages = 0
                        if line_id.name == "SCS (Employer)":
                            emp_share_socso = line_id.total
                            worksheet.write(row, col + 5, str(emp_share_socso))

                        if line_id.name == "SCS (Employee)":
                            em_share_socso = line_id.total
                            worksheet.write(row, col + 6, str(em_share_socso))

                        if line_id.code == 'BASIC':
                            basic_wages = round(line_id.total, 2)
                            worksheet.write(row, col + 4, str(basic_wages))

                        if line_id.name == "EIS (Employer)":
                            emp_share_eis = line_id.total
                            worksheet.write(row, col + 7, str(emp_share_eis))

                        if line_id.name == "EIS (Employee)":
                            em_share_eis = line_id.total
                            worksheet.write(row, col + 8, str(em_share_eis))
                    row += 1
            else:
                raise UserError("No Data Found")

            workbook.close()
            fp.seek(0)
            result = fp.read()
            return result
        else:
            ####   Label Information of Class  ####
            # worksheet.write('A1', 'Member No', main_heading)
            # worksheet.write('B1', 'Name', main_heading)
            # worksheet.write('C1', 'IC No', main_heading)
            # worksheet.write('D1', 'PCB/PCB-38', main_heading)


            if self.date_start and self.end_date:
                payslip_record = self.env['hr.payslip'].sudo().search(
                    [('date_from', '>=', self.date_start), ('date_to', '<=', self.end_date)])

                row = 1
                col = 1
                total_employee = 0
                month_of_export = self.date_start.strftime('%Y') + self.date_start.strftime('%m')
                company_tax_id = self.env.user.company_id.c_number
                final_string_first = str(company_tax_id)+str(month_of_export)
                total_pcb = 0
                total_pcb_paid_by = 0
                total_pcb_cf = 0
                total_pcb_cf_paid_by = 0
                for record in payslip_record:
                    total_employee += 1
                    employee_epf_no = record.employee_id.epf_no if record.employee_id.epf_no else ''
                    employee_name = record.employee_id.name
                    employee_id_no = record.employee_id.identification_id if record.employee_id.identification_id else ''
                    worksheet.write(row, col - 1, str(employee_epf_no))
                    worksheet.write(row, col, str(employee_name))
                    worksheet.write(row, col + 1, str(employee_id_no))
                    pcb_paid = '00000000'
                    pcb_cp_paid = '0000000000'
                    pcb_flag = False
                    pcb_cp_flag = False
                    for line_id in record.line_ids.filtered(lambda x:x.name=='PCB' or x.name=='PCB-CP38'):
                        if line_id.name == "PCB":
                            pcb_paid = line_id.total if line_id.name == 'PCB' else 0
                            total_pcb += pcb_paid
                            # pcb_cp_paid = line_id.total if line_id.name == 'PCB-CP38' else 0
                            pcb_paid = str(pcb_paid).replace(".", "")
                            # pcb_cp_paid = str(pcb_cp_paid).replace(".", "")
                            if len(pcb_paid) < 8:
                                pcb_paid = pcb_paid.zfill(8)
                            total_pcb_paid_by += 1
                            pcb_flag = True
                        if line_id.name == 'PCB-CP38':
                            pcb_cp_paid = line_id.total if line_id.name == 'PCB-CP38' else 0
                            total_pcb_cf += pcb_cp_paid
                            pcb_cp_paid = str(pcb_cp_paid).replace(".", "")
                            if len(pcb_cp_paid) < 8:
                                pcb_cp_paid = pcb_cp_paid.ljust(10, '0')
                            total_pcb_cf_paid_by += 1
                            pcb_cp_flag = True
                    if pcb_flag and pcb_cp_flag:
                        joined_string = pcb_paid + '000' + pcb_cp_paid
                        worksheet.write(row, col + 2, str(joined_string))
                    elif pcb_flag and not pcb_cp_flag:
                        joined_string = pcb_paid + '000' + '0000000000'
                        worksheet.write(row, col + 2, str(joined_string))
                    else:
                        joined_string = '00000000' + '000' + pcb_cp_paid
                        worksheet.write(row, col + 2, str(joined_string))
                    row += 1
                total_pcb = str(total_pcb).replace(".", "")
                total_pcb_cf = str(total_pcb_cf).replace(".", "")
                final_string_first = final_string_first + str(total_pcb) + str(total_pcb_paid_by) + str(total_pcb_cf) + str(total_pcb_cf_paid_by)
                worksheet.write('A1', final_string_first)
            else:
                raise UserError("No Data Found")

            workbook.close()
            fp.seek(0)
            result = fp.read()
            return result
