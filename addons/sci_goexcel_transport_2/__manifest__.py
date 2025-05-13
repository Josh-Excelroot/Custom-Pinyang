# -*- coding: utf-8 -*-
{
    "name": "Goexcel Trasnport 2  ",
    "version": "12.0.2.0.2",
    "category": "Transport ",
    "license": "LGPL-3",
    "summary": """Transport Inherit View """,
    "description": "Transport Inherit View 2 ",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ["contacts","sale_management", "sci_goexcel_freight","sci_goexcel_transport"],
    "sequence": 2,
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "views/transport_inherit_view.xml",
        "views/configure_view.xml",
        "views/res_partner_view.xml",
        "data/temperature_type_configuration_data.xml",
        "data/job_type_configuration_data.xml"


    ],
}
