# -*- coding: utf-8 -*-

{
    # version 3
    'name': 'Multiple Invoice Payment',
    'category': 'Accounting',
    'summary': 'Validate one payment against multiple invoices of a partner.',
    'version': '12.3.0.0.4',
    'description': """""",
    'author': "Kinjal-Laxicon Solution",
    'website': "www.laxicon.in",
    'license': "OPL-1",
    'price': "10",
    'currency': 'EUR',
    'depends': ['account', 'sr_manual_currency_exchange_rate'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_view.xml',
        # Kinjal's Update ---
        'wizard/confirmation_wiz.xml',
        'views/inherited_account_journal.xml',  # added in 1.7
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': True,
}
