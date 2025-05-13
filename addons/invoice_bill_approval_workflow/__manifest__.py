# -*- coding: utf-8 -*-
{
    'name': 'Invoice, Bill, Customer, Vendor Credit Note Approval Workflow',
    'summary': """Invoice, Bill,  Customer, Vendor Credit Note Approval Workflow""",
    'description': 'Invoice, Bill,  Customer, Vendor Credit Note Approval Workflow',

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Accounting',
    'version': '12.0.3.0.2',
    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'data/validate_invoice_bill_email_template.xml',
        'wizard/reject_wizard.xml',
        'views/res_config_settings_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_views.xml',
        'report/vendor_payment_approval_report.xml',
    ],

    'license': "OPL-1",
    "auto_install": False,
    "installable": True,

    'images': ['static/description/banner.png'],
}
