# See LICENSE file for full copyright and licensing details.

{
    "name": "GoExcel Sequence Journal Date",
    "version": "12.0.5",
    "category": "Account",
    "license": 'OPL-1',
    "summary": "Bank journal sequence with date",
    "description": """When we create any payment voucher or payment at that time use payment bank journal with date as sequence""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'account', 'sci_goexcel_payment_receipt'],

    # Data
    "data": [
        'views/account_journal.xml',
        'views/ir_sequence.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
