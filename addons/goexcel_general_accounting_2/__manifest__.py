# -*- coding: utf-8 -*-
{
    'name': "GoExcel General Accounting 2",
    'summary': """
        General Accounting Function.
        """,
    'description': """
        General Improvement to the Accounting
    """,
    'author': "Excelroot",
    'website': "https://www.excelroot.com",
    'category': 'Accounting',
    'version': '12.0.1.7',
    # kashif 27oct23: added dependency web_drop_target
    'depends': ['base', 'web','account', 'account_cancel', 'web_drop_target', 'credit_note_for_payment',
                'onepayment_against_multipleinvoices_mdpmdp89', 'account_banking_reconciliation', 'attachment_preview',
                'mail',"product","stock", "invoice_bill_approval_workflow"],
    # always loaded
    'data': [
        'data/server_action.xml',
        'security/ir_rule.xml',
        'views/assest.xml',
        'views/account_invoice_view.xml',
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        'views/assets.xml',
        'views/bank_recon_view.xml',
        'views/payment_view.xml',
        'views/account_type_view.xml',
        'views/base_menu_custom_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_partner_bank.view.xml',
          "views/product_template_inherit.xml",
          "views/invoice_cn_view.xml",
        # 'reports/report_invoice.xml',
    ],
"qweb": [
        'static/src/xml/attach.xml',


    ],
    'installable': True,
    'auto_install': False,
}
