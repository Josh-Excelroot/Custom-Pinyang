# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "GOExcel Sale",
    'summary': """
        Sale related customisation.
        """,
    'description': """
        Sale related customisation
    """,
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'category': 'sale',
    'version': '12.2',
    'depends': ['sales_team','account', 'sale', 'sale_management', 'sale_crm', 'goexcel_crm', 'many2many_tags_link',
                'goexcel_multi_signature', 'stock_picking_cancel_app','sale_picking_manual','whatsapp_integration'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'data/ir_sequence.xml',
        'data/ir_crone_job.xml',
        'data/mail_template.xml',
        'data/res_partner_inactive_config.xml',
        'reports/report_sale_order.xml',
        'views/res_config_view.xml',
        'wizard/sale_lost_reason_wiz.xml',
        'wizard/partner_credit_approval_wiz.xml',
        'wizard/unblock_partner_wiz.xml',
        'views/sale_lost_reason.xml',
        'views/res_partner_view.xml',
        'views/res_partner_inactive_config_view.xml',
        'views/product_view.xml',
        'views/sale_order_view.xml',
        'views/sale_order_line.xml',
        'views/sales_team_view.xml',
        'views/crm_lead_view.xml',
        'views/technical_plan_view.xml',
        # 'views/account_invoice_line_report.xml',
        # 'views/invoice_line_report_sale_target.xml',
    ],
    'demo': [],
    'sequence': 3,
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'external_dependencies': {'python': ['phonenumbers', 'selenium']},
}
