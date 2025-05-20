# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductsPerPage(models.Model):
    _name = 'product.qty_per_page'
    _description = 'Qty per page'

    name = fields.Integer(name='name', string='Quantity', default=10)
    sequence = fields.Integer(name='sequence', string='Sequence', default=10)

    _sql_constraints = [
    ('const_unique_name','unique(name)', 'The duplicates of Quantity values are not allowed!'),
    ('check_name', 'CHECK(name > 0)', 'The Quantity should be greater than 0.'),
    ]
