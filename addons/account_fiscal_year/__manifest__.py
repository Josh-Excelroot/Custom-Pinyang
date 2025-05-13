
{
    "name": "Account Fiscal Year",
    "summary": "Create a menu for Account Fiscal Year",
    "version": "12.0.7",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "",
    "author": "",
    "maintainers": ["laxicon"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "date_range",
    ],
    "data": [
        'security/ir.model.access.csv',
        "security/fiscal_year_security.xml",
        "data/date_range_type.xml",
        "views/account_views.xml",
        'wizard/generate_opening_entries.xml',
        'wizard/account_open_closed_fiscalyear_view.xml',
        'views/account_fiscal_year.xml',
        'views/account_invoice_move.xml',
        'views/account_config.xml',
    ],
}
