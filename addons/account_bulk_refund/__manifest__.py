# -*- coding: utf-8 -*-
{
    'name': 'Bulk Debit./Credit note v12',
    'version': '12.0.3',
    'summary': "Bulk creation of Debit/Credit note against invoices",
    'sequence': 15,
    'description': """
                    Bulk creation of Debit/Credit note against invoices
                    """,
    'category': 'Accounting/Accounting',
    "price": 0,
    'author': 'Pycus',
    'maintainer': 'Pycus Technologies',
    'website': '',
    'depends': ['account', 'account_debitnote'],
    'data': [
        'wizard/bulk_refund_wizard_view.xml',
        'views/account_customer_debit_note.xml'
    ],
    'demo': [],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
