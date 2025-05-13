from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    additional_tax_ids = fields.One2many('additional.tax','employee_ids',
                             'Additonal')


class AdditionalTax(models.Model):
    _name = 'additional.tax'

    employee_ids = fields.Many2one('hr.employee',string='Employee Id')
    month_selection = fields.Selection([('January', 'January'), ('February', 'February'), ('March', 'March'),
                                             ('April', 'April'), ('May', 'May'), ('June', 'June'), ('July', 'July'),
                                             ('August', 'August'), ('September', 'September'), ('October', 'October'),
                                             ('December', 'November'), ('December', 'December')],
                                              string='Month',default='January',required=True)

    @api.model
    def _get_default_year(self):
        return self.env['month.year'].search([('id','=',1)],limit=1)

    year_selection = fields.Many2one('month.year','Year',default=_get_default_year,required=True)
    additional_tax_amount = fields.Float('Additional Tax Amount',required=True)

    @api.onchange('month_selection')
    def onchange_get_data(self):
        if self.month_selection:
            print(self.month_selection)
            for year in range(2020, 2051):
                record = self.env['month.year'].search([('year_name','=',year)],limit=1)
                if not record:
                    object_record = self.env['month.year'].create({
                        'year_name':str(year)
                    })


class MonthYear(models.Model):
    _name = 'month.year'
    _rec_name = 'year_name'

    year_name = fields.Char('Year Name')
