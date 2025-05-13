# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 WebLine Apps 
##############################################################################

{
    'name': 'User Restrict Create Partner and product',
    'version': '12.0.1.0',
    'category': 'sale',
    'description': """
        User Restrict Create Partner and product 
    """,
    'summary': """
        User Restrict Create Partner  and product, 
        now user restrict  product and customer in sales and purchae order line
        
    """,
    'author': 'Webline apps',
    'website': 'weblineapps@gmail.com',
    'depends': ['base', 'sale','purchase'],
    'data': [
        'security/security.xml',
        # "views/custom_partner_warning.xml",
        'views/res_users_view.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_View.xml',
        'views/product_templet_view.xml',
        "views/res_settings.xml",
    ],
    'price': 11.00,
    'images' : ['static/description/banner.png'],
	'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
