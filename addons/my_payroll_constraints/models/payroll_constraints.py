# See LICENSE file for full copyright and licensing details
from datetime import date

from odoo import models, api, _
from odoo.exceptions import ValidationError, UserError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('employee_id')
    def _check_employee_status(self):
        for rec in self:
            if rec.employee_id.emp_status == 'terminated':
                raise ValidationError(
                    _('You can not create contract for Terminated employee!'))

    @api.constrains('wage')
    def _check_contract_wage(self):
        for rec in self:
            if rec.wage <= 0:
                raise ValidationError(
                    _('Please add valid wage amount for this contract!'))

    @api.constrains('is_prev_employment')
    def _check_contract_prev_employment(self):
        for rec in self:
            if rec.is_prev_employment and not rec.prev_empl_add:
                raise ValidationError(
                    _('Please add Previous Employment Gross for this contract!'))


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.slip_id.state == 'done':
                raise UserError(
                    _('You cannot delete a payslip line which is not draft!'))
            return super(HrPayslipLine, self).unlink()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default['date_from'] = date.today()
        default['date_to'] = date.today()
        return super(HrPayslip, self).copy(default)

    @api.constrains('credit_note')
    def check_refund_payslip(self):
        for rec in self:
            payslip_ids = self.search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_from', '=', rec.date_from),
                ('date_to', '=', rec.date_to),
                ('credit_note', '=', False)])
            if len(payslip_ids) > 1:
                for payslip in payslip_ids:
                    if payslip.credit_note is True:
                        continue
                    else:
                        raise ValidationError(
                            _("You can not create multiple payslip for same month"))
