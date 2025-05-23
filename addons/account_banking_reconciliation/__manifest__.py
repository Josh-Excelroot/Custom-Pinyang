# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
# Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Bank Account Reconciliation",
    "summary": "Check transactions that cleared the bank",
    "version": "0.4.5",
    "license": "AGPL-3",
    "category": "Accounting and Financial Management",
    "author": "NovaPoint Group LLC, "
              "Open Source Integrators, "
              "Odoo Community Association (OCA)",
              "laxicon Solution"
    "website": "https://github.com/OCA/account-reconcile",
    "depends": [
        "account_voucher", 'account', 'account_bank_statement_import',
    ],
    "data": [
        "security/account_banking_reconciliation.xml",
        "security/ir.model.access.csv",
        "views/account_banking_reconciliation.xml",
        "views/account_move_line.xml",
        "views/account_journal_dashboard_view.xml",
        "report/bank_statement_report.xml",
        "report/report_bank_statement_summary.xml",
        "report/report_bank_statement_detail.xml"],
    "installable": True,
    "development_status": "Stable",
    #"maintainers": ["max3903"],
}
