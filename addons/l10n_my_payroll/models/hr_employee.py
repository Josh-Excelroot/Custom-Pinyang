# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    @api.depends('emp_child_ids', 'emp_child_ids.dependent_children',
                 'emp_child_ids.child_percent')
    def _get_DSC_C_amount(self):
        camount = 0
        for rec in self:
            for line in rec.emp_child_ids:
                if line.dependent_children == 'under18education':
                    if line.child_percent == '50':
                        camount += 0.5
                    else:
                        camount += 1.0
                elif line.dependent_children in ('over18diploma',
                                                 'over18degree'):
                    if line.child_percent == '50':
                        camount += 2.0
                    else:
                        camount += 4.0
                elif line.dependent_children == 'disabled':
                    if line.child_percent == '50':
                        camount += 1.5
                    else:
                        camount += 3.0
                elif line.dependent_children == 'disablededucation':
                    if line.child_percent == '50':
                        camount += 3.5
                    else:
                        camount += 7.0
                else:
                    camount += 0.0
            rec.c_amount = camount

    is_non_permanent_employee = fields.Boolean('Is Non Permanent Employee',default=False)
    is_freelance = fields.Boolean('Is Freelancer',default=False)
    marital = fields.Selection([
        ('single', 'Single'),
        ('single_ch', 'Single With Children'),
        ('divorced', 'Divorced or Widowed'),
        ('married', 'Married and Spouse is Working'),
        ('married_sp_nwork', 'Married and Spouse is not Working'),
        ('married_sp_dsbl', 'Married and Spouse is Disable'),
    ], string='Marital Status', groups='hr.group_hr_user',
        default='single',)
    disable_status = fields.Selection([('n', 'Not Disabled'),
                                       ('d', 'Disabled')], default="n",
                                      string="Disabled Status")
    dsc_category1 = fields.Integer(
        'Marital/Disable Category', help="It is based on marital/disable status")
    d_amount = fields.Float('(D) Deduction for individual')
    s_amount = fields.Float('(S) Deduction for spouse')
    c_amount = fields.Float(compute='_get_DSC_C_amount',
                            string="(C) Number of qualifying children")
    emp_child_ids = fields.One2many('employee.children', 'employee_id',
                                    'Child Details')
    payslip_generate = fields.Selection(
        [('monthly', 'Monthly'), ('biweekly', 'Biweekly')], default='monthly', string="Payslip Generate Gap")

    @api.onchange('marital', 'disable_status')
    def onchange_marital_DSC(self):
        if not self.marital or not self.disable_status:
            self.dsc_category1 = 0
            self.s_amount = 0
            self.d_amount = 0
        if self.marital:
            if self.marital == 'single':
                self.dsc_category1 = 1
                self.s_amount = 0
                if self.disable_status and self.disable_status == 'd':
                    self.d_amount = 15000
                else:
                    self.d_amount = 9000
            elif self.marital in ('single_ch', 'divorced', 'married'):
                self.dsc_category1 = 3
                self.s_amount = 0
                if self.disable_status and self.disable_status == 'd':
                    self.d_amount = 15000
                else:
                    self.d_amount = 9000
            elif self.marital == 'married_sp_nwork':
                self.dsc_category1 = 2
                self.s_amount = 4000
                if self.disable_status and self.disable_status == 'd':
                    self.d_amount = 15000
                else:
                    self.d_amount = 9000
            elif self.marital == 'married_sp_dsbl':
                self.dsc_category1 = 2
                self.s_amount = 7500
                if self.disable_status and self.disable_status == 'd':
                    self.d_amount = 15000
                else:
                    self.d_amount = 9000
        elif self.disable_status:
            if self.disable_status == 'd':
                self.dsc_category1 = 1
                self.d_amount = 15000
                self.s_amount = 0
            else:
                self.dsc_category1 = 0
                self.d_amount = 0
                self.s_amount = 0

    @api.onchange('user_id')
    def _onchange_user(self):
        super(HrEmployee, self)._onchange_user()
        if self.user_id:
            self.address_home_id = self.user_id.partner_id and self.user_id.partner_id.id or False

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Override Search method for put filter on current working status.
        """
        context = dict(self._context) or {}
        if context.get('batch_start_date') and context.get('batch_end_date'):
            active_contract_employee_list = []
            contract_ids = self.env['hr.contract'].search([
                '|', ('date_end', '>=', context.get('batch_start_date')),
                ('date_end', '=', False),
                ('date_start', '<=', context.get('batch_end_date'))
            ])
            for contract in contract_ids:
                active_contract_employee_list.append(contract.employee_id.id)
            args.append(('id', 'in', active_contract_employee_list))
        return super(HrEmployee, self
                     ).search(args, offset, limit, order, count=count)

    @api.model
    def default_get(self, fields_list):
        res = super(HrEmployee, self).default_get(fields_list)
        country_id = self.env.ref('base.my')
        res.update({'country_id': country_id and country_id.id or False})
        return res


class EmployeeChildren(models.Model):
    _name = 'employee.children'
    _description = "Employee Children"

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Employee ID')
    dependent_children = fields.Selection([
        ('under18education', 'Under 18 or in education'),
        ('over18diploma', 'Over 18 - in education (diploma level)'),
        ('over18degree', 'Over 18 - in education (degree level or higher)'),
        ('disabled', 'Disabled'),
        ('disablededucation', 'Disabled - in Higher education'),
    ], string='Dependent Children', default='under18education',)
    child_percent = fields.Selection([('100', '100%'), ('50', '50%'), ('0', '0%')],
                                     string='Children Percentage',
                                     default='100',
                                     help="children eligible Percentage")
