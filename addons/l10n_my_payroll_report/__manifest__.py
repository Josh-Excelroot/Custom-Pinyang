# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia Payroll Reports",
    "version": '12.0.1.2.0',
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "sequence": 1,
    "category": "HR",
    "license": "LGPL-3",
    "summary": """Manage Payroll Reports.""",
    "description": """
        This module provide payroll reports and provide wizard to
        upload csv file in payslip.
    """,
    "depends": [
        "l10n_my_payroll",
        "partner_fax",
        "product", 'mail', 'report_xlsx'
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_payroll_extended_view.xml",
        "views/hr_employee_additional_tax.xml",
        "report/hr_bank_summary_report_view.xml",
        "report/hr_cheque_summary_report_view.xml",
        "report/hr_incometax_report_view.xml",
        "report/hr_payroll_summary_report_view1.xml",
        "report/payslip_detail_report_view.xml",
        "report/report_registration.xml",
        "report/bank_bulk_payment_report_xlsx.xml",
        "data/payroll_schedule_data.xml",
        "wizard/epf_eis_mtd.xml",
        "wizard/export_employee_summary_wiz_view.xml",
        "wizard/payslip_summary_wizard_view.xml",
        "wizard/upload_xls_wizard_view.xml",
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'l10n_my_payroll_report/static/src/js/visit_view.js',
    #     ],
    # },
    "installable": True,
    "images": ['static/description/banner.png'],
    "application": True,
    "price": 149,
    "currency": "EUR",
}
