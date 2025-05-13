# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia PF Reports",
    "version": '12.0.1.0.1',
    "license": "LGPL-3",
    "depends": [
        "l10n_my_payroll",
    ],
    "website": "http://www.serpentcs.com",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "category": "HR",
    "summary": """Manage Employees PF reports.""",
    "description": """
        This module provide wizard to print pf reports.
    """,
    "data": [
        "views/employee_view.xml",
        "wizard/epf_txt_file_wizard_view.xml",
        "report/hr_payslip_epf_report_view.xml"
    ],
    "installable": True,
    "images": ['static/description/banner.png'],
    "application": True,
    "price": 99,
    "currency": "EUR",
}
