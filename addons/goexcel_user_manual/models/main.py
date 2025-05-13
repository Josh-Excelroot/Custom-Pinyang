from odoo.api import model
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class Freightbookinginherit(models.Model):
    _name = "freight.booking.popup"
    # _name = 'user.manual_popup'

    def open_url_popoup(self, user=None):
        a = 8

        view = self.env.ref("goexcel_user_manual.url_wizard_from")
  

        if not user:
            return {
                'name': 'User Guide',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.url',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
            }
        else:
            model = user.get('model')
            view_id=False
            if user.get('view_id') != "undefined":
                view_id = int(user.get('view_id'))
            name = False
            name2  = False
            url = False
            url2= False
            docs_url = False
            data = self.env['user.manual'].search([('model_name', '=', model),('view_id','=',view_id)],order='create_date ASC',limit=1)
            if data:
                name = data[-1].name
                url = data[-1].url
                url2=data[-1].url2
                name2 = data[-1].name2
                docs_url = data[-1].pdf_url
            if self.env.user._is_admin():
                p = True
            else:
                p = False


            return {
                'name': 'User Guide',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.url',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': {'default_model_name': model,
                            'default_view_id': view_id,
                            'default_name': name,
                            'default_name2': name2,
                            'default_url': url,
                            'default_url2':url2,
                            'default_pdf_url':docs_url,
                            'default_active_docs':p
                            }
            }


class UserManual(models.Model):
    _name = 'user.manual'

    name = fields.Char(string='Name')
    name2 = fields.Char(string='Name')
    url = fields.Char(string='URL')
    url2 = fields.Char(string='URL2')
    model_name = fields.Char(string='model name')
    view_id = fields.Many2one('ir.ui.view', string='View')
    pdf_url = fields.Char(string='URL to the Document Guide')
