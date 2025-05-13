# Copyright (C) 2017 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
from datetime import timedelta, date as datetime_date
from dateutil.relativedelta import relativedelta


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    branch = fields.Many2one('account.analytic.tag', string='Branch')


