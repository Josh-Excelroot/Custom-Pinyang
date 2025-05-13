# -*- coding: utf-8 -*-
{
    "name": "CRM Customization",
    "version": "12.0.2.0.2",
    "category": "CRM",
    "license": "LGPL-3",
    "summary": """CRM Customization""",
    "description": "CRM Customization",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ["contacts","sale_management", 'crm', 'sale_crm'],
    "sequence": 2,
    "application": True,
    "data": [
        # comment for uniship
        "data/scheduler_data.xml",
        "data/pipeline_stage.xml",
        "data/crm_lead_reminder_email_template.xml",
        "views/crm_lead_view.xml",
        "views/crm_oppurtunity_form.xml",
        "security/ir.model.access.csv",
        "views/config_type.xml",
        "wizards/crm_won_reason_wiz.xml",
        "views/crm_won_reason.xml",
        "views/crm_industry.xml",
        "views/crm_stage_form.xml",
        "demo/won_reason_data.xml",

           ],
}
