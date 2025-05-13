##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sci Goexcel Ocr',
    'version': '12.0.1.0.1',
    'category': 'Accounting',
    'summary': """
            Import Customer Invoice or Vendor Invoice
            Based on Image or PDF.""",
    'author': 'EXCELROOT TECHNOLOGY SDN BHD',
    'maintainer': 'EXCELROOT TECHNOLOGY SDN BHD',
    'website': "https://www.excelroot.com",
    'license': 'AGPL-3',
    'depends': [
        'account',
        'sci_goexcel_freight',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'demo/template_table_mapping_data.xml',
        'data/res.lang.csv',
        'wizard/import_invoice_wizard_view.xml',
        'views/res_lang_view.xml',
        'views/ocr_table_mapping_view.xml',
        'views/res_partner_view.xml',
        'views/account_invoice_view.xml',
        'views/message_monitor.xml',
        #'views/res_config_settings_view.xml',
    ],
    'images' : ['doc/ExcelRoot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook',
}
