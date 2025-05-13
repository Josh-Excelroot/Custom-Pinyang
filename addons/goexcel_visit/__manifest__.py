# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Visit",
    "version": "15.0.0.0",
    "category": "Sales",
    "license": 'OPL-1',
    "summary": """Customer Visit and Planning for the salespersons""",
    "description": """Customer Visit Management""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'base', 'web', 'sales_team', 'sale', 'crm','crm_project'],

    # Data
    "data": [
        'security/visit_security.xml',
        'security/ir.model.access.csv',
        'data/visit_method.xml',
        'data/visit_outcome.xml',
        'data/visit_purpose.xml',
        'data/visit_objective.xml',
        'data/visit_value.xml',
        'views/visit_view.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/crm_lead_view.xml',
        'views/configure_view.xml',
        # 'data/cron_data.xml',
        'wizard/prospect_data.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'goexcel_visit/static/src/js/visit_view.js',
        ],
    },

    # Odoo App Store Specific
    'images': ['static/description/goexcel.jpg'],

    # Technical
    "application": True,
    "installable": True,
    'price': 289,
    'currency': 'EUR',
}
