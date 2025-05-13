# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PayslipIncometaxReportWizard(models.TransientModel):
    _name = 'payslip.incometax.report.wizard'
    _description = "Pay Slip Income Tax Wizard"

    employee_ids= fields.Many2many('hr.employee', 'ppm_hr_employee_rel2','emp_id','employee_id','Employee Name', required=False)
    date_from = fields.Date('Date Start',
                             default = lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date End',
                           default = lambda *a: str(datetime.now() + relativedelta(months = +1, day = 1, days = -1))[:10])

    @api.constrains('date_from','date_to')
    def check_date(self):
        if self.date_from > self.date_to:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def print_incometax_report(self):
        data = self.read()[0]
        data.update({'date_from': data['date_from'], 'date_to': data['date_to'], 'employee_ids':data['employee_ids']})
        datas = {
            'ids': [],
            'form': data,
            'model':'hr.payslip',
        }
        return self.env.ref('l10n_my_payroll_report.hr_incometax_report'\
                            '_detail').report_action(self, data=datas)

