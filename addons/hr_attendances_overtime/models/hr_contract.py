# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class HrContract(models.Model):
    """Inherit Hr Contract ."""

    _inherit = 'hr.contract'

    attend_police_id = fields.Many2one(
        'hr.attendance.policies', string='Policy')
    is_applicable_ot = fields.Boolean(string='Apply OT')

    @api.multi
    @api.onchange('is_applicable_ot')
    def onchange_is_applicable_ot(self):
        if self.is_applicable_ot:
            wage = self.wage/26
            self.rate_per_hour = wage/8


class HrEmployee(models.Model):
    """Inherit Hr Employee to add Attendance Sheet Many2one."""

    _inherit = 'hr.employee'
    _description = 'Description'

    attendance_sheet_id = fields.Many2one(
        'hr.attendance.sheet', string='Attendance Sheet')


class HrPayslip(models.Model):
    """Inherit Hr Payslip."""

    _inherit = 'hr.payslip'
    _description = 'Pay Slip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """Method is overriden to add worked days line in Payslip."""
        res = super(HrPayslip, self).get_worked_day_lines(
            contracts, date_from, date_to)
        sheet_id = self.env['hr.attendance.sheet'].search(
            [('employee_id', '=', self.employee_id.id),
             ('request_date_from', '=', date_from),
             ('request_date_to', '=', date_to)])

        if sheet_id:
            if sheet_id.no_overtime:
                res.append({
                    'name': 'Overtime',
                    'code': 'OVT',
                    'number_of_days': sheet_id.no_overtime or False,
                    'number_of_hours': sheet_id.total_overtime or False,
                    'contract_id': self.contract_id.id or False
                })
            if sheet_id.no_latein:
                res.append({
                    'name': 'Late in',
                    'code': 'LATE',
                    'number_of_days': sheet_id.no_latein or False,
                    'number_of_hours': sheet_id.total_latein or False,
                    'contract_id': self.contract_id.id or False
                })
            if sheet_id.no_absence:
                res.append({
                    'name': 'Absence',
                    'code': 'ABS',
                    'number_of_days': sheet_id.no_absence or False,
                    'number_of_hours': sheet_id.total_absence or False,
                    'contract_id': self.contract_id.id or False
                })
            if sheet_id.no_difftime:
                res.append({
                    'name': 'DIFFRENCE TIME',
                    'code': 'DIFFT',
                    'number_of_days': sheet_id.no_difftime or False,
                    'number_of_hours': sheet_id.total_difftime or False,
                    'contract_id': self.contract_id.id or False
                })

        return res
