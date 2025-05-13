# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 WebLine Apps 
##############################################################################

{
    'name': 'Show all company users',
    'version': '12.0.0.0',
    'category': 'general',
    'description': """
        User can see all company users 
    """,
    'summary': """
        User Restrict Create Partner  and product, 
        now user restrict  product and customer in sales and purchae order line
        
    """,
    'author': 'excelroot',
    'website': 'www.excelroot.com',
    'depends': ['base','mail'],
    'data': [
        'security/security.xml',
        'views/res_users_view.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': '_post_init_hook',
'uninstall_hook': 'uninstall_hook',

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
