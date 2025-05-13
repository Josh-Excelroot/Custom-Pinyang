# See LICENSE file for full copyright and licensing details

import time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WizHrEmployeeReport(models.TransientModel):
    _name = 'wiz.pcb2.report'
    _description = "PCB2 Wizard"

    employee_ids = fields.Many2many('hr.employee', 'rel_employee',
                                    'an_employee', 'employee_id', 'Employee')
    start_date = fields.Date("Start Date", default=time.strftime('%Y-01-01'))
    end_date = fields.Date("End Date", default=time.strftime('%Y-12-31'))

    @api.multi
    def print_report(self):
        if self.start_date.year != self.end_date.year:
            raise ValidationError(
                _("Start date and End date must be from same year"))
        if self.start_date > self.end_date:
            raise ValidationError(
                _("Start Date should be Greater than End Date"))
        datas = {
            'ids': [],
            'model': 'hr.payslip',
            'form': self.read([])[0]
        }
        return self.env.ref('my_mtd_report.mtd_pcb2_report_view').\
            report_action(self, data=datas)
