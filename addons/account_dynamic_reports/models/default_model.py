from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError
import datetime


class DefaultRecordSave(models.Model):
    _name = 'default.record.save'

    report_name = fields.Char("Display Name")
    user_id = fields.Many2one("res.users","Partner")
    company_id = fields.Many2one("res.company","Company")
    currency_id = fields.Many2one("res,currency","Currency")
    context_data = fields.Text("Context Data")


