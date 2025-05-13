{
    'name': 'Bank Deposits & Withdrawals',
    'version': '12',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Manage all bank deposits and withdrawals in one place',
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/sequence.xml',
        'views/account_bank_deposit.xml'
    ],

    'images': ['static/description/goexcel.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
