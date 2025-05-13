from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class HREmployeeMedicalClaim(models.Model):
    _name = 'hr.employee.medical.claim'
    _description = 'Employee Medical Claim'

    @api.depends('claim_amount')
    def _compute_balance(self):
        self.balance = self.fee_before_claim - self.claim_amount

    date = fields.Date(string='Date')
    fee_before_claim = fields.Float(string='Fee Before Claim', store=True)
    claim_amount = fields.Float(string='Claim Amount')
    balance = fields.Float(string='Balance', default=_compute_balance)
    note = fields.Text(string='Note')
    employee_id = fields.Many2one('hr.employee', string='Employee')

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    medical_claim_ids = fields.One2many('hr.employee.medical.claim', 'employee_id', string='Medical Claims')
    total_medical_fee = fields.Float(string='Total Medical Fee')
    remaining_medical_fee = fields.Float(string='Remaining Medical Fee')

    @api.model
    def update_remaining_medical_fee(self):
        current_date = fields.Date.today()
        if current_date.month == 1 and current_date.day == 1:
            employees = self.search([])
            for employee in employees:
                employee.remaining_medical_fee = employee.total_medical_fee


class HRLeave(models.Model):
    _inherit = 'hr.leave'

    def _compute_claim_date(self):
        return self.request_date_from if self.request_date_from else fields.Date.today()

    date = fields.Date(string='Medical Claim Date', default=_compute_claim_date, readonly=True)
    claim_amount = fields.Float(string='Medical Claim Amount')
    note = fields.Text(string='Medical Claim Note')

    @api.onchange('request_date_from')
    def _update_claim_date(self):
        self.date = self.request_date_from

    @api.model
    def create(self, values):
        leave = super(HRLeave, self).create(values)
        employee = leave.employee_id
        if 'employee_id' in values:
            print(employee,'employee')
            employee.remaining_medical_fee = abs(employee.remaining_medical_fee)
            leave.claim_amount = abs(leave.claim_amount)

            sick_leave_id = leave.env['hr.leave.type'].search([
                    ('name', '=', 'Sick Leaves'),('code', '=', 'SL') ])
            current_year = datetime.now().year
            sick_leave_count = leave.env['hr.leave'].search_count([
                ('holiday_status_id', '=', sick_leave_id.id),
                ('employee_id', '=', leave.employee_id.id),
                ('date_from', '>=', f'{current_year}-01-01'),
                ('date_to', '<=', f'{current_year}-12-31'),
            ])
            if sick_leave_count <= 1:
                employee.remaining_medical_fee = employee.total_medical_fee
            medical_claim_values = {
                'leave_id': leave.id,
                'employee_id': leave.employee_id.id,
                'fee_before_claim': employee.remaining_medical_fee,
                'date': leave.date_from,
                'claim_amount': leave.claim_amount,
                'balance': employee.remaining_medical_fee - leave.claim_amount,
                'note': leave.note,
            }
            self.env['hr.employee.medical.claim'].create(medical_claim_values)
            leave.employee_id.remaining_medical_fee = leave.employee_id.remaining_medical_fee - leave.claim_amount
            if leave.employee_id.remaining_medical_fee <0:
                raise ValidationError(f"You've exceeded your medical claim limit, remaining medical claim balance is {leave.employee_id.remaining_medical_fee + leave.claim_amount}")
        return leave
