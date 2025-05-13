# See LICENSE file for full copyright and licensing details

import time

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizBorangEReport(models.TransientModel):
    _name = 'wiz.borang.e.report'
    _description = "Borang Report Wizard"

    employee_ids = fields.Many2many(
        'hr.employee', 'rel_e_employee', 'e_employee', 'employee_id', 'Employee')
    from_date = fields.Date("Start Date", default=time.strftime('%Y-01-01'))
    to_date = fields.Date("End Date", default=time.strftime('%Y-12-31'))

    @api.multi
    def print_pdf_report(self):
        if self.from_date.year != self.to_date.year:
            raise ValidationError(
                _("Start date and End date must be from same year"))
        if self.from_date > self.to_date:
            raise ValidationError(
                _("Start Date should be Greater than End Date"))
        data = self.read([])[0]
        data = {
            'ids': [],
            'model': 'hr.employee',
            'form': data
        }
        return self.env.ref('my_mtd_report.report_borang_e'
                            ).report_action(self, data=data)
