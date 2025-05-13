'''
Created on Jan 30, 2020

@author: Openinside
'''

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_is_zero
from odoo import api, models, fields


def strptime(value, dateformat):  # @UnusedVariable
    return fields.Datetime.to_datetime(value)


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    account_asset_id = fields.Many2one(
        'account.account', related='category_id.account_asset_id', string='Fixed Asset Account')
    account_depreciation_id = fields.Many2one(
        'account.account', related='category_id.account_depreciation_id', string='Depreciation Account')
    account_depreciation_expense_id = fields.Many2one(
        'account.account', related='category_id.account_depreciation_expense_id', string='Expense Account')
    journal_id = fields.Many2one(
        'account.journal', related='category_id.journal_id', readonly=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', related='category_id.account_analytic_id', readonly=True, string='Analytic Account')
