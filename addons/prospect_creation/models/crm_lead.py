from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    crm_line_ids = fields.One2many('crm.line', 'crm_lead_id', string="Crm Line", copy=False)
    is_prospect = fields.Boolean(string="Is Prospect", compute="get_is_prospect")

    @api.multi
    def sale_action_quotations_new(self):
        if not self.partner_id:
            raise UserError(_("Please create Prospect or Select Customer"))
        order_line = []
        for res in self.crm_line_ids:
            data = {
                'product_id': res.product_id.id,
                'name': res.product_id.display_name,
                'product_uom_qty': res.product_uom_qty,
                'product_uom': res.product_uom.id,
                'price_unit': res.price,
            }
            order_line.append((0, 0, data))
        action = self.env.ref('sale_crm.sale_action_quotations_new').read()[0]
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_opportunity_id': self.id,
            'default_order_line': order_line,
            'default_partner_id': self.partner_id.id or False
        }
        return action

    @api.depends('partner_id', 'partner_id.is_prospect', 'partner_id.customer')
    def get_is_prospect(self):
        for res in self:
            if res.partner_id and res.partner_id.is_prospect:
                res.is_prospect = True
            elif not res.partner_id:
                res.is_prospect = True
            else:
                res.is_prospect = False

    @api.multi
    def action_prospect_creation(self):
        # self.ensure_one()
        if self.partner_id:
        #     raise UserError(_("Customer Already Created so you can't create prospect for this Lead"))
            order_line = []
            data = {}
            for res in self.crm_line_ids:
                data = {
                    'product_id': res.product_id.id,
                    'name': res.product_id.display_name,
                    'product_uom_qty': res.product_uom_qty,
                    'product_uom': res.product_uom.id,
                    'price_unit': res.price,
                }
            order_line.append((0, 0, data))
            ctx = {
                'default_partner_id': self.partner_id.id,
                'default_order_type': 'prospect',
                'default_order_line': self.env.context.get('order_line'),
                'default_opportunity_id': self.id,
                'default_mode': self.mode,
                'default_service_type': self.shipment_mode,
                'default_commodity1': self.commodity1_id.id,
                'default_type': self.cargo_type,
                'default_POL': self.port_of_loading.id,
                'default_POD': self.port_of_discharge.id,
                'default_incoterm': self.incoterm.id,
                'default_place_of_delivery': self.place_of_delivery,
                'default_type_of_movement': self.type_of_movement,
                'default_container_lines': [(0, 0, {'container_type': line.size_id.id,'container_quantity': line.quantity,'weight': line.weight}) for line in self.container_line_ids],
            }
            views = [(self.env.ref('sale.view_order_form').id, 'form')]
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
            order_line = []
            for res in self.crm_line_ids:
                data = {
                    'product_id': res.product_id.id,
                    'name': res.product_id.display_name,
                    'product_uom_qty': res.product_uom_qty,
                    'product_uom': res.product_uom.id,
                    'price_unit': res.price,
                }
                order_line.append((0, 0, data))
            ctx = {
                'default_name': self.partner_name,
                'default_street': self.street,
                'default_street2': self.street2,
                'default_city': self.city,
                'default_state_id': self.state_id.id,
                'default_zip': self.zip,
                'default_country_id': self.country_id.id,
                'default_phone': self.phone,
                'default_mobile': self.mobile,
                'default_order_type': 'prospect',
                'default_email': self.email_from,
                'default_customer': False,
                'default_is_prospect': True,
                'order_line': order_line,
                'opportunity_id': self.id,
                'sale_order': True
            }
            view = self.env.ref('prospect_creation.prospect_creation_view_form')
            return {
                'name': 'Create Prospect',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'prospect.creation.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }


    @api.multi
    def _create_lead_partner(self):
        """ Create a partner from lead data
            :returns res.partner record
        """
        #print('>>>>>>>>> LeadInherit _create_lead_partner >>>>>>')
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name:
            partner_company = Partner.create(self._create_lead_partner_data(self.partner_name, True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            raise ValidationError(_('Please Fill Up the Company Name!'))

        if contact_name:
            Partner.create(self._create_lead_partner_data(contact_name, False, partner_company.id if partner_company else False))
        # Return partner company to be the default customer (partner_id)
        if partner_company:
            return partner_company

        return Partner.create(self._create_lead_partner_data(self.name, False))


    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        #print('>>>>>>>>> LeadInherit _create_lead_partner >>>>>>')
        email_split = tools.email_split(self.email_from)

        if is_company:
            return {
                'name': name,
                'user_id': self.env.context.get('default_user_id') or self.user_id.id,
                'comment': self.description,
                'team_id': self.team_id.id,
                'parent_id': parent_id,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': email_split[0] if email_split else False,
                'title': self.title.id,
                'function': self.function,
                'street': self.street,
                'street2': self.street2,
                'zip': self.zip,
                'city': self.city,
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'website': self.website,
                'is_company': is_company,
                'customer': False,
                'is_prospect': True,
                'type': 'contact'
            }

        else:
            return {
                'name': name,
                'user_id': self.env.context.get('default_user_id') or self.user_id.id,
                'comment': self.description,
                'team_id': self.team_id.id,
                'parent_id': parent_id,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': email_split[0] if email_split else False,
                'title': self.title.id,
                'function': self.function,
                'street': self.street,
                'street2': self.street2,
                'zip': self.zip,
                'city': self.city,
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'website': self.website,
                'is_company': False,
                'customer': False,
                'is_prospect': False,
                'type': 'contact'
            }


class CRMLead2Opportunity(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    action = fields.Selection(
        [('exist', 'Link to an existing customer'), ('create', 'Create a new prospect'),
         ('nothing', 'Do not link to a customer')],
        'Related Customer', default="create")


class CrmLine(models.Model):
    _name = 'crm.line'
    _description = 'Crm Line Ids'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'price', 'currency_id')
    def get_sub_total(self):
        for res in self:
            res.sub_total = res.product_uom_qty * res.price

    crm_lead_id = fields.Many2one('crm.lead')
    categ_id = fields.Many2one('product.category', string="Product Catagory")
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price = fields.Monetary('Price')
    currency_id = fields.Many2one('res.currency')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sub_total = fields.Float(string="Sub Total", compute="get_sub_total")

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        result = {'domain': domain}
        vals['categ_id'] = self.product_id.categ_id.id
        vals['price'] = self.product_id.lst_price
        self.update(vals)

        return result
