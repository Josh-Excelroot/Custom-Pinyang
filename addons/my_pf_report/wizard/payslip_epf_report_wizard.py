# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
from odoo import models, fields, api


class PayslipEpfReportWizard(models.TransientModel):
    _name = 'payslip.epf.report.wizard'
    _description = "EPF Report Wizard"

    employee_ids = fields.Many2many(
        'hr.employee', 'ppm_hr_employee_rel1', 'emp_id', 'employee_id',
        'Employee Name', required=True)
    date_from = fields.Date('Date Start',
                            default=lambda self: time.strftime('%Y-%m-01'))
    date_to = fields.Date(
        'Date End', default=lambda self: str(datetime.now() + \
                                             relativedelta(months=+1, day=1,
                                                           days=-1))[:10])

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        if self.date_from > self.date_to:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def print_epf_report(self):
        data = self.read()[0]
        data.update({
            'employee_ids': data['employee_ids'],
            'date_from': data['date_from'],
            'date_to': data['date_to']})
        datas = {
            'ids': [],
            'form': data,
            'model': 'hr.payslip',
        }
        return self.env.ref('my_pf_report.hr_payslip_epf_report_detail'
                            ).report_action(self, data=datas)
