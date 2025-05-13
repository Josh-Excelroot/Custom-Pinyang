# See LICENSE file for full copyright and licensing details.
{
    # Module Info.
    "name": "GoExcel Sales Team and Security",
    "version": "12.0.1",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """Added record rule based on team members""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['sale', 'crm', 'goexcel_visit'],

    'sequence': 1,

    # Data
    "data": [
        'security/sales_team_security.xml',
        'views/res_partner_view.xml',
    ],

    # Technical
    "installable": True,

}
