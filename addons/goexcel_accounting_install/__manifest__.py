{
    "name": "GoExcel Accounting Install",
    "version": "12.0.1.0",
    "category": "",
    "license": 'OPL-1',
    "summary": "base goexcel accounting modules",
    "description": """base goexcel accounting modules""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": [
        'base',
        'aos_account_invoice_writeoff',
        'account',
        'account_asset',
        'account_cancel',
        'account_fiscal_year',
        'account_financial_report',
        'account_bulk_refund',
        'dynamic_xlsx',
        'accounting_pdf_reports',
        'account_dynamic_reports',
        'account_invoice_fixed_discount',
        'account_banking_reconciliation',
        'accounting_pdf_reports',
        'wedo_account_payment_pivot_graph_view',
        'oi_account_netting_merge',
        'oi_account_netting',
        'sci_goexcel_payment_receipt',
        'goexcel_general_accounting',
        'goexcel_general_accounting_2',
        'goexcel_recurring_transaction',
        'credit_note_for_payment',
        'onepayment_against_multipleinvoices_mdpmdp89',
        'sr_manual_currency_exchange_rate',
        'goexcel_customer_statement',
        'goexcel_sequence_journal_date',
        # Yulia 24012025 add goexcel_import_asset
        "goexcel_import_asset",
        'oi_deferred_expense',
        'print_journal_entries',
        'import_multiple_journal_entry',
        'sale_term',
        'goexcel_bank_deposit',
        'currency_rate_update',
        'invoice_bill_approval_workflow',
        'bulk_bank_payments',
        'account_invoice_currency',
        'sequence_reset_period',
    ],

    # Data
    "data": [
    ],

    # Odoo App Store Specific
    'images': [],

    # Technical
    "installable": True,

}
# See LICENSE file for full copyright and licensing details.
