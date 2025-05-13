# See LICENSE file for full copyright and licensing details

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LeaveEntitlement(models.Model):

    _name = "leave.entitlement"
    _description = "Leave Entitlement"
    _rec_name = 'leave_type_id'

    job_position = fields.Many2one('hr.job', required=True)
    department = fields.Char(related="job_position.department_id.name",string="Department")
    minimum_annual_leave_entitlement = fields.Float('Minimum Annual Leave Entitlement', digits=(12, 1), default=0.0 ,required=True)
    employee_count = fields.Float(compute='compute_count')
    additional_leave_entitlement_per_year = fields.Float('Additional Leave Entitlement For Each of No of Service Year',
                                                         default=0.0, digits=(12, 1), required=True)
    state = fields.Selection(selection=[('draft','Draft'),('approved','Approved')], default='draft',required=True)
    max_transfer_annual_leave = fields.Float('Max Transferred Leave', digits=(12, 1),default=0.0,requried=True)
    leave_type_id = fields.Many2one('hr.leave.type',string="Leave Type",required=True)

    def compute_count(self):
        for record in self:
            record.employee_count = self.env['hr.employee'].search_count(
                [('leave_entitlement', '=', self.id)])

    def smart_button_employee(self):
        return {
            'name': _('Employee'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.employee',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('leave_entitlement.id', '=', self.id)],
        }

