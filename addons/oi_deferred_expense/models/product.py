# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    deferred_expense_category_id = fields.Many2one(
        'account.asset.category', string='Deferred Expense Type', company_dependent=True, ondelete="restrict")
