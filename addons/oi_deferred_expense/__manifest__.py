# -*- coding: utf-8 -*-
# Copyright 2018 Openinside co. W.L.L.
{
    "name": "Deferred Expense",
    "summary": "Deferred Expense,Deferred, Recognition, Deferred Expense, Expense Recognition",
    "version": "12.0.2.2.0",
    'category': 'Accounting',
    "website": "https://www.open-inside.com",
    "description": """
        Adding deferred expense to the accounting.
        Adding new type in asset category.
        Adding generating entries wizard.
    """,
    'images': [
            'static/description/cover.png'
    ],
    "author": "Openinside",
    "license": "OPL-1",
    "price": 29.99,
    "currency": 'EUR',
    "installable": True,
    "depends": [
        'account', 'account_asset'
    ],
    "data": [
        'view/account_asset_asset.xml',
        'view/account_asset_category.xml',
        'view/account_invoice.xml',
        'view/product_template.xml',
        'view/action.xml',
        'view/menu.xml',
    ],
    'odoo-apps': True

}
