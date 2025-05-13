{
    'name': 'Bulk Bank Payments',
    'version': '12',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Bulk export payments into excel/csv file',
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'depends': [
        'account',
    ],
    'data': [
        'wizard/view_bulk_bank_payment.xml',
        'reports/report_bulk_bank_payments_xlsx.xml',
    ],

    'images': ['static/description/goexcel.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
