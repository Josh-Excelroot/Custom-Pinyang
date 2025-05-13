# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Ocean Freight Rate",
    "version": "0.0.4",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['sci_goexcel_charge_base', 'sci_goexcel_freight'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'security/ir.model.access.csv',
        'data/validate_ocean_freight_rate_email_template.xml',
        'views/ocean_freight_rate_view.xml',
        'views/invoice_view.xml',
        'views/res_config_settings_view.xml',
        'wizards/ocean_freight_rate_wizard.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
