# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia PCB Reports",
    "version": '12.0.1.0.5',
    "license": "LGPL-3",
    "depends": ["l10n_my_payroll"],
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "sequence": 1,
    "category": "Human Resources",
    "summary": """Manage Employees PCB Reports.""",
    "description": """
        This module provide reports for Monthly Tax Deduction and Income Tax.
    """,
    "data": [
            "views/hr_employee_extended_view.xml",
            "wizard/my_pcb2_report.xml",
            "report/my_pcb_report_view.xml",
            "wizard/my_incometax_report.xml",
            "report/my_income_tax_report_view.xml",
            "wizard/my_borang_E_report.xml",
            "report/my_borang_e_report_view.xml",
            "wizard/mtd_text_file.xml",
    ],
    "installable": True,
    "images": ['static/description/banner.png'],
    "application": True,
    "price": 149,
    "currency": "EUR",
}
