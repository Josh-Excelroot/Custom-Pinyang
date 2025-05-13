# See LICENSE file for full copyright and licensing details

import time
import base64
import tempfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class BinaryEpfTextWizard(models.TransientModel):
    _name = 'binary.epf.text.wizard'
    _description = "EPF Wizard"

    name = fields.Char('Name', size=32)
    rst_file = fields.Binary('Click On DownLoad Link To Download File',
                             readonly=True)


class EpfTxtFileWizard(models.TransientModel):
    _name = 'epf.txt.file.wizard'
    _description = "EPF TXT File Wizard"

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_rel11',
                                    'employe_id', 'employee_id',
                                    'Employee', required=True)
    date_start = fields.Date('Date Start',
                             default=lambda self: time.strftime('%Y-%m-01'))
    date_stop = fields.Date(
        'Date End', default=lambda self: str(datetime.now() +\
                                             relativedelta(months=+1, day=1,
                                                           days=-1))[:10])

    @api.constrains('date_start', 'date_stop')
    def check_date(self):
        if self.date_start > self.date_stop:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def download_epf_txt_file(self):
        context = self.env.context
        data = self.read()[0]
        if not data['date_start'] or not data['date_stop'] or not data['employee_ids']:
            return False
        end_date_obj = data['date_stop'] + relativedelta(months=1)
        yearmonthdate = datetime.today().strftime('%Y%m%d')
        monthyear = end_date_obj.strftime('%m%Y')
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = open(tgz_tmp_filename, "w")
        try:
            payslip_ids = self.env['hr.payslip'].search([
                ('date_from', '>=', data['date_start']),
                ('date_from', '<=', data['date_stop']),
                ('employee_id', 'in', data['employee_ids'])
                ], order='employee_name')
            totalcontribution = totalemployercontibution = 0.0
            total_record = epf_no_total = 0
            for payslip in payslip_ids:
                epf_no_total += payslip.employee_id.epf_no
                for line in payslip.line_ids:
                    if line.code in ['EPFY']:
                        totalcontribution += line.total
                    if line.code in ['EPFE']:
                        totalemployercontibution += line.total
            totalcontribution = totalcontribution * 100
            new_totalscse = int(round(totalcontribution))
            if new_totalscse < 0:
                new_totalscse = new_totalscse * -1
            final_totalscse = '%0*d' % (15, new_totalscse)
            totalemployercontibution = totalemployercontibution * 100
            new_totalscsy = int(round(totalemployercontibution))
            if new_totalscsy < 0:
                new_totalscsy = new_totalscsy * -1
            final_totalscsy = '%0*d' % (15, new_totalscsy)
            header_record = '00'.ljust(2) + \
                            'EPF MONTHLY FORM A'.ljust(18) + \
                            ustr(yearmonthdate).ljust(8) + \
                            '00001'.ljust(5) + \
                            ustr(final_totalscse).ljust(15) + \
                            ustr(final_totalscsy).ljust(15) + \
                            ustr(epf_no_total).rjust(21, '0') + \
                            ustr('').ljust(45) + "\r\n"
            tmp_file.write(header_record)
            second_header_record = '01'.ljust(2) + \
                '0000000000006117228'.ljust(19) + \
                ustr(monthyear).ljust(6) + \
                'DSK'.ljust(3) + \
                '00001'.ljust(5) + \
                '0000'.ljust(4) + \
                '0000'.ljust(4) + \
                '0000000'.ljust(4) + \
                ustr('').ljust(79) + "\r\n"
            tmp_file.write(second_header_record)
            for payslip in payslip_ids:
                total_record += 1
                gross = epfe = epfy = 0.0
                for line in payslip.line_ids:
                    if line.code in ['GROSS']:
                        gross = line.amount
                    elif line.code in ['EPFY']:
                        epfy = line.amount
                    elif line.code in ['EPFE']:
                        epfe = line.amount
                gross = gross * 100
                new_gross = int(round(gross))
                if new_gross < 0:
                    new_gross = new_gross * -1
                final_gross = '%0*d' % (15, new_gross)
                epfy = epfy * 100
                new_epfy = int(round(epfy))
                if new_epfy < 0:
                    new_epfy = new_epfy * -1
                final_new_epfy = '%0*d' % (9, new_epfy)
                epfe = epfe * 100
                new_epfe = int(round(epfe))
                if new_epfe < 0:
                    new_epfe = new_epfe * -1
                final_new_epfe = '%0*d' % (9, new_epfe)
                actual_detail_record = '02'.ljust(2) + \
                    ustr(payslip.employee_id.epf_no and
                         str(payslip.employee_id.epf_no).rjust(19, '0')
                         or ' '.ljust(19, '0')) + \
                    ustr(payslip.employee_id.identification_id and
                         ustr(payslip.employee_id.identification_id
                              ).ljust(15) or ' '.ljust(15)) + \
                    ustr(payslip.employee_id.name and
                         payslip.employee_id.name.ljust(40)
                         or ' '.ljust(40)) + \
                    ustr(payslip.employee_id.user_id.login and
                         payslip.employee_id.user_id.login.ljust(20)
                         or ' '.ljust(20)) + \
                    ustr(final_new_epfy).ljust(9) + \
                    ustr(final_new_epfe).ljust(9) + \
                    ustr(final_gross).ljust(15) + "\r\n"
                tmp_file.write(actual_detail_record)
            tot_cont = tot_emp_cnt = total_epfey = 0.0
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code in ['EPFE']:
                        tot_cont += line.total
                    if line.code in ['EPFY']:
                        tot_emp_cnt += line.total
                    if line.code in ['EPFY', 'EPFE']:
                        total_epfey += line.total
            tot_cont = tot_cont * 100
            new_tot_cont = int(round(tot_cont))
            if new_tot_cont < 0:
                new_tot_cont = new_tot_cont * -1
            final_cont = '%0*d' % (15, new_tot_cont)
            tot_emp_cnt = tot_emp_cnt * 100
            new_tot_emp_cnt = int(round(tot_emp_cnt))
            if new_tot_emp_cnt < 0:
                new_tot_emp_cnt = new_tot_emp_cnt * -1
            final_cont_2 = '%0*d' % (15, new_tot_emp_cnt)
            total_epfey = total_epfey * 100
            new_total_epfey = int(round(total_epfey))
            if new_total_epfey < 0:
                new_total_epfey = new_total_epfey * -1
            final_new_total_epfey = '%0*d' % (21, new_total_epfey)
            total_record = '%0*d' % (7, total_record)
            footer_record = '99'.ljust(2) + \
                            ustr(total_record).ljust(7) + \
                            ustr(final_cont_2).ljust(15) + \
                            ustr(final_cont).ljust(15) + \
                            ustr(final_new_total_epfey).ljust(21) + \
                            ustr('').ljust(69)
            tmp_file.write(footer_record)
        finally:
            if tmp_file:
                tmp_file.close()
        file_cont = open(tgz_tmp_filename, "rb")
        out = file_cont.read()
        file_cont.close()
        res = base64.b64encode(out)
        # Create record for Binary data.
        epfrma_bank_rec = self.env['binary.epf.text.wizard'].create({
            'name': 'EPFORMA.TXT',
            'rst_file': res,
            })
        return {
            'name': _('Binary'),
            'res_id': epfrma_bank_rec.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'binary.epf.text.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
