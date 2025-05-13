# Copyright 2020 WeDo Technology
# Website: http://wedotech-s.com
# Email: apps@wedotech-s.com 
# Phone:00249900034328 - 00249122005009

{
    'name' : 'Payment Pivot & Graph Report View',
    'version' : '13.0.1.0',
	'license' : 'OPL-1',
	'author': 'WeDo Technology',
	'support' : 'odoo.support@wedotech-s.com',
    'summary': 'Add Pivot and Graph View Report to the Payment in Account Module',
    'description': """
	Payments
    Allow to Generate Pivot and Graphic Report from Account Payment View
	Add these Filters in Payment view:
		Today
		Yesterday
		This Month
		Previous Month
    """,
    'category': 'Accounting',
    'sequence': 1,
    'website' : 'http://wedotech-s.com',
    'depends' : ['account'],
	'images': ['images/main_screenshot.png','images/main_1.png','images/main_2.png'],
    'demo' : [],
    'data' : [
 	'views/account_payment_view.xml',
    ], 
    'test' : [
        
    ],
    'auto_install': False,
    'installable': True,
}
