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


class AccountAssetReport(models.TransientModel):
    _name = "account.asset.report"
    _inherit = ['dynamic.reports.mixin']
    _description = "Account Asset Report"

    # date_from, date_to, company_id
    account_id = fields.Many2one('account.account', required=True,
                                 domain=lambda self: [('user_type_id.id', '=', self.env.ref('account.data_account_type_current_assets').id)])
    category_types = fields.Char()
    result_json = fields.Text(default='[]')

    def get_filters(self, default_filters={}):
        return dict(**{
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id,
            'account_id': self.account_id,
            'category_types': self.category_types
        }, **default_filters)

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}

        filters['date_to'] = data.get('date_to')
        filters['date_from'] = data.get('date_from')

        if data.get('company_id'):
            filters['company'] = data.get('company_id').name
        else:
            filters['company'] = ''

        if data.get('account_id'):
            filters['account'] = data.get('account_id').code + ' ' + data.get('account_id').name
        else:
            filters['account_id'] = ''

        return filters

    def _get_sql(self):
        date_from = self.date_from.strftime('%Y-%m-%d')
        date_to = self.date_from.strftime('%Y-%m-%d')
        account_id = self.account_id.id
        company_id = self.company_id.id
        category_types = self._context.get('category_types') or self.category_types or "('expense')"
        return f"""WITH asset_depreciation_line as (
SELECT
    asset_id,
    ROUND(COALESCE(SUM(CASE WHEN depreciation_date < '{date_from}' THEN amount ELSE 0 END), 0), 2) AS amount_before_date_from,
    ROUND(COALESCE(SUM(CASE WHEN depreciation_date >= '{date_from}' AND depreciation_date <= '{date_to}' THEN amount ELSE 0 END), 0), 2) AS amount_in_range,
    ROUND(COALESCE(SUM(CASE WHEN depreciation_date > '{date_to}' THEN amount ELSE 0 END), 0), 2) AS amount_after_date_to
FROM
    account_asset_depreciation_line
GROUP BY
    asset_id)

SELECT asset.id                                        AS asset_id,
       COALESCE(asset.code, '')                        AS reference,
       invoice.date_invoice                            AS date,
       asset.currency_id                               AS currency_id,
       currency.name                                   AS currency_name,
       asset.name                                      AS description,
       partner.name                                    AS vendor_name,
       value                                           AS paid_amount,
       asset.date                                      AS start_date,
       asset.date_end                                  AS end_date,
       COALESCE(asset.amortization_period_number, 0)   AS amortization_period,
       COALESCE(asset.amortization_per_period, 0)      AS monthly_amortization,
       COALESCE(asset_info.amount_before_date_from, 0) AS balance_b_f,
       CASE
           WHEN asset_info.amount_before_date_from = 0 THEN value
           ELSE 0
           END                                         AS addition,
       CASE
           WHEN asset_info.amount_before_date_from = 0 THEN value
           ELSE COALESCE(asset_info.amount_before_date_from, 0)
           END                                         AS cost_total,
       COALESCE(asset_info.amount_in_range, 0)         AS charged_out_total,
       COALESCE(asset_info.amount_after_date_to, 0)    AS balance_c_f

FROM account_asset_asset asset
LEFT JOIN res_partner partner ON partner.id = asset.partner_id
LEFT JOIN account_asset_category category ON category.id = asset.category_id
LEFT JOIN res_currency currency ON currency.id = asset.currency_id
LEFT JOIN asset_depreciation_line asset_info ON asset_info.asset_id = asset.id
LEFT JOIN account_invoice invoice ON invoice.id = asset.invoice_id
WHERE (category.account_asset_id={account_id} OR category.account_depreciation_id={account_id})
        AND asset.company_id={company_id}
        AND category.type in {category_types}
order by asset.date desc;"""

    @api.constrains('date_from', 'date_to', 'account_id')
    def save_data(self, return_data=False):
        self._cr.execute(self._get_sql())
        result = self._cr.dictfetchall()
        result_json = to_json(result)
        result_json = result_json.replace('&', '%26')
        self.result_json = result_json

    def process_data(self):
        data = to_dict(self.result_json)
        return data

    def get_report_datas(self, default_filters={}):
        filters = self.process_filters()
        currency_data = self.process_data()
        return filters, currency_data

    def action_pdf(self):
        return NotImplemented  # yet
        # filters, lines = self.get_report_datas()
        # return self.env.ref('account_dynamic_reports.action_print_account_asset_report').with_context(landscape=True)\
        #     .report_action(
        #     self, data={'Data': lines,
        #                 'Filters': filters
        #                 })

    def action_xlsx(self):
        # NotImplemented
        pass

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Account Asset Report View',
            'tag': 'dynamic.asset',
            'context': {'wizard_id': self.id}
        }
        return res

