# -*- coding: utf-8 -*-
{
    'name': "GoExcel General Accounting",
    'summary': """
        General Accounting Function.
        """,
    'description': """
        print JE, sequences in JE, restrict view in account in Inv/VB, simplify bank acct journal, JE show all pages
        no create in the journal entry&sales&vendor receipt / move internal reference to below the total receivable
        Contact default list view 
        After create bank account, add bank acct (COA), auto-create partner bank, auto-create journal with default auto-cancel
    """,
    'author': "Excelroot",
    'website': "https://www.excelroot.com",
    'category': 'Accounting',
    'version': '12.3.3.1',
    # any module necessary for this one to work correctly
    'depends': ['base',
                'account', 'account_cancel', 'account_voucher',
                'print_journal_entries',
                'contacts', 'account_fiscal_year', 'credit_note_for_payment'
                ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_partner_bank.xml',
        'views/res_partner_view.xml',
        'views/account_move_view.xml',
        'views/account_voucher_view.xml',
        'views/account_invoice_view.xml',
        'views/account_journal_view.xml',
        'views/account_account_view.xml',
        'views/customer_payment_report.xml',
        'views/vendor_payment_report.xml',
        'reports/report_print_journal_entries.xml',
        'data/cron.xml'
    ],
    'installable': True,
    'auto_install': False,
}
