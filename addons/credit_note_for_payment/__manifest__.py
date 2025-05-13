# -*- coding: utf-8 -*-

{
    # Version 3
    'name': 'Credit Note for Payment',
    'category': 'Accounting',
    'summary': 'Validate one invoice against multiple creadit note and one credit note against multiple creadit note of a partner',
    'version': '12.3.0.0.4',
    'description': """
        - Credit Note for Payment
    """,
    'author': "Laxicon Solution/Kinjal",
    'website': "https://www.laxicon.in",
    'depends': ['account', 'onepayment_against_multipleinvoices_mdpmdp89', 'sci_goexcel_payment_receipt'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_view.xml',
        'report/account_payment_receipt_report.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': True,
}
