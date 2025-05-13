# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "GOExcel Multi SIgnature",
    'summary': """
        user multi signature.
        """,
    'description': """
        User multi signature
    """,
    'author': "Laxicon Solution",
    'website': "https://www.laxicon.in",
    'category': 'crm',
    'version': '12.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
