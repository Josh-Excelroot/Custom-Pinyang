# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Activity",
    "version": "12.0.3.0.1",
    "category": "Sales",
    "license": 'OPL-1',
    "summary": """Schedule Activity""",
    "description": """Schedule Activity""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'web'],

    # Data
    "data": [
        'data/cron_data.xml',
        'data/activity_reminder_email_template.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/goexcel.jpg'],

    # Technical
    "application": True,
    "installable": True,
    'price': 289,
    'currency': 'EUR',
}