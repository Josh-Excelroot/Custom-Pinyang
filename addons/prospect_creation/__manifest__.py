# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Prospect Creation",
    "version": "12.0.2",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['sale', 'crm', 'goexcel_visit', 'sale_crm'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'security/ir.model.access.csv',
        'views/sales_quotation_view.xml',
        'views/crm_lead_view.xml',
        'views/res_partner.xml',
        'wizards/prospect_data.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
