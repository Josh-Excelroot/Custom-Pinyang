# -*- coding: utf-8 -*-
{
    'name': "Account netting Merge",
    'summary': 'Account netting Merge',
    'description': """Account netting Merge.""",
    "author": "Laxicon Solution",
    "license": "OPL-1",
    'website': "www.laxicon.in",
    'category': 'Accounting',
    'version': '12.0.1',
    'images': [
        'static/description/cover.png'
    ],
    'depends': ['account', 'sci_goexcel_payment_receipt', 'one2many_field_search'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/account_netting.xml',
        'views/account_payment.xml',
        'views/account_move_line.xml',
        'views/action.xml',
        'views/menu.xml',
        'reports/report_contra.xml',
        'security/ir.model.access.csv'
    ],
    'odoo-apps': False,
    'auto_install': False,
}
