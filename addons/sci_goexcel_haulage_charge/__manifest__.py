# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Haulage Charge",
    "version": "0.1.1",
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
        'data/validate_haulage_charge_email_template.xml',
        'views/haulage_charge_view.xml',
        'views/invoice_view.xml',
        'views/res_config_settings_view.xml',
        'wizards/haulage_charge_wizard.xml',
        'wizards/faf_percent_wizard.xml',

    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "application": True,
    "installable": True,

}
