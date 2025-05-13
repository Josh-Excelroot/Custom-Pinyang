# -*- coding: utf-8 -*-
{
    "name": "Goexcel Transport Invoices",
    "version": "12.0.0.0.0",
    "category": "Transport",
    "license": "LGPL-3",
    "summary": """Invoices For Multiple RFTs""",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ["sci_goexcel_freight", "sci_goexcel_invoice", "sci_goexcel_transport"],
    "sequence": 2,
    "application": True,
    "data": [
        "views/account_invoice.xml",
        "views/transport_rft.xml",
    ],
}
