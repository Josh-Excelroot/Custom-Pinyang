# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "GOExcel Invoice General",
    'summary': """
        Invoice enhancement
        """,
    'description': """
        Invoice enhancement
    """,
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'category': 'Accounting',
    'version': '12.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'report_qweb_element_page_visibility'],
    # always loaded
    'data': [
        'reports/report_account_invoice_inherit.xml',
        # 'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
