# -*- coding: utf-8 -*-
{
    "name": "goexcel_einvoicing_my",
    "version": "12.0.2",
    "category": "Integeration",
    "license": "LGPL-3",
    "summary": """Custom E-invoice""",
    "description": "Custom Module for E-invoice",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": [
        "base",
        "account",
        "product",
        "base_ubl",
        "sh_message",
    ],
    "sequence": 20,
    "application": True,
    # kashif 7june23 : added data.xml file for decimal precision
    "data": [
        "data/data.xml",
        "data/frequencyofbilling_data.xml",
        "data/classification_type.xml",
        "data/tax_type.xml",
        "data/payment_method.xml",
        "data/einvoice_uom.xml",
        "data/my_state_data.xml",
        "security/ir.model.access.csv",
        "views/account_invoice_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/res_config_setting_view.xml",
        "views/account_invoice_report_template.xml",
        "views/status_check_cron_job.xml",
        "views/data_catalogue_e_invoice.xml",
        "views/product_view.xml",
        "views/bulk_e_invoice_send.xml",
        "views/msic_code.xml",
        'views/einvoice_ar_report.xml',
    ],
    # 'post_init_hook': 'post_init_hook',
}
