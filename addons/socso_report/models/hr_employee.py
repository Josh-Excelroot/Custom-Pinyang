# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    no_perkeso = fields.Char('SOCSO NO', size=64)
    socso_category = fields.Selection([
        ('a', 'Not Applicable'),
        ('b', 'Employment Injury Scheme and Invalidity Scheme'),
        ('c', 'Employment Injury Scheme')], default='b')

    @api.onchange('identification_id')
    def onchange_identification_id(self):
        if self.no_perkeso:
            self.no_perkeso = self.no_perkeso.replace("-", "")
        else:
            if self.identification_id:
                self.no_perkeso = self.identification_id.replace("-", "")


class EmployeeSocso(models.Model):

    _name = 'employee.socso'
    _description = "Employee SOCSO"

    name = fields.Char("Name")
    socso_line_ids = fields.One2many('employee.socso.view',
                                     'con_catg_socso_id', "SOCSO Lines")


class EmployeeSocsoView(models.Model):

    _name = 'employee.socso.view'
    _description = "Employee SOCSO View"

    con_catg_socso_id = fields.Many2one('employee.socso', 'Category')
    range_from = fields.Float('Range From(RM)')
    range_to = fields.Float("Range To(RM")
    employer_contribution = fields.Float(
        "1st Category:Employer's Contribution")
    employee_contribution = fields.Float(
        "1st Category:Employee's Contribution")
    employer_only_contribution = fields.Float(
        "2nd Category:Contribution by Employer Only")


class HrContract(models.Model):

    _inherit = 'hr.contract'

    ded_employee_socso_id = fields.Many2one('employee.socso', "Employee SOCSO")

    ded_employee_eis_id = fields.Many2one('employee.eis', "Employee EIS")
    not_applicable = fields.Char("N/A", default="N/A")
    applicable_boolean = fields.Boolean("Applicable ?", default=False)

    @api.onchange("struct_id")
    def onchange_contract_category(self):
        if self.struct_id:
            if 'Part Timer' in self.struct_id.name:
                self.ded_employee_eis_id = None
                self.ded_employee_socso_id = None
                self.mrb_category = None
                self.applicable_boolean = True
            else:
                self.applicable_boolean = False
        else:
            self.applicable_boolean = False

    @api.onchange('employee_id','struct_id')
    def onchange_employee_contract(self):
        all_structure_id = self.env['hr.payroll.structure'].search([]).ids
        if self.employee_id.age >= 60:
            self.struct_id = None
            structure_ids = self.env['hr.payroll.structure'].search([('name', 'ilike', 'Senior')]).ids
            self.struct_id = structure_ids[0]
            return {'domain': {'struct_id': [('id', 'in', structure_ids)]}}
        else:
            return {'domain': {'struct_id': [('id', 'in',all_structure_id)]}}


    @api.model
    def default_get(self, fields_list):
        res = super(HrContract, self).default_get(fields_list)
        struct_id = self.env.ref('l10n_my_payroll.structure_all_in_one')
        socso = self.env.ref('socso_report.socso_categ_1')
        pcb = self.env.ref('l10n_my_payroll.mrb_category2')
        eis = self.env.ref('socso_report.eis_categ_1')
        res.update({'struct_id': struct_id and struct_id.id or False,
                    'ded_employee_socso_id': socso and socso.id or False,
                    'ded_employee_eis_id': eis and eis.id or False,
                    'category_mrb': pcb and pcb.id or False})
        return res


class EmployeeEIS(models.Model):

    _name = 'employee.eis'
    _description = "Employee EIS"

    name = fields.Char("Name")
    eis_line_ids = fields.One2many('employee.eis.view',
                                   'con_catg_eis_id', "EIS Lines")


class EmployeeEISView(models.Model):

    _name = 'employee.eis.view'
    _description = "Employee EIS View"

    con_catg_eis_id = fields.Many2one('employee.eis', 'Category')
    range_from = fields.Float('Range From (RM)')
    range_to = fields.Float("Range To (RM)")
    employer_contribution = fields.Float("Employer's Contribution")
    employee_contribution = fields.Float("Employee's Contribution")
    #employer_only_contribution = fields.Float("2nd Category:Contribution by Employer Only")
