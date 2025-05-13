# See LICENSE file for full copyright and licensing details

import time
import base64
import tempfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class MtdTextBinaryWizard(models.TransientModel):
    _name = 'mtd.text.binary.wizard'
    _description = "PCB Text Binary Wizard"

    name = fields.Char('Name', size=32)
    rst_file = fields.Binary('Click On DownLoad Link To Download File',
                             readonly=True)


class MtdTxtFileWizard(models.TransientModel):
    _name = 'mtd.txt.file.wizard'
    _description = "PCB TXT File Wizard"

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_mtd_rel',
                                    'mtd_id', 'employees_id',
                                    'Employee')
    date_start = fields.Date('Date Start',
                             default=lambda *a: time.strftime('%Y-%m-01'))
    date_stop = fields.Date('Date End',
                            default=lambda *a: str(datetime.now(
                            ) + relativedelta(months=+1, day=1,
                                              days=-1))[:10])

    @api.constrains('date_start', 'date_stop')
    def check_date(self):
        if self.date_start > self.date_stop:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def download_mtd_txt_file(self):
        context = dict(self._context) or {}
        data = self.read()[0]
        employ_ids = data['employee_ids']
        start_date = data['date_start']
        end_date = data['date_stop']
        if not start_date or not end_date or not employ_ids:
            return False
        mth_of_ded = start_date.strftime('%m')
        year_of_ded = start_date.strftime('%Y')
        file_name_mtd = "Emp_MTD.TXT"
        if mth_of_ded and year_of_ded:
            file_name_mtd = mth_of_ded + "_" + year_of_ded + '.TXT'
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = open(tgz_tmp_filename, "w")

        try:
            slip_obj = self.env['hr.payslip']
            payslip_ids = slip_obj.search([('date_from', '>=', start_date),
                                           ('date_from', '<=', end_date),
                                           ('employee_id', 'in', employ_ids)
                                           ], order='employee_id')

            empl_e_num = '0000000000'
            if self.env.user:
                curr_user = self.env.user
                if curr_user.company_id and curr_user.company_id.id:
                    if curr_user.company_id.e_number1:
                        empl_e_num = str(curr_user.company_id.e_number1)
                        if curr_user.company_id.e_number2:
                            empl_e_num += str(curr_user.company_id.e_number2)
                        else:
                            empl_e_num += '00'
                file_name_mtd = empl_e_num + str(file_name_mtd)
            total_mtd_amt = total_cp38_amt = 0
            total_cp38_rec = []
            total_mtd_rec = []
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'PCBCURRMONTH':
                        total_mtd_amt += line.total
                        total_mtd_rec.append(payslip.employee_id.id)
                    if line.code == 'PCBCP38':
                        total_cp38_amt += line.total
                        total_cp38_rec.append(payslip.employee_id.id)

            if len(total_mtd_rec) != 0:
                total_mtd_rec = len(list(set(total_mtd_rec)))
            else:
                total_mtd_rec = 0

            if len(total_cp38_rec) != 0:
                total_cp38_rec = len(list(set(total_cp38_rec)))
            else:
                total_cp38_rec = 0

            if total_mtd_amt:
                total_mtd_amt = total_mtd_amt * 100
                if total_mtd_amt < 0:
                    total_mtd_amt = total_mtd_amt * -1
                total_mtd_amt = '%0*d' % (10, int(abs(total_mtd_amt)))

            if total_cp38_amt:
                total_cp38_amt = total_cp38_amt * 100
                if total_cp38_amt < 0:
                    total_cp38_amt = total_cp38_amt * -1
                total_cp38_amt = '%0*d' % (10, int(abs(total_cp38_amt)))

