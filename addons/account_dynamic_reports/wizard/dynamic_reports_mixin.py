from odoo import api, fields, models, _

from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from lxml import etree
FETCH_RANGE = 2000


def calculate_performance(before, after):
    if before is None:
        return '-'
    elif before and after:
        return '{:,.2f}'.format(
            (after - before) * 100 / before
        )
    elif before and not after:
        return '-100.00'
    elif not before and after:
        return '100.00'
    else:
        return '0.00'


class AttrDict(dict):
    """ Dictionary subclass that supports dot notation for accessing attributes. """

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError(f"'AttrDict' object has no attribute '{key}'")


class DynamicReportsMixin(models.TransientModel):
    _name = "dynamic.reports.mixin"
    _description = "Mixin for Dynamic Reports"

    def default_get_domain(self, values=None):
        return [
            ('company_id', '=', self._get_default_company().id),
            ('create_uid', '=', self.env.user.id)
        ]

    @api.model
    def default_get(self, fields):
        res = super(DynamicReportsMixin, self).default_get(fields)
        company = self.company_id.browse(res.get('company_id'))
        if company.load_last_dynamic_reports_record:
            last_rec = self.search(self.default_get_domain(res), order='id desc', limit=1).read()
            if '__last_update' not in fields and last_rec:
                f = 'id create_date create_uid write_date write_uid display_name'
                for key, value in last_rec[0].items():
                    if key in f:
                        continue
                    if type(value) == list:
                        res[key] = [(6, 0, value)]
                    elif type(value) == tuple:
                        res[key] = value[0]
                    else:
                        res[key] = value
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DynamicReportsMixin, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='date_from']|//field[@name='date_to']"):
                node.set('context', "{'unselect_date_range': True}")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def get_dates_from_date_range(self, date_range=False):
        if not date_range:
            date_range = self.date_range
        date_from, date_to = False, False
        if date_range:
            date = datetime.today()
            if date_range == 'today':
                date_from = date.strftime("%Y-%m-%d")
                date_to = date.strftime("%Y-%m-%d")
            elif date_range == 'this_week':
                day_today = date - timedelta(days=date.weekday())
                date_from = (
                        day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                date_to = (day_today + timedelta(days=6)
                           ).strftime("%Y-%m-%d")
            elif date_range == 'this_month':
                date_from = datetime(
                    date.year, date.month, 1).strftime("%Y-%m-%d")
                date_to = datetime(
                    date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            elif date_range == 'this_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    date_from = datetime(
                        date.year, 1, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    date_from = datetime(
                        date.year, 4, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    date_from = datetime(
                        date.year, 7, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    date_from = datetime(
                        date.year, 10, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            elif date_range == 'this_financial_year':
                fiscal_id = self.env['account.fiscal.year'].search(
                    [('date_from', '<=', fields.Date.to_string(datetime.now())),
                     ('date_to', '>=', fields.Date.to_string(datetime.now())),
                     ('company_id', '=', self.company_id.id)])
                if not fiscal_id:
                    raise ValidationError(_('Please configure fiscal year!'))
                date_from = fiscal_id.date_from
                date_to = fiscal_id.date_to
            elif date_range == 'yesterday':
                date = (datetime.now() - relativedelta(days=1))
                date_from = date.strftime("%Y-%m-%d")
                date_to = date.strftime("%Y-%m-%d")
            elif date_range == 'last_week':
                date = (datetime.now() - relativedelta(days=7))
                day_today = date - timedelta(days=date.weekday())
                date_from = (
                        day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                date_to = (day_today + timedelta(days=6)
                           ).strftime("%Y-%m-%d")
            elif date_range == 'last_month':
                date = (datetime.now() - relativedelta(months=1))
                date_from = datetime(
                    date.year, date.month, 1).strftime("%Y-%m-%d")
                date_to = datetime(
                    date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            elif date_range == 'last_quarter':
                date = (datetime.now() - relativedelta(months=3))
                if int((date.month - 1) / 3) == 0:  # First quarter
                    date_from = datetime(
                        date.year, 1, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    date_from = datetime(
                        date.year, 4, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    date_from = datetime(
                        date.year, 7, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    date_from = datetime(
                        date.year, 10, 1).strftime("%Y-%m-%d")
                    date_to = datetime(
                        date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            elif date_range == 'last_financial_year':
                date = (datetime.now() - relativedelta(years=1))
                fiscal_id = self.env['account.fiscal.year'].search([
                    ('date_from', '<=', fields.Date.to_string(date)),
                    ('date_to', '>=', fields.Date.to_string(date)),
                    ('company_id', '=', self.company_id.id)
                ])
                if not fiscal_id:
                    raise ValidationError(_('Please configure last fiscal year!'))
                date_from = fiscal_id.date_from
                date_to = fiscal_id.date_to
        if not date_range:
            date_from, date_to = self.date_from, self.date_to
        return date_from, date_to

    @api.onchange('date_range', 'financial_year')
    def onchange_date_range(self):
        self.date_from, self.date_to = self.get_dates_from_date_range()

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if self._context.get('unselect_date_range'):
            self.date_range = False

    @api.constrains('date_from', 'date_to')
    def _validate_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Start date must be less than or equal to end date'))

    @api.model
    def _get_default_date_range(self):
        return self.env.user.company_id.date_range

    @api.model
    def _get_default_financial_year(self):
        return self.env.user.company_id.financial_year

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_default_strict_range(self):
        return self.env.user.company_id.strict_range

    financial_year = fields.Selection(
        [('april_march', '1 April to 31 March'),
         ('july_june', '1 july to 30 June'),
         ('january_december', '1 Jan to 31 Dec')],
        string='Financial Year', default=_get_default_financial_year)

    date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This Financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Date Range', default=_get_default_date_range)

    date_from = fields.Date(string='Start date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End date', required=True, default=fields.Date.context_today)

    company_id = fields.Many2one('res.company', default=_get_default_company)

    def query_fetch(self, query, params=None, fetchall=False, first_column=True, obj_format=False):
        self._cr.execute(query, params)
        if fetchall:
            if obj_format:
                return [AttrDict(d) for d in self._cr.dictfetchall()]
            else:
                res = self._cr.fetchall()
                if res:
                    if first_column:
                        return [r[0] for r in res]
                return res

        else:
            if obj_format:
                res = self._cr.dictfetchone()
                if not res:
                    res = {}
                return AttrDict(res)
            else:
                res = self._cr.fetchone()
                if res:
                    if first_column:
                        return res[0]
                return res

    def create_query_and_fetch(self, table, fields, where_clause=None, limit=None, params=None, fetchall=False, first_column=True, obj_format=False):
        if isinstance(fields, tuple) or isinstance(fields, list):
            fields = ','.join(fields)
        query = f"""SELECT {fields} FROM {table} """
        if where_clause:
            query += f" where {where_clause} "
        if limit:
            query += f" limit {limit} "
        return self.query_fetch(query, params=params, fetchall=fetchall, first_column=first_column, obj_format=obj_format)

    def func(self, func_name, *args, **kwargs):
        return eval(func_name)(*args, **kwargs)