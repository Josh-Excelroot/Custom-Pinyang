# -*- coding: utf-8 -*-
{
    'name': "Goexcel Employee Medical Claim",
    'summary': """
        HR related customization
        """,
    'description': """
        HR related customization
    """,
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'category': 'hr',
    'version': '12',
    'depends': ['hr', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_medical_fee_reset.xml',
        'views/hr_employee_medical_claim.xml',
    ],

    'images': ['static/description/goexcel.jpg'],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install': False,
}
