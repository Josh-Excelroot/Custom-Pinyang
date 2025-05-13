import logging
import os
import csv
import tempfile
from odoo.exceptions import UserError,ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date
import xlrd, mmap, xlwt
import base64
import tempfile
import binascii
import io
# from IPython.display import IFrame
try:
    import xlwt
except ImportError:
    xlwt = None

_logger = logging.getLogger(__name__)


class URL_Wizard(models.TransientModel):
    _name = "wizard.url"

    file_data = fields.Binary('Report')
    name = fields.Char('Name')
    name2 = fields.Char('Name')

    url = fields.Char("URL")
    url2 = fields.Char("URL2")

    view_id = fields.Many2one('ir.ui.view', string='View')
    model_name = fields.Char(string='Model')
    pdf_url = fields.Char(string='URL to the Document Guide')
    active_docs = fields.Boolean(string="Docs")
    html = fields.Html(compute='compute_html')



    def compute_html(self):
        var_html = ''
        if self.url or self.url2:
            url = ""
            if self.url:
                url = self.url
            elif self.url2:
                url = self.url2
            var_html = f"<iframe src={url} frameborder='0' allowfullscreen></iframe>"
            self.html = var_html
        else:
            self.html = var_html

    def save_data(self):
        data = self.env['user.manual'].search([('model_name', '=', self.model_name), ('view_id', '=', self.view_id.id)],
                                              order='create_date ASC', limit=1)
        if data:
            data.write({
                'name': self.name,
                'name2': self.name2,
                'url': self.url,
                'url2': self.url2,
                'view_id': self.view_id.id,
                'model_name': self.model_name,
                'pdf_url': self.pdf_url
            })
        else:
            a=1
            if self.name or self.name2 and self.url or self.url2 and self.model_name:
                a =self.env['user.manual'].create({
                    'name': self.name,
                    'name2':self.name2,
                    'url': self.url,
                    'url2':self.url2,
                    'view_id': self.view_id.id,
                    'model_name': self.model_name,
                    'pdf_url':self.pdf_url
                })
            else:
                raise UserError("Name, URL, View, and Model are required fields.")
        # return {
        #     "type": "ir.actions.do_nothing",
        # }

    def play_videosecond(self, user):
        view = self.env.ref("goexcel_user_manual.url_wizard_html")
        html = ''
        if self.url2:
            html = f"<iframe src={self.url2} width='100%' height='400px' frameborder='0' allowfullscreen></iframe>"
        return {
            'name': 'Video Play',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.url',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_html': html},
            'flags': {'create': False, 'edit': False}
        }


    def play_video(self, user):
        view = self.env.ref("goexcel_user_manual.url_wizard_html")
        html = ''
        if self.url:
            html = f"<iframe src={self.url} width='100%' height='400px' frameborder='0' allowfullscreen></iframe>"
        return {
            'name': 'Video Play',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.url',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_html': html},
            'flags': {'create': False, 'edit': False}
        }
