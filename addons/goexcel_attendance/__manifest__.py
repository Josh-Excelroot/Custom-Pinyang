# See LICENSE file for full copyright and licensing details.

{
    "name": "GoExcel Attendance",
    "version": "12.0.1",
    "category": "HR",
    "license": 'OPL-1',
    "summary": "Adds feature in attendance",
    "description": """Enables geolocation, geofencing, and attendance report features for employee attendance""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": [
        'base',
        'hr_attendance_geolocation',
        'hr_attendances_overtime',
        'hr_attendance',
        'hr',
        'hr_contract',
        'l10n_my_payroll'
    ],

    # Data
    "data": [
        'data/attendance_mail_schedule_action.xml',
        'data/attendance_mail_template.xml',
        'security/hr_attendance_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/attendance_report_config.xml',
        'views/hr_attendance.xml',
        'views/hr_attendance_overtime.xml',
        'views/hr_attendance_sheet.xml',
        'views/hr_employee.xml',
        'views/location_data.xml',
        'views/res_company.xml',
        'views/res_config_settings.xml',
        'wizard/attendance_report.xml',
        'wizard/hr_change_attendance.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
