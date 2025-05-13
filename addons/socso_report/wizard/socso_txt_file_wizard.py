# See LICENSE file for full copyright and licensing details
import time
import base64
import tempfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class BinaryTextWizard(models.TransientModel):
    _name = 'binary.text.wizard'
    _description = "Binary Text Wizard"

    name = fields.Char('Name', size=32, default="BRG8A.TXT")
    rst_file = fields.Binary('Click On Download Link To Download File',
                             readonly=True)


class SocsoTxtFileWizard(models.TransientModel):

    _name = 'socso.txt.file.wizard'
    _description = "SOCSO Text File Wizard"

    employee_ids = fields.Many2many(
        'hr.employee', 'ppm_hr_employe_rel10', 'empt_id', 'employee_id',
        'Employee', required=False)
    date_start = fields.Date(
        'Date Start', default=lambda self: time.strftime('%Y-%m-01'))
    date_stop = fields.Date(
        'Date End', default=lambda self: str(datetime.now() + \
                                             relativedelta(months=+1, day=1, days=-1))[:10])

    @api.constrains('date_start', 'date_stop')
    def check_date(self):
        if self.date_start > self.date_stop:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def download_socso_txt_file(self):
        context = self.env.context
        data = self.read()[0]
        if not data['date_start'] or not data['date_stop'] or not data['employee_ids']:
            return False
        monthyear = data['date_stop'].strftime('%m%y')
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = False
        try:
            payslip_ids = self.env['hr.payslip'].search([
                ('date_from', '>=', data['date_start']),
                ('state', 'in', ['draft', 'done', 'verify']),
                ('date_from', '<=', data['date_stop']),
                ('employee_id', 'in', data['employee_ids'])])
            tmp_file = open(tgz_tmp_filename, "w")
            if not payslip_ids:
                tmp_file.write(' ')
            for payslip in payslip_ids:
                totalscsey = 0.0
                for line in payslip.line_ids:
                    if line.code in ['SCSY', 'SCSE']:
                        totalscsey += line.total
                totalscsey = totalscsey * 100
                totalscsey = int(round(totalscsey))
                if totalscsey < 0:
                    totalscsey = totalscsey * -1
                out = 'A3609732P'.ljust(9) + \
                        ustr(payslip.employee_id.identification_id and \
                             ustr(payslip.employee_id.identification_id)[:12].\
                             upper().ljust(12) or ' '.ljust(12)) + \
                        ustr(payslip.employee_id.no_perkeso and \
                             ustr(payslip.employee_id.no_perkeso)[:9].\
                             upper().ljust(9) or ' '.ljust(9)) + \
                        monthyear.ljust(4) + \
                        ustr((payslip.employee_id.name and \
                              payslip.employee_id.name)[:45].upper().ljust(45) \
                             or ' '.ljust(45)) + \
                        ustr(totalscsey or '').ljust(4) + "\r\n"
                tmp_file.write(out)
        finally:
            if tmp_file:
                tmp_file.close()
        file_cont = open(tgz_tmp_filename, "rb")
        out = file_cont.read()
        file_cont.close()
        res = base64.b64encode(out)
        # Create record for Binary data.
        rst_bank_rec = self.env['binary.text.wizard'].create({
            'name': 'BRG8A.TXT',
            'rst_file': res})
        return {
          'name': _('Binary'),
          'res_id': rst_bank_rec.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'binary.text.wizard',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
        }
