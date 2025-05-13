# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Payslip_details_report_wizard(models.TransientModel):

    _name = 'payslip.details.report.wizard'
    _description = "Pay slip Details Wizard"

    employee_ids = fields.Many2many(
        'hr.employee', 'ppm_hr_employee_rel', 'emp_id', 'employee_id', 'Employee', required=False)
    date_from = fields.Date('Date Start',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date End',
                          default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        if self.date_from > self.date_to:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def print_payslipdetails_report(self):
        data = self.read()[0]
        start_date = data.get('date_from', False)
        end_date = data.get('date_to', False)
        emp_ids = data.get('employee_ids', False) or []
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', emp_ids),
                                                     ('date_from',
                                                      '>=', start_date),
                                                     ('date_to', '<=', end_date),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
        if not payslip_ids:
            raise ValidationError(
                _('There is no payslip details available for selected date %s and %s') % (start_date, end_date))
        datas = {
            'ids': [],
            'form': data,
            'model': 'hr.payslip',
        }
        return self.env.ref('l10n_my_payroll_report.hr_payslip_details_report')\
            .report_action(self, data=datas)

    @api.multi
    def send_mail_payslip(self):
        data = self.read()[0]
        start_date = data.get('date_from', False)
        end_date = data.get('date_to', False)
        emp_ids = data.get('employee_ids', False) or []
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', emp_ids),
                                                     ('date_from',
                                                      '>=', start_date),
                                                     ('date_to',
                                                      '<=', end_date),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            payslip.send_quick_payslip_mail()
