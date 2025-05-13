# Copyright 2014 Therp BV (<http://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Preview attachments",
    "version": "12.0.1.0.3",
    "author": "Therp BV,"
              "Onestein,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": 'Preview attachments supported by Viewer.js',
    "category": "Knowledge Management",
    "depends": [
        'web',
        'mail',
        'account'
    ],
    "data": [
        "templates/assets.xml",
        "views/res_config_setting.xml",
    ],
    "qweb": [
        'static/src/xml/attachment_preview.xml',
        'static/src/xml/m2o_widgets_pdf_preview.xml',

    ],
    "installable": True,
}
