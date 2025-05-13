# See LICENSE file for full copyright and licensing details.

{
    "name": "GoExcel Inventory Install",
    "version": "12.0.1.0",
    "category": "",
    "license": 'OPL-1',
    "summary": "base goexcel inventory modules",
    "description": """base goexcel inventory modules""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": [
        'base',
        'stock',
        'mrp',
        'product',
        'stock_account',
        'stock_landed_costs',
        'purchase_stock',
        'delivery',
        'disallow_negative_stock',
        'goexcel_effective_date_editable',
        'goexcel_sale_price_cost_update',
        'inventory_cancel',
        'procurement_jit',
        'product_expiry',
        'sale_stock',
        'stock_account_valuation_report',
        'stock_ageing_report_app',
        'stock_card_report',
        'stock_dropshipping',
        'stock_forecast_report',
        'stock_picking_batch',
        'stock_picking_cancel_app',
        'gts_stock_xlsx_report',
        'stock_inventory_valuation_location',
        'stock_landed_costs',
        'sci_goexcel_purchase_custom',
        'stock_return_with_credit_note',
        'goexcel_inventory_base'
    ],

    # Data
    "data": [
        'views/product_views.xml',
    ],

    # Odoo App Store Specific
    'images': [],

    # Technical
    "installable": True,

}
