# See LICENSE file for full copyright and licensing details

{
    "name": "Malaysia Localization Package",
    "version": "12.0.1.0.1",
    "license": "LGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "category": "Localization",
    "sequence": 1,
    "description":
    '''
    This is a master module for Malaysia Localization, which install all
    modules of Malaysia Localization.
    ''',
    "depends": ["l10n_my_payroll_report",
                "my_pf_report",
                "socso_report",
                "my_mtd_report",
                "my_payroll_constraints",
                "hr_expense"],
    "installable": True,
    'images': ['static/description/banner.jpg'],
    "application": True,
    "price": 1,
    "currency": "EUR",
}
