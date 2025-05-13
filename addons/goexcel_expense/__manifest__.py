# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "GOExcel Expense",
    'summary': """
        Expense.
        """,
    'description': """
        Expense
    """,
    'author': "Laxicon Solution",
    'website': "https://www.laxicon.in",
    'category': 'Expense',
    'version': '12.3.0.2',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense', 'mail', 'sale_expense'],
    # always loaded
    'data': [
        'wizard/upload_document_wizard_view.xml',
        'security/ir.model.access.csv',
        'security/monitor_security.xml',
        'views/hr_expense_view.xml',
        'views/message_monitor_expense.xml',
        'views/ocr_table_mapping_view_expense.xml',
        'views/res_config_settings_view_expense.xml',
        'data/mail_template.xml',
        'data/template_table_mapping_data_expense.xml',
    ],
    'installable': True,
    'auto_install': False,
}
