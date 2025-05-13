# -*- coding: utf-8 -*-
# Theme information
{
    'name': 'Payment Follow-up',
    'version': '1.0.7',
    'category': 'Accounting & Finance',
    'description': """""",
    # Author
    'author': 'laxicon solution',

    'website': 'https://www.laxicon.in',
    'maintainer': 'laxicon Solution',

    # Dependencies
    'depends': ['account', 'mail', 'goexcel_customer_statement'],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/payment_followup_crone.xml',
        'data/mail_template_overdue_soa.xml',
        'views/res_partner.xml',
        'views/payment_followup.xml',
        'views/res_config_view.xml',
        # 'views/automatic_payment_followup.xml',
        'wizard/customer_stmt_wiz.xml',
    ],

    # Odoo Store Specific
    'live_test_url': '',
    'images': [
        'static/description/main_poster.jpeg',
        'static/description/main_screenshot.jpeg',
    ],

    # Technical
    'installable': True,
    'application': True,
    'auto_install': False,
}
