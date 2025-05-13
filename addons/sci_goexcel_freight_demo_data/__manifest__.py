{
    "name": "GoExcel Freight Demo Data",
    "version": "12.0.1.0.0",
    "category": "Transport",
    "license": 'LGPL-3',
    "summary": """Freight Management for Freight Forwarding.""",
    'description': 'Freight Management for Freight Forwarder (Air, Land and Ocean)',
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ['sci_goexcel_freight',"uom",'product','account'],
    'sequence': 1,
    "data": [
        'demo/configure.xml',
        'demo/configure_port.xml',
        'demo/configure_terminal.xml',
        'demo/configure_incoterm.xml',
        'demo/configure_product_categories.xml',
        'demo/configure_uom.xml',
        'demo/configure_container.xml',

    ],
}
