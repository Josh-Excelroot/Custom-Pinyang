# See LICENSE file for full copyright and licensing details.
{
    "name": "GoExcel Warehouse Install",
    "version": "12.0.1.0",
    "category": "",
    "license": 'OPL-1',
    "summary": "base goexcel warehouse modules",
    "description": """base goexcel warehouse modules""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": [
        'base',
        'stock'
        'sale_stock',
        'sci_goexcel_warehouse',
        'sci_goexcel_warehouse_2',
        'sci_goexcel_warehouse_invoice',
        'stock_account',
        'stock_card_report'
        'purchase_stock',
        'warehouse_barcode_app'
    ],

    # Data
    "data": [
    ],

    # Odoo App Store Specific
    'images': [],

    # Technical
    "installable": True,

}
