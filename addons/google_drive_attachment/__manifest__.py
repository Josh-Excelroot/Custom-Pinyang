# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "Attachments Upload on Google Drive",
    'summary': """
        Upload attachments on google drive.
        """,
    'description': """
        Upload your attachment file on google drive and get download link
    """,
    'author': "Laxicon Solution",
    'website': "https://www.laxicon.in",
    'category': 'Generic Modules',
    'version': '1.6',
    "price": 49,
    "currency": 'EUR',
    'license': 'OPL-1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'google_drive', 'document'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameter.xml',
        'views/multi_folder_drive_view.xml',
        'views/res_compnay_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    "images": ['static/description/banner.png'],
}
