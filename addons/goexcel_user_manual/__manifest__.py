# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Goexcel User Manual',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': "",
    'depends': ['ks_list_view_manager'],
    'qweb': [
        "static/src/xml/custom_button.xml",
    ],

    'data': [
        'views/jstemplate.xml',
        'security/ir.model.access.csv',
        'wizard/url_wizard.xml'

    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
