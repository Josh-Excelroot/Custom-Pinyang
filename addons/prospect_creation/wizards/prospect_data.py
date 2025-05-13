from odoo import api, fields, models, _


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

    @api.multi
    def action_create(self):
        res_partner = self.env['res.partner']
        data = {
            'name': self.name,
            'street': self.street or False,
            'street2': self.street2 or False,
            'city': self.city or False,
            'state_id': self.state_id.id or False,
            'zip': self.zip or False,
            'country_id': self.country_id.id or False,
            'phone': self.phone or False,
            'mobile': self.mobile or False,
            # 'fax': self.fax or False,
            'email': self.email or False,
            'company_type': 'company',
            'user_id': self.env.user.id,
            'customer': False,
            'is_prospect': True,
        }
        #print ("self.env.context", self.env.context)
        partner = res_partner.create(data)
        #print ("partner", partner, self.env.context)
        views = [(self.env.ref('sale.view_order_form').id, 'form')]
        if self.env.context.get('visit', False):
            ctx = dict()
            ctx.update({
                'default_customer_name': partner.id,
                'default_opportunity_id': self.env.context.get('opportunity_id')
            })
            return {
                'name': _('Create Visit'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'visit',
                'views': [(self.env.ref('goexcel_visit.view_form_visit').id, 'form')],
                'view_id': self.env.ref('goexcel_visit.view_form_visit').id,
                'context': ctx,
            }
        if self.env.context.get('sale_order', False):
            opportunity_id = self.env.context.get('opportunity_id')
            opportunity_data = self.env['crm.lead'].sudo().search([('id','=',opportunity_id)])
            ctx = {
                'default_partner_id': partner.id,
                'default_order_type': 'prospect',
                'default_order_line': self.env.context.get('order_line'),
                'default_opportunity_id': self.env.context.get('opportunity_id'),
                'default_mode': opportunity_data.mode,
                'default_service_type': opportunity_data.shipment_mode,
                'default_commodity1': opportunity_data.commodity1_id.id,
                'default_type': opportunity_data.cargo_type,
                'default_lcl_length': opportunity_data.lcl_length,
                'default_lcl_width': opportunity_data.lcl_width,
                'default_lcl_height': opportunity_data.lcl_height,
                'default_lcl_quantity': opportunity_data.lcl_quantity,
                'default_lcl_Weight': opportunity_data.lcl_weight,
                'default_POL': opportunity_data.port_of_loading.id,
                'default_POD': opportunity_data.port_of_discharge.id,
                'default_incoterm': opportunity_data.incoterm.id,
                'default_place_of_delivery': opportunity_data.place_of_delivery,
                'default_type_of_movement': opportunity_data.type_of_movement,
                'default_container_lines': [(0, 0,
                                             {'container_type': line.size_id.id, 'container_quantity': line.quantity,
                                              'weight': line.weight}) for line in opportunity_data.container_line_ids],
            }
            print("sale order ", ctx)
            return {
                'name': 'Sale Order',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'sale.order',
                'views': views,
                'type': 'ir.actions.act_window',
                'context': ctx,
            }
        else:
            return True
