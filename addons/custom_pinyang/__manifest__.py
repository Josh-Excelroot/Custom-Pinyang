# -*- coding: utf-8 -*-
{
    'name': "Custom PinYang",
    'summary': """
        Custom PinYang Module.
        """,
    'description': """
        PinYang Custom Module
    """,
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'category': 'Transport',
    'version': '12.1',
    'depends': ['base', 'sale', 'product', 'sci_goexcel_freight', 'sci_goexcel_sq', 'account', 'sci_goexcel_freight_2',
                'sci_goexcel_invoice',
                "account_bulk_refund", "sale_management", "sale_term", "sci_goexcel_invoice"],
    # always loaded
    'data': [
        'reports/noa_booking_inherit.xml',
        'reports/bl_report_inherit.xml',
        'reports/noa_bl_inherit.xml',
        'reports/invoice_report_inherit.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
