from odoo import models
from datetime import date as datetime_date, timedelta, datetime, date
from dateutil.relativedelta import relativedelta


class ResCompany(models.Model):
    _inherit = "res.company"

    def set_schedul_date(self):
        data_ids = self.env['transaction.template'].search([('status', '=', 'confirm')])
        for rec in data_ids:
            if rec.previous_date or rec.previous_date == rec.next_date or not rec.next_date:
                next_date_var = ''
                if rec.interval_t == 'days':
                    next_date_var = rec.previous_date + timedelta(days=1)
                elif rec.interval_t == 'weeks':
                    next_date_var = rec.previous_date + timedelta(days=7)
                elif rec.interval_t == 'months':
                    next_date_var = rec.previous_date + relativedelta(months=1)
                elif rec.interval_t == 'years':
                    next_date_var = rec.previous_date + relativedelta(years=1)
                rec.next_date = next_date_var

            if str(rec.next_date) == datetime.today().strftime("%Y-%m-%d"):
                    rec.action_create_journal_data_btn()
                    rec.previous_date = datetime.today().strftime("%Y-%m-%d")

            next_date_var = ''
            if rec.interval_t == 'days':
                next_date_var = rec.previous_date + timedelta(days=1)
            elif rec.interval_t == 'weeks':
                next_date_var = rec.previous_date + timedelta(days=7)
            elif rec.interval_t == 'months':
                next_date_var = rec.previous_date + relativedelta(months=1)
            elif rec.interval_t == 'years':
                    next_date_var = rec.previous_date + relativedelta(years=1)
            rec.next_date = next_date_var
