# -*- coding: utf-8 -*-
{
    "name": "Sailing Reschedule",
    "version": "12.0.1.3",
    "category": "Logistics",
    "license": 'LGPL-3',
    "summary": """Sailing Reschedule """,
    'description': 'Sailing Reschedule',
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ['base','account','mail','sci_goexcel_freight'],
    'sequence': 2,
    'application': True,
    "data": [
        #'security/ir.model.access.csv',
        #'views/booking_view.xml',
        'data/reschedule_mail_template.xml',
        'wizards/reschedule_sailing_view.xml',
    ],
}