#           Header Record For MTD Text File
            header_record = 'H'.ljust(1) + \
                            ustr(empl_e_num).rjust(10) + \
                            ustr(empl_e_num).rjust(10) + \
                            ustr(year_of_ded).ljust(4) + \
                            ustr(mth_of_ded).ljust(2) + \
                            ustr(total_mtd_amt).rjust(10, '0') + \
                            ustr(total_mtd_rec).rjust(5, '0') + \
                            ustr(total_cp38_amt).rjust(10, '0') + \
                            ustr(total_cp38_rec).rjust(5, '0') + "\r\n"
            tmp_file.write(header_record)

            for employee in self.env['hr.employee'].browse(employ_ids):
                pay_slip_ids = slip_obj.search([('date_from', '>=', start_date),
                                                ('date_from', '<=', end_date),
                                                ('employee_id', '=', employee.id)
                                                ], order='employee_id')

                mtd_amt = cp38_amt = 0.0
                for pay_slip in pay_slip_ids:
                    for lines in pay_slip.line_ids:
                        if lines.code in ['PCBCURRMONTH']:
                            mtd_amt = lines.amount
                        if lines.code in ['PCBCP38']:
                            cp38_amt = lines.amount

                if mtd_amt:
                    mtd_amt = mtd_amt * 100
                    if mtd_amt < 0:
                        mtd_amt = mtd_amt * -1
                    mtd_amt = '%0*d' % (8, int(abs(mtd_amt)))

                if cp38_amt:
                    cp38_amt = cp38_amt * 100
                    if cp38_amt < 0:
                        cp38_amt = cp38_amt * -1
                    cp38_amt = '%0*d' % (8, int(abs(cp38_amt)))

                emp_pcb_no = '00000000000'
                if employee.pcb_number:
                    emp_pcb_no = employee.pcb_number
                    emp_pcb_no = emp_pcb_no.replace(' ', '')
                    emp_pcb_no = emp_pcb_no[3:]
                    emp_pcb_no = emp_pcb_no.replace("-", "")

                emp_new_ic = ''
                if employee.identification_id:
                    emp_new_ic = employee.identification_id
                    emp_new_ic = emp_new_ic.replace(" ", "")
                    emp_new_ic = emp_new_ic.replace('-', '')

                emp_old_ic = ''
                if employee.emp_old_ic:
                    emp_old_ic = employee.emp_old_ic
                    emp_old_ic = emp_old_ic.replace(" ", "")
                    emp_old_ic = emp_old_ic.replace('-', '')

                emp_passport = ''
                if employee.passport_id:
                    emp_passport = employee.passport_id
                    emp_passport = emp_passport.replace(" ", "")

                emp_cntry_code = employee.country_id and \
                    employee.country_id.code or ''

                emp_badge_id = ''
                if employee.badge_id:
                    emp_badge_id = employee.badge_id
                    emp_badge_id = emp_badge_id.replace(" ", "")

                emp_name = ''
                if employee.name:
                    emp_name = employee.name
                    emp_name = emp_name.encode('utf8')

                detail_record = 'D'.ljust(1) + \
                                ustr(emp_pcb_no).rjust(11, '0') + \
                                ustr(emp_name).ljust(60, ' ') + \
                                ustr(emp_old_ic).ljust(12, ' ') + \
                                ustr(emp_new_ic).ljust(12, ' ') + \
                                ustr(emp_passport).ljust(12, ' ') + \
                                ustr(emp_cntry_code).ljust(2, ' ') + \
                                ustr(mtd_amt or 0).rjust(8, '0') + \
                                ustr(cp38_amt or 0).rjust(8, '0') + \
                                ustr(emp_badge_id).ljust(10, ' ') + \
                                "\r\n"
                tmp_file.write(detail_record)
        finally:
            if tmp_file:
                tmp_file.close()
        file_cont = open(tgz_tmp_filename, "rb")
        out = file_cont.read()
        file_cont.close()
        res = base64.b64encode(out)
        # Create record for Binary data.
        mtd_text_rec = self.env['mtd.text.binary.wizard'].create({
            'name': file_name_mtd,
            'rst_file': res,
        })
        return {
            'name': _('Employee PCB Text File'),
            'res_id': mtd_text_rec.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'mtd.text.binary.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
