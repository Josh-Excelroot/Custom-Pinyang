# See LICENSE file for full copyright and licensing details.
{
    "name": "GoExcel HR Install",
    "version": "12.0.1.0",
    "category": "",
    "license": 'OPL-1',
    "summary": "base goexcel HR modules",
    "description": """base goexcel HR modules""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": [
        'base',
        'goexcel_attendance',
        'goexcel_expense',
        'google_drive_attachment',
        'hr_attendance_geolocation',
        'hr_attendances_overtime',
        'l10n_my_payroll',
        'l10n_my_payroll_report',
        'leave_summary',
        'malaysia_localization_package',
        'my_holiday',
        'my_mtd_report',
        'my_payroll_constraints',
        'my_pf_report',
        'payroll_web',
        'socso_report',

    ],

    # Data
    "data": [
    ],

    # Odoo App Store Specific
    'images': [],

    # Technical
    "installable": True,

}
