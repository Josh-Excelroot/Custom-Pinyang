'''
Created on Jan 30, 2020

@author: Openinside
'''

from odoo import models, fields


class AssetCategory(models.Model):
    _inherit = "account.asset.category"

    type = fields.Selection([('sale', 'Sale: Revenue Recognition'),
                             ('purchase', 'Purchase: Asset'), ('expense', 'Expense Asset')])
