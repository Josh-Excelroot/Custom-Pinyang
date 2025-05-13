# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia Leave Summary Report",
    "version": '12.0.1.0.0',
    "author": "Laxicon Solution",
    "website": "http://www.laxicon.com",
    "sequence": 1,
    "category": "HR",
    "license": "LGPL-3",
    "summary": """Manage Leave Summary Report.""",
    "description": """
        This module provide leave summary reports and provide wizard to
        dowanload.
    """,
    "depends": [
        "my_holiday",
    ],
    "data": [
        "wizard/hr_leave_summary.xml",
    ],
    "installable": True,
    "images": ['static/description/banner.png'],
    "application": True,
    "price": 149,
    "currency": "EUR",
}
