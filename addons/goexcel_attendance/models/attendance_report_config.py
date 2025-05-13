# 1. Standard library imports
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class AttendanceReportConfig(models.Model):
    _name = 'attendance.report.config'

    is_multiple_dates = fields.Boolean(string="Multiple Report")
    name = fields.Char(required=True)
    single_date = fields.Integer(string="Generate Date")
    multiple_dates_ids = fields.One2many(comodel_name='attendance.report.config.lines', inverse_name='report_config_id', string="Dates")
    config_active = fields.Boolean(string="Configuration Active?")

    @api.constrains('single_date')
    def _check_single_date(self):
        for rec in self:
            if not rec.is_multiple_dates:
                if rec.single_date < 1 or rec.single_date > 28:
                    raise UserError('Please set date between 1-28')

    @api.constrains('multiple_dates_ids')
    def _check_duplicate_dates(self):
        for rec in self:
            if rec.multiple_dates_ids:
                date_list = [multi.date for multi in rec.multiple_dates_ids]
                has_duplicate = len(date_list) != len(set(date_list))
                print('date_list ', date_list)
                if has_duplicate:
                    raise UserError('Cannot have multiple dates!')
                else:
                    date_list.sort()
                    print('sorted_date ', date_list)
                    print('rec.multiple_dates_ids ', rec.multiple_dates_ids)
                    for i, multi in enumerate(rec.multiple_dates_ids):
                        print('multi.date ', multi.date)
                        multi.date = date_list[i]

    def set_active(self):
        self.ensure_one()
        self.env['attendance.report.config'].write({'config_active': False})
        self.config_active = True

class ReportDates(models.Model):
    _name = 'attendance.report.config.lines'
    _rec_name = 'date'

    date = fields.Integer(required=True)
    report_config_id = fields.Many2one(comodel_name='attendance.report.config')

    @api.constrains('date')
    def _check_date(self):
        for rec in self:
            if rec.date < 1 or rec.date > 28:
                raise UserError('Please set date between 1-28')