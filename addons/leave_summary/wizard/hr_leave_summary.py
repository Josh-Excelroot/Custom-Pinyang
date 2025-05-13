from odoo import models, fields, api


class LeaveSummary(models.TransientModel):

    _name = 'leave.summary.wiz'
    _description = "Leave Summary"

    hr_year_id = fields.Many2one('hr.year', string="HR Year")
    select_year = fields.Selection(
        [('all_hr_year', 'All HR Year'), ('custom', 'Custom')], string="Select Year")
    company_id = fields.Many2one('res.company', string="Company")
    hr_summay_leave_ids = fields.One2many(
        'leave.summary.line', 'leave_summary_id', string="Summary Line")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type")

    @api.multi
    def view_leave(self):
        self._cr.execute("delete from leave_summary_line")
        leave_obj = self.env['hr.leave']
        allocation_obj = self.env['hr.leave.allocation']
        leave_domain = []
        allocation_domain = []
        if self.company_id:
            allocation_domain += [('employee_id.company_id', '=', self.company_id.id)]
            leave_domain += [('employee_id.company_id', '=', self.company_id.id)]
        if self.select_year == 'custom' and self.hr_year_id:
            allocation_domain += [('hr_year_id', '=', self.hr_year_id.id)]
            leave_domain += [('hr_year_id', '=', self.hr_year_id.id)]
        if self.employee_id:
            allocation_domain += [('employee_id', '=', self.employee_id.id)]
            leave_domain += [('employee_id', '=', self.employee_id.id)]
        if self.leave_type_id:
            allocation_domain += [('holiday_status_id', '=', self.leave_type_id.id)]
            leave_domain += [('holiday_status_id', '=', self.leave_type_id.id)]
        if self.department_id:
            allocation_domain += [('employee_id.department_id', '=', self.department_id.id)]
            leave_domain += [('department_id', '=', self.department_id.id)]
        allocations = allocation_obj.search(allocation_domain)
        leaves = leave_obj.search(leave_domain)
        leave_dict = {}
        for allocation in allocations.filtered(lambda x: x.state == 'validate'):
            leave = leaves.filtered(lambda x: x.employee_id == allocation.employee_id and
                                    x.holiday_status_id == allocation.holiday_status_id and
                                    x.hr_year_id == allocation.hr_year_id and
                                    x.state == 'validate'
                                    )
            leave_days = sum([x.number_of_days_display for x in leave])
            virtual_leave = leaves.filtered(lambda x: x.employee_id == allocation.employee_id and
                                            x.holiday_status_id == allocation.holiday_status_id and
                                            x.hr_year_id == allocation.hr_year_id and
                                            x.state in (
                                                'draft', 'confirm', 'validate1')
                                            )
            virtual_leave_days = sum([x.number_of_days_display for x in virtual_leave])
            name = str(allocation.employee_id.id) + '-' + str(allocation.holiday_status_id.id)
            if name not in leave_dict.keys():
                leave_dict.update(
                    {name: {
                        'employee_id': allocation.employee_id.id,
                        'hr_year_id': allocation.hr_year_id.id,
                        'leave_type_id': allocation.holiday_status_id.id,
                        'department_id': allocation.employee_id.department_id.id,
                        'company_id': allocation.employee_id.company_id.id,
                        'leave_allocation_id': allocation.id,
                        'number_of_days_display': allocation.number_of_days_display,
                        'taken_leave': leave_days,
                        'virtual_leave': virtual_leave_days
                    }})

            else:
                leave_dict[name]['number_of_days_display'] += allocation.number_of_days_display
        self.hr_summay_leave_ids = [(0, 0, vals) for vals in list(leave_dict.values())]
        action = self.env.ref('leave_summary.report_action_leave_summary').read()[0]
        return action


class LeaveSummaryLine(models.TransientModel):

    _name = 'leave.summary.line'
    _description = "Leave Summary Line"

    leave_summary_id = fields.Many2one(
        'leave.summary.wiz', string="Leave Summary")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")
    hr_year_id = fields.Many2one('hr.year', string="HR Year")
    company_id = fields.Many2one('res.company', string="Company")
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type")
    number_of_days_display = fields.Float(string="Allocation Days")
    taken_leave = fields.Float(string="Taken Leave")
    remaining_leave = fields.Float(
        string="Remaining Leave", compute="_remaining_leaves")
    virtual_leave = fields.Float(string="Virtual Leave")
    virtual_remaining_leave = fields.Float(
        string="Virtual Remaining Leave", compute="_remaining_leaves")

    def _remaining_leaves(self):
        for rec in self:
            rec.remaining_leave = rec.number_of_days_display - rec.taken_leave
            rec.virtual_remaining_leave = rec.number_of_days_display - \
                rec.taken_leave - rec.virtual_leave
