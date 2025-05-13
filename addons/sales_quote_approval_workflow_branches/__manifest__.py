# -*- coding: utf-8 -*-
{
    "name": "Sales Quote Approval Workflow",
    "summary": """Sales Quote Approval Workflow""",
    "description": "Sales Quote Approval Workflow",
    "category": "Sale Management",
    "version": "12.0.0.1.0",
    "depends": ["mail", "fetchmail", "sale_management","sale","sci_goexcel_freight","sci_goexcel_freight_2"],
    "data": [
        "security/ir.model.access.csv",
        "data/validate_sales_quote_email_template.xml",
        "data/approve_sales_quote_email_template.xml",
        "data/reject_sales_quote_email_template.xml",
        "views/res_config_settings_view.xml",
        "views/sale.xml",
        "views/sale_approval_settings.xml",
    ],
    "license": "OPL-1",
    "price": 0,
    "currency": "EUR",
    "auto_install": False,
    "installable": True,
    "images": ["static/description/banner.png"],
}
