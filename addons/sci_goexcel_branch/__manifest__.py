# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Branch",
    "version": "12.1.2",
    "category": "",
    "license": "OPL-1",
    "summary": """""",
    "description": """""",
    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    # Dependencies
    "depends": [
        "product",
        "account",
        "sale",
        "sci_goexcel_freight",
        "account_dynamic_reports",
        "sci_goexcel_payment_receipt",
        "account_voucher",
        "onepayment_against_multipleinvoices_mdpmdp89",
        "sci_goexcel_master_booking",
        "sci_goexcel_freight_2",
        "sale_term",
        "oi_account_netting_merge",
    ],
    "css": ["static/src/css/style.css"],
    "sequence": 1,
    # Data
    "data": [
        "data/ir_sequence.xml",
        "data/ir_cron.xml",
        "security/security.xml",
        'security/ir.model.access.csv',
        "views/res_users_view.xml",
        "views/sales_quotation_view.xml",
        "views/account_invoice_view.xml",
        "views/booking_inherit_view.xml",
        "views/res_partner_view.xml",
        "views/sequence_views.xml",
        "views/account_payment_view.xml",
        "views/account_netting_view.xml",
        "views/sale_term_view.xml",
        "reports/report_external_layout_inherit.xml",
        "reports/payment_receipt_report_inherit.xml",
        "reports/official_receipt_report_inherit.xml",
        "reports/account_voucher_report_inherit.xml",
        "reports/purchase_receipt_report_inherit.xml",
        "reports/soa_report_inherit.xml",
    ],
    # Odoo App Store Specific
    "images": ["static/description/icon.png"],
    # Technical
    "installable": True,
}
