# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Base Charge",
    "version": "12.0.2",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['product', 'account', 'sci_goexcel_freight', 'sci_goexcel_sq'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'views/res_config_settings_view.xml',
        'views/sales_quotation_view.xml',
        'views/booking_view.xml',
        'views/invoice_view.xml',
        'wizards/charge_wizard.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "application": True,
    "installable": True,

}
