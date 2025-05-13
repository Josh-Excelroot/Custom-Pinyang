# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Local Charge",
    "version": "12.0.2",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['sci_goexcel_charge_base'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'security/ir.model.access.csv',
        'data/validate_local_charge_email_template.xml',
        'views/local_charge_view.xml',
        'views/invoice_view.xml',
        'views/res_config_settings_view.xml',
        'wizards/local_charge_wizard.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
