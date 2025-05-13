# -*- coding: utf-8 -*-
{
    'name': "Account netting",

    'summary': 'Account netting',
    
    'description' : """This module allows to compensate the balance of a receivable account with the balance of a payable account for the same partner or other partner, creating a journal item that reflects this operation.""",

    "author": "Openinside",
    "license": "OPL-1",
    'website': "https://www.open-inside.com",
    "price" : 100,
    "currency": 'EUR',
    'category': 'Accounting',
    'version': '12.0.2.1.1',
    'images':[
        'static/description/cover.png'
        ], 

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_netting.xml',
        'views/account_payment.xml',
        'views/action.xml',
        'views/menu.xml',
        'reports/report_contra.xml',
        'security/ir.model.access.csv'       
    ],    
    'odoo-apps' : False,
    'auto_install': False,
}