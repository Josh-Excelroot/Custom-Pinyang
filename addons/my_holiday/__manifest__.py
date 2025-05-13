# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia Holiday",
    "version": "12.0.1.1.6",
    "license": "LGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "category": "Human Resources",
    "sequence": 1,
    "summary": """Manage Leaves, Auto allocation on Schedulers.""",
    "description":
    '''
    Module to manage leave request approval.
    Documents can attached with a leave request.
    Calculate remaining leaves and carry forward to the next year.
    Carry forwarded leaves period.
    Public holiday lists and pdf report directly emailed to employees.
    ''',
    "depends": ["hr_payroll","hr_holidays", "board", 'hr_contract', 'calendar'],

    "data": [
        "data/my_state_data.xml",
        #kashif 1 sept23: addd this email template file
        "data/leave_approval_mail_template.xml",
        "security/group.xml",
        "security/ir.model.access.csv",
        "views/hr_year_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_holiday_view.xml",
        "views/public_holiday_view.xml",
        "views/calender_inherit.xml",
        'data/demo_data.xml',
        "report/emp_pub_holiday_report_view.xml",
        "report/emp_info_report_view.xml",
        "report/document_expiry_report_view.xml",
        "wizard/hr_refuse_leave_view.xml",
        "wizard/hr_leave_allocation_batch.xml",
        #        "views/board_hr_holidays_view.xml",
        "views/hr_menu_view.xml",
        "views/leave_entitlement.xml",
        "data/hr_schedular.xml",
        "data/remaining_leave_hr.xml",
    ],
    "installable": True,
    "images": ['static/description/banner.png'],
    "application": True,
    "price": 49,
    "currency": "EUR",
}
