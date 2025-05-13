# -*- coding: utf-8 -*-
{
    'name': "GoExcel CoA Type View",
    'summary': """
        Enable Chart of Account View to delete.
        """,
    'description': """
        
    """,
    'author': "Excelroot",
    'website': "https://www.excelroot.com",
    'category': 'Accounting',
    'version': '12.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                ],
    # always loaded
    'data': [
        'views/account_account_type.xml',
    ],
    'installable': True,
    'auto_install': False,
}
