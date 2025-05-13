import logging
import os
import csv
import tempfile
from odoo.exceptions import UserError,ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)


class PayslipWizard(models.TransientModel):
    _name = 'payslip.wizard'

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    employee = fields.Many2many('hr.employee',string="Employee")

    
    @api.model
    def default_get(self, fields):
        res = super(PayslipWizard, self).default_get(fields)
        employees = self.env['hr.employee'].search([])

        res['employee'] = [(6, 0, employees.ids)]
        return res

    def create_payslips(self):
        if self.employee:
            for rec in self.employee:
                contract = self.env['hr.contract'].search([("employee_id", '=', rec.id), ('state', '=', 'open')],
                                                          limit=1)

                self.env['hr.payslip'].create({
                    "employee_id":rec.id,
                    "date_from":self.start_date,
                    "date_to":self.end_date,
                    "name":"Salary Slip of"+" "+rec.name+" for "+str(self.start_date.strftime("%B"))+"-"+str(self.start_date.year)
                })
        else:
            raise UserError("Required Employee!")