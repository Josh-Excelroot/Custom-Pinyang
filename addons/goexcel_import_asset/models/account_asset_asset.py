# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.model
    def get_import_templates(self):
        return [
            {
                'label': _('Import Template for Assets'),
                'template': '/goexcel_import_asset/static/xls/account_asset_asset.xls'
            },
            {
                'label': _('Import Template for Deferred Expenses'),
                'template': '/goexcel_import_asset/static/xls/account_asset_deferred_expense.xls'
            },
        ]
