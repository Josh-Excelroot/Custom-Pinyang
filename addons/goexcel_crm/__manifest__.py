# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "GOExcel CRM",
    'summary': """
        CRM related customisation.
        """,
    'description': """
        CRM related customisation
    """,
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'category': 'crm',
    'version': '12.1.2',
    # any module necessary for this one to work correctly
    'depends': ['sale_crm', 'utm', 'crm', 'contacts', 'product', 'web_widget_color', 'sale',
                'base_geolocalize', 'payment_followup', 'goexcel_bps_security'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'security/security_data.xml',
        'data/sequence.xml',
        # 'data/pipeline_stages.xml',
        'data/ir_crone_job.xml',
        'data/mail_template.xml',
        'wizard/mass_reassign_to_customer_wiz_view.xml',
        'wizard/find_customer_data_wiz.xml',
        'wizard/crm_won_reason_wiz.xml',
        'wizard/crm_lead_lost_wiz.xml',
        'wizard/sh_message_wiz.xml',
        'views/res_partner_view.xml',
        'views/customer_hours_view.xml',
        'views/crm_lead_view.xml',
        'views/customer_analysis_view.xml',
        'views/bps_all_master_view.xml',
        'views/occation_gift_view.xml',
        'views/res_config_contact.xml',
        'views/menu_items_view.xml',
        'views/template.xml',
    ],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install': False,
}
