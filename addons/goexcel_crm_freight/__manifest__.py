# -*- coding: utf-8 -*-
{
    "name": "CRM Customization for Freighting",
    "version": "12.0.1.0.0",
    "category": "CRM",
    "license": "LGPL-3",
    "summary": """CRM Customization for Freighting""",
    "description": "CRM Customization for Freighting",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ["contacts","sale_management", 'crm', 'sale_crm'],
    "sequence": 2,
    "application": True,
    "data": [
        # "data/pipeline_stage.xml",
        "views/crm_oppurtunity_form.xml",
        "security/ir.model.access.csv",
        "views/crm_commodity.xml",
        "views/crm_service.xml",
        "views/crm_stage_form.xml",
    ],
}
