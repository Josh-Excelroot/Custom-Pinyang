# Copyright (C) 2017 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
from datetime import timedelta, date as datetime_date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import datetime


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    range_reset = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ])

    def _compute_date_from_to(self, date):
        self.ensure_one()
        date_from = date_to = date
        if self.range_reset == 'weekly':
            date_from = date_from - timedelta(days=date_from.weekday())
            date_to = date_from + timedelta(days=6)
        elif self.range_reset == 'monthly':
            date_from = datetime_date(date_from.year, date_from.month, 1)
            date_to = date_from + relativedelta(months=1)
            date_to += relativedelta(days=-1)
        elif self.range_reset == 'yearly':
            date_from = datetime_date(date_from.year, 1, 1)
            date_to = datetime_date(date_from.year, 12, 31)
        return date_from, date_to

    def _create_date_range_seq(self, date):
        self.ensure_one()
        if not self.range_reset:
            return super()._create_date_range_seq(date)
        date_from, date_to = self._compute_date_from_to(date)
        date_range = self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', self.id), ('date_from', '>=', date),
             ('date_from', '<=', date_to)], order='date_from desc', limit=1)
        if date_range:
            date_to = date_range.date_from + timedelta(days=-1)
        date_range = self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', self.id), ('date_to', '>=', date_from),
             ('date_to', '<=', date)], order='date_to desc', limit=1)
        if date_range:
            date_from = date_range.date_to + timedelta(days=1)
        seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'sequence_id': self.id,
        })
        return seq_date_range

    def _next(self):
        """ Returns the next number in the preferred sequence in all the ones given in self."""
        if not self.use_date_range:
            return self._next_do()
        # date mode
        dt = fields.Date.today()
        if self._context.get('custom_date'):
            dt = datetime.datetime.strptime(self._context.get('custom_date'), DEFAULT_SERVER_DATE_FORMAT)
            #print('>>>>>>>>>>> RESET Sequence date dt=', dt)
        if self._context.get('ir_sequence_date'):
            dt = self._context.get('ir_sequence_date')
        seq_date = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
        #print('>>>>>>>>>>> RESET Sequence_date=', dt)
        if not seq_date:
            seq_date = self._create_date_range_seq(dt)
        return seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()
