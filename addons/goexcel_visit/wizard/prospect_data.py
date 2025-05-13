from odoo import api, fields, models


class MasterDataWizard(models.TransientModel):
    _name = 'prospect.creation.wizard'

    name = fields.Char(string='Name', required=1)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one('res.country', string='Country')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    fax = fields.Char(string='Fax')
    email = fields.Char(string='Email')

    # @api.multi
    def action_create(self):
        res_partner = self.env['res.partner']
        partner = res_partner.create({
            'name': self.name,
            'street': self.street or False,
            'street2': self.street2 or False,
            'city': self.city or False,
            'state_id': self.state_id.id or False,
            'zip': self.zip or False,
            'country_id': self.country_id.id or False,
            'phone': self.phone or False,
            'mobile': self.mobile or False,
            'fax': self.fax or False,
            'email': self.email or False,
            'company_type': 'company',
            'customer': False,
            'is_prospect': True,
            'user_id': self.env.uid,
            })

        views = [(self.env.ref('goexcel_visit.view_form_visit').id, 'form')]
        #print(partner)
        ctx = {
            'default_customer_name': partner.id,
        }
        return {
            'name': 'Visit',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'visit',
            'views': views,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
