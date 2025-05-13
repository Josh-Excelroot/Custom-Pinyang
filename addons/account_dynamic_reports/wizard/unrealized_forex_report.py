import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from collections import defaultdict
import json

FETCH_RANGE = 2000


def to_dict(json_str):
    return json.loads(json_str)


def to_json(dict_obj):
    return json.dumps(dict_obj, default=str)


class UnrealizedForexReport(models.TransientModel):
    _name = "unrealized.forex.report"
    _inherit = ['dynamic.reports.mixin']
    _description = "Unrealized Forex Report"

    def _default_date_to(self):
        today = fields.Date.context_today(self)
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=last_day)

    # company_id
    date_to = fields.Date(string='End date', required=True, default=_default_date_to)
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')],
                                   string='Target Moves', required=True, default='posted')
    forex_rate_ids = fields.One2many('forex.rate', 'report_id', domain=[('select', '=', True)])
    result_json = fields.Text(default='[]')
    show_move_lines = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(UnrealizedForexReport, self).default_get(fields)
        if res.get('date_to') and 'forex_rate_ids' in fields:
            res['forex_rate_ids'] = self._get_forex_rates(res['date_to'])
            res['date_from'] = '1971-01-01'
        return res

    def _update_forex_rates(self, date=None):
        self.forex_rate_ids = [(5, 0, 0)] + self._get_forex_rates(date or self.date_to)

    def _get_forex_rates(self, date):
        company = self.company_id or self.env.user.company_id
        active_currencies = self.env['res.currency'].search([('id', '!=', company.currency_id.id)])
        return [(0, 0, {
            'currency_id': currency_id,
            'rate': rate,
            'select': bool(rate)
        }) for currency_id, rate in active_currencies._get_rates(company, date).items()]

    def _get_currency_displays(self):
        company_currency_name = self.company_id.currency_id.name
        return {r.currency_id.id: f'{r.currency_id.name} (= {r.rate} {company_currency_name})'
                for r in self.forex_rate_ids.filtered('select')}

    @api.onchange('date_to')
    def _onchange_date_to(self):
        self._update_forex_rates()

    def get_filters(self, default_filters={}):
        return dict(**{
            'target_move': self.target_move,
            'currency_ids': self.forex_rate_ids.filtered('select').mapped('currency_id'),
            'date_to': self.date_to,
            'company_id': self.company_id,
        }, **default_filters)

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}

        currencies = data.get('currency_ids', [])
        if currencies:
            filters['currencies'] = ','.join(currencies.mapped('name'))

        if data.get('target_move') == 'all_entries':
            filters['target_move'] = 'All Entries'
        else:
            filters['target_move'] = 'Posted Only'

        filters['date_to'] = data.get('date_to')

        if data.get('company_id'):
            filters['company'] = data.get('company_id').name
        else:
            filters['company'] = ''

        filters['display_lines'] = self.show_move_lines

        return filters

    def get_forex_rate_values(self):
        return ','.join([f'({fr.currency_id.id}, {fr.rate})' for fr in self.forex_rate_ids if fr.select])

    def _get_sql(self):
        move_where_clause = (self.target_move == 'posted' and " AND move.state = 'posted' ") or ''
        date_where_clause = f" AND aml.date <= '{self.date_to.strftime('%Y-%m-%d')}' "
        forex_rates = self.get_forex_rate_values()
        account_types = ('receivable', 'payable', 'liquidity')
        return f"""SELECT aml.id,
       aml.move_id,
       aml.name,
       aml.account_id,
       aml.journal_id,
       aml.company_id,
       aml.currency_id,
       aml.company_currency_id,
       aml.analytic_account_id,
--        aml.display_type,
       aml.date,
       aml.debit,
       aml.credit,
       aml.balance,
       aml.amount_residual,
       aml.amount_residual_currency,
       aml.amount_residual_currency                                                    AS report_amount_currency,
       aml.amount_residual                                                             AS report_balance,
       aml.amount_residual_currency * custom_currency_table.rate                       AS report_amount_currency_current,
       aml.amount_residual_currency * custom_currency_table.rate - aml.amount_residual AS report_adjustment,
       aml.currency_id                                                                 AS report_currency_id,
       account.code                                                                    AS account_code,
       account.id                                                                      AS account_id,
       account.name                                                                    AS account_name,
       currency.name                                                                   AS currency_code,
       move.ref                                                                        AS move_ref,
       move.name                                                                       AS move_name
FROM account_move_line aml
         JOIN account_move move ON move.id = aml.move_id
         JOIN account_account account ON aml.account_id = account.id
         JOIN res_currency currency ON currency.id = aml.currency_id
         JOIN (VALUES {forex_rates}) AS custom_currency_table(currency_id, rate)
              ON custom_currency_table.currency_id = currency.id
WHERE (1 = 1)
AND
    (account.currency_id != aml.company_currency_id OR
       (account.internal_type IN {account_types} AND (aml.currency_id != aml.company_currency_id)))
  AND (aml.amount_residual != 0 OR aml.amount_residual_currency != 0)
  {move_where_clause + date_where_clause}

UNION ALL

-- Add the lines without currency, i.e. payment in company currency for invoice in foreign currency
SELECT aml.id,
       aml.move_id,
       aml.name,
       aml.account_id,
       aml.journal_id,
       aml.company_id,
       aml.currency_id,
       aml.company_currency_id,
       aml.analytic_account_id,
--        aml.display_type,
       aml.date,
       aml.debit,
       aml.credit,
       aml.balance,
       aml.amount_residual,
       aml.amount_residual_currency,
       CASE
           WHEN aml.id = part.credit_move_id THEN -apr_deb.currency_id
           ELSE -apr_cred.currency_id
           END                                            AS report_amount_currency,
       -part.amount                                       AS report_balance,
       CASE
           WHEN aml.id = part.credit_move_id THEN -apr_deb.amount_currency
           ELSE -apr_cred.amount_currency
           END * custom_currency_table.rate               AS report_amount_currency_current,
       CASE
           WHEN aml.id = part.credit_move_id THEN -apr_deb.amount_currency
           ELSE -apr_cred.amount_currency
           END * custom_currency_table.rate - aml.balance AS report_adjustment,
       CASE
           WHEN aml.id = part.credit_move_id THEN apr_deb.currency_id
           ELSE apr_cred.currency_id
           END                                            AS report_currency_id,
       account.code                                       AS account_code,
       account.id                                         AS account_id,
       account.name                                       AS account_name,
       currency.name                                      AS currency_code,
       move.ref                                           AS move_ref,
       move.name                                          AS move_name
FROM account_move_line aml
         JOIN account_move move ON move.id = aml.move_id
         JOIN account_account account ON aml.account_id = account.id
         JOIN account_partial_reconcile part ON aml.id = part.credit_move_id OR aml.id = part.debit_move_id
         JOIN account_move_line apr_deb ON apr_deb.id = part.debit_move_id
         JOIN account_move_line apr_cred ON apr_cred.id = part.credit_move_id
         JOIN res_currency currency ON currency.id = (CASE
                                                          WHEN aml.id = part.credit_move_id THEN apr_deb.currency_id
                                                          ELSE apr_cred.currency_id END)
         JOIN (VALUES {forex_rates}) AS custom_currency_table(currency_id, rate)
              ON custom_currency_table.currency_id = currency.id
WHERE (account.currency_id = aml.company_currency_id AND
       (account.internal_type IN {account_types} AND aml.currency_id = aml.company_currency_id))
       {move_where_clause + date_where_clause}"""

    @api.constrains('date_to', 'target_move', 'forex_rate_ids')
    def save_data(self, return_data=False):
        self._cr.execute(self._get_sql())
        result = self._cr.dictfetchall()
        result_json = to_json(result)
        result_json = result_json.replace('&', 'and')
        self.result_json = result_json

    def process_data(self):
        data = to_dict(self.result_json)
        currency_data = {c['currency_id']: c
                         for c in self.create_query_and_fetch('res_currency',
                                                              'id as currency_id,name as currency_name,symbol as currency_symbol,rounding as currency_precision,position as currency_position',
                                                              '', fetchall=True, first_column=False, obj_format=True)
                         }
        currency_displays = self._get_currency_displays()
        company_currency_data = self.create_query_and_fetch('res_currency',
                                                              'id as company_currency_id,name as company_currency_name,symbol as company_currency_symbol,rounding as company_currency_precision,position as company_currency_position',
                                                              f'id = {self.company_id.currency_id.id}', fetchall=True, first_column=False, obj_format=True)[0]
        account_data = {a['id']: a
                        for a in self.create_query_and_fetch('account_account', 'id,name', '', fetchall=True, first_column=False, obj_format=True)}
        # Initializing default dictionary for aggregation
        result = defaultdict(lambda: {
            "debit": 0,
            "credit": 0,
            "balance": 0,
            "amount_residual": 0,
            "amount_residual_currency": 0,
            "report_amount_currency": 0,
            "report_balance": 0,
            "report_amount_currency_current": 0,
            "report_adjustment": 0,
            "data": None,
            "lines": defaultdict(lambda: {
                "debit": 0,
                "credit": 0,
                "balance": 0,
                "amount_residual": 0,
                "amount_residual_currency": 0,
                "report_amount_currency": 0,
                "report_balance": 0,
                "report_amount_currency_current": 0,
                "report_adjustment": 0,
                "data": None,
                "lines": []
            })
        })

        # Process each record
        for record in data:
            currency_id = record["currency_id"]
            account_id = record["account_id"]
            record.update(currency_data[currency_id])
            record.update(company_currency_data)
            date = record["date"]

            # Update currency level
            currency = result[currency_id]
            currency["debit"] += record["debit"]
            currency["credit"] += record["credit"]
            currency["balance"] += record["balance"]
            currency["amount_residual"] += record["amount_residual"]
            currency["amount_residual_currency"] += record["amount_residual_currency"]
            currency["report_amount_currency"] += record["report_amount_currency"]
            currency["report_balance"] += record["report_balance"]
            currency["report_amount_currency_current"] += record["report_amount_currency_current"]
            currency["report_adjustment"] += record["report_adjustment"]
            if currency["data"] is None or \
                    datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(account["data"], "%Y-%m-%d"):
                currency["data"] = date
            currency.update(currency_data[currency_id])
            currency.update(company_currency_data)
            currency['currency_display'] = currency_displays[currency_id]

            # Update account level
            account = currency["lines"][account_id]
            account["debit"] += record["debit"]
            account["credit"] += record["credit"]
            account["balance"] += record["balance"]
            account["amount_residual"] += record["amount_residual"]
            account["amount_residual_currency"] += record["amount_residual_currency"]
            account["report_amount_currency"] += record["report_amount_currency"]
            account["report_balance"] += record["report_balance"]
            account["report_amount_currency_current"] += record["report_amount_currency_current"]
            account["report_adjustment"] += record["report_adjustment"]
            if account["data"] is None or \
                    datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(account["data"], "%Y-%m-%d"):
                account["data"] = date
            account.update(currency_data[currency_id])
            account.update(company_currency_data)
            account['account_name'] = account_data[account_id]['name']

            # Add to account lines
            account["lines"].append(record)

        # Convert defaultdict to dict for JSON serialization
        result = {currency_code: dict(data) for currency_code, data in result.items()}
        for currency_code in result:
            result[currency_code]["lines"] = {
                account_code: dict(data)
                for account_code, data in result[currency_code]["lines"].items()
            }
        return result

    def get_report_datas(self, default_filters={}):
        filters = self.process_filters()
        currency_data = self.process_data()
        return filters, currency_data

    def action_pdf(self):
        filters, lines = self.get_report_datas()
        return self.env.ref('account_dynamic_reports.action_print_unrealized_forex_report').with_context(landscape=True)\
            .report_action(
            self, data={'Data': lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        # NotImplemented
        pass

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Unrealized Forex Report View',
            'tag': 'dynamic.ufrx',
            'context': {'wizard_id': self.id}
        }
        return res


class ForexRate(models.TransientModel):
    _name = "forex.rate"
    _description = "Forex Rates"

    report_id = fields.Many2one('unrealized.forex.report')
    currency_id = fields.Many2one('res.currency')
    rate = fields.Float(digits=(12, 6))
    select = fields.Boolean(default=True)

    @api.onchange('rate')
    def _onchange_rate(self):
        self.select = bool(self.rate)

