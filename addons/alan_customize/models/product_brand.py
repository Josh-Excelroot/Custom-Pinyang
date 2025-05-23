# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductBrand(models.Model):
    _name = 'product.brand.website'
    _inherit = ['website.multi.mixin']
    _description = 'Product brands'


    name = fields.Char('Brand Name', required=True, translate=True)
    logo = fields.Binary('Logo File')
    sequence = fields.Integer(string="Sequence")
    product_ids = fields.One2many(
        'product.template',
        'product_brand_website_id',
        string='Brand Products',
    )
    products_count = fields.Integer(
        string='Number of products',
        compute='_get_products_count',
    )
    visible_slider=fields.Boolean("Visible in Website",default=True)
    active=fields.Boolean("Active",default=True)

    @api.one
    @api.depends('product_ids')
    def _get_products_count(self):
        self.products_count = len(self.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_website_id = fields.Many2one(
        'product.brand.website',
        string='Brand',
        help='Select a brand for this product'
    )
