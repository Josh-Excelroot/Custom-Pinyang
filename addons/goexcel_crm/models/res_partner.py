from odoo import api, models, fields, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

from lxml import etree
import json
import ast


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_company = fields.Boolean(string='Is a Company', default=True, help="Check if the contact is a company, otherwise it is a person")

    type_cust_id = fields.Many2one('type.of.partner', string="Type of Customer", track_visibility='onchange', copy=False)
    type_of_sector_id = fields.Many2one('customer.sector', string="Type of Sector", track_visibility='onchange', copy=False)
    type_of_industry_id = fields.Many2one('res.partner.industry', string="Type of Industry", track_visibility='onchange', copy=False)
    type_of_purchase_id = fields.Many2one('type.of.purchase', string="Type of Purchase", track_visibility='onchange', copy=False)
    industry_remark = fields.Text(string="Industry Remark", copy=False)
    # custmer_brand_ids = fields.Many2many('customer.brand', 'brand_cust_relation', string="Customer Brand", track_visibility='onchange')
    competitor_remark = fields.Char(string="Competitor Remark", track_visibility='onchange', copy=False)
    cust_growth_rate = fields.Float(string="Growth Rate%", track_visibility='onchange', digits=dp.get_precision('bps percentage'), copy=False)
    reason_growth_rate = fields.Char(string="Reason", copy=False)
    facebook_url = fields.Char(string="Facebook", track_visibility='onchange', copy=False)
    instagram_url = fields.Char(string="Instagram", track_visibility='onchange', copy=False)
    twitter_url = fields.Char(string="Twiter", track_visibility='onchange', copy=False)
    linkedin_url = fields.Char(string="Linkedin", track_visibility='onchange', copy=False)

    after_sale_expectaion = fields.Text(string="Customer Expectation", track_visibility='onchange', copy=False)

    strength = fields.Text(string="Strength", track_visibility='onchange', copy=False)
    weakness = fields.Text(string="Weakness", track_visibility='onchange', copy=False)
    opportunity_id = fields.Text(string="Opportunity", track_visibility='onchange', copy=False)
    threat = fields.Text(string="Threat", track_visibility='onchange', copy=False)
    remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)
    cust_so_pattern = fields.Selection([('0', '0'), ('0.25', '0.25'), ('0.5', '0.5'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'),
                                        ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12')], default='0', string="Sale order pattern", track_visibility='onchange', copy=False)
    cust_priority_id = fields.Many2one('customer.priority', string="Customer Priority", track_visibility="onchange", copy=False)
    p_of_contact = fields.Selection([('dominance', 'Dominance'), ('influence', 'Influence'), ('steadiness', 'Steadiness'), ('conscientiousness', 'Conscientiousness')], string="Personality", track_visibility='onchange', copy=False)
    religious_festival_ids = fields.One2many('religious.fetsival.line', 'partner_id', string="Religious Festival", track_visibility='onchange', copy=False)
    custmer_brand_ids = fields.One2many('customer.brand.line', 'partner_id', string="Customer Brand", track_visibility='onchange', copy=False)
    competitor_brand_ids = fields.One2many('competetitor.brand.line', 'partner_id', string="Competitor Brand", track_visibility='onchange', copy=False)
    upsale_product_ids = fields.One2many('cros.sale.product', 'partner_id', string="Upsell Product", track_visibility='onchange', copy=False)
    cros_sele_product_ids = fields.One2many('up.sale.product', 'partner_id', string="Cross-Sell Product", track_visibility='onchange', copy=False)
    payment_mode_ids = fields.One2many('payment.mode.line', 'partner_id', string="Payment Mode", track_visibility='onchange', copy=False)
    communication_method_ids = fields.One2many('communication.method.line', 'partner_id', string="Communication Method", track_visibility='onchange', copy=False)

    type = fields.Selection(selection_add=[('related_company', 'Related Company'), ('order_address', 'Order Address')])
    best_fitted_item_ids = fields.One2many('best.fitted.product', 'partner_id', string="Best Fitted Product", track_visibility='onchange', copy=False)
    invoice_method_ids = fields.One2many('invoice.method.line', 'partner_id', string="Invoice Method", track_visibility="onchange", copy=False)
    order_style_ids = fields.One2many('order.style.line', 'partner_id', string="Order Style", copy=False)
    pain_analysis_ids = fields.One2many('customer.pain.analysis', 'partner_id', string="Pain Analysis", track_visibility='onchange', copy=False)
    needs_analysis_ids = fields.One2many('customer.needs.analysis', 'partner_id', string="Needs Analysis", track_visibility='onchange', copy=False)
    challenges_analysis_ids = fields.One2many('customer.challenges.analysis', 'partner_id', string="Challenges Analysis", track_visibility='onchange', copy=False)
    value_solution_ids = fields.One2many('customer.value.solution', 'partner_id', string="Value Solution", copy=False)
    tech_plan_detail_ids = fields.One2many('technical.customer.plan', 'partner_id', string="Customer Plan", copy=False)
    operating_hours_ids = fields.One2many('operating.hours', 'partner_id', string="Operating Hours", copy=False)
    phone2 = fields.Char('Phone2', copy=False)
    phone3 = fields.Char('Phone3', copy=False)
    visiting_hr_ids = fields.One2many('visiting.hours', 'partner_id', string="Connecting Time", copy=False)
    personality_contact_ids = fields.One2many('personality.contact', 'partner_id', string="Personality Contact", copy=False)
    history_ids = fields.One2many('salesperson.customer.history', 'partner_id', readonly=True, copy=False)
    related_compnay_id = fields.Many2one('res.partner', string="Related Compnay", copy=False)
    status = fields.Selection([('active', 'Active'), ('lost_customer', 'Lost Customer'), ('lost_lead', 'Lost Lead'),
                               ('suspended', 'Suspended'), ('debt', 'Bad Debt'), ('dormant', 'Dormant'),
                               ('inactive', 'Inactive')], string="Status", copy=False)
    is_multibrand = fields.Boolean(string="Multibrand", compute="get_is_multibrand", store=True, copy=False)
    company_registry = fields.Char(string="Company Registry", copy=False)
    churn_review = fields.Text(string="churn review", copy=False)
    churn_review_date = fields.Date(string="Review Date", copy=False)
    lost_reason_id = fields.Many2one('crm.lost.reason', string="Lost Reason", copy=False)
    lost_date = fields.Date(string="Lost Date", copy=False)

    cust_machine_ids = fields.One2many('customer.machine', 'partner_id', string="Machine Detail", copy=False)

    # fields for contact person
    department_id = fields.Many2one('department.department', string="Department", copy=False)
    pain_point = fields.Text(string="Pain Points", copy=False)
    pain_challanges = fields.Text(string="Pain Challanges", copy=False)
    contact_goal = fields.Text(string="Goal", copy=False)
    contact_dob = fields.Date(string="DOB", copy=False)
    contact_gender = fields.Selection([('m', 'Male'), ('f', 'Female')], string="Gender", copy=False)
    contact_personality = fields.Selection([('dominance', 'Dominance'), ('influence', 'Influence'), ('steadiness', 'Steadiness'), ('conscientiousness', 'Conscientiousness')], string="Personality", track_visibility='onchange', copy=False)
    contact_speak = fields.Text(string="Speak", copy=False)
    contact_solution_pain = fields.Text(string="Pain Solution", copy=False)
    remark_note = fields.Text(string="Remark note")

    # @api.constrains('name', 'company_id', 'company_type', 'is_company')
    # def _check_duplicate_contact(self):
    #     for res in self:
    #         if not res.company_id:
    #             res.company_id = self.env.user.company_id.id
    #         if len(self.env['res.partner'].search([('name', '=', res.name), ('is_company', '=', True), ('company_id', '=', res.company_id.id)])) > 1:
    #             raise ValidationError(_('You cannot have a Same Name Customer/Vendor Twice'))

    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)

    @api.depends('competitor_brand_ids')
    def get_is_multibrand(self):
        for res in self:
            if len(res.competitor_brand_ids) > 1:
                res.is_multibrand = True
            else:
                res.is_multibrand = False

    @api.model
    def create(self, vals):
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
        if 'customer' in vals and 'email' in vals:
            vals['default_payment_email'] = True
        res = super(ResPartner, self).create(vals)
        if res and res.type == 'related_company':
            res.customer = False
            res.name = res.related_compnay_id.name
        if res and 'user_id' in vals:
            history_vals = {'user_id': vals['user_id'],
                            'partner_id': res.id,
                            'from_date': fields.date.today()}
            self.env['salesperson.customer.history'].create(history_vals)
        if res.street and res.zip and res.city and res.state_id and res.country_id:
            res.geo_localize()
        # kashif 27sept23: added code to handel child partner not assigned with user id by default
        if res.parent_id and not res.user_id:
            res.user_id = res.parent_id.user_id.id
        return res

    @api.multi
    def write(self, vals):
        if 'type' in vals and vals['type'] == 'related_company':
            vals.update({'customer': False})
        if 'customer' in vals and 'email' in vals:
            vals.update({'default_payment_email': True})
        res = super(ResPartner, self).write(vals)
        if 'user_id' in vals:
            for rec in self:
                if rec.user_id:
                    old_rec = self.env['salesperson.customer.history'].sudo().search([('partner_id', '=', rec.id),
                                                                               ('to_date', '=', False)], limit=1)
                    if old_rec:
                        old_rec.to_date = fields.date.today()
                    self.env['salesperson.customer.history'].sudo().create({'user_id': vals['user_id'],
                                                                     'partner_id': rec.id,
                                                                     'from_date': fields.date.today()})
                else:
                    self.env['salesperson.customer.history'].sudo().create({'user_id': vals['user_id'],
                                                                     'partner_id': rec.id,
                                                                     'from_date': fields.date.today()})
        if 'street' in vals or 'zip' in vals or 'city' in vals or 'state_id' in vals or 'country_id' in vals:
            self.geo_localize()
        # if 'ref' in vals:
        #     self.name_get()
        return res

    @api.multi
    def change_credit_data(self):
        pass

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            user = self.env.user
            user_is_crm_sale_person = user.has_group('goexcel_bps_security.crm_group_user')
            user_is_crm_manager = user.has_group('goexcel_bps_security.crm_group_manager')
            user_is_account_manager = user.has_group('account.group_account_manager')
            user_is_account_user = user.has_group('account.group_account_invoice')
            #if (user_is_crm_sale_person and not user_is_crm_manager) or not user_is_crm_sale_person:
            if not user_is_account_user and not user_is_account_manager:
                # Make sale purchase page fields readonly for the user who is only sale person and not manager
                doc = etree.XML(res['arch'])
                for field in doc.xpath("//notebook/page[@name='sales_purchases']//field"):
                    if field.get('name') == 'delivery_note':
                        continue
                    modifiers_dict = ast.literal_eval(
                        field.get('modifiers').replace('true', 'True').replace('false', 'False'))
                    modifiers_dict['readonly'] = True
                    # replace Title Case to lower case to make it readable for JS
                    modifiers_str = str(modifiers_dict).replace("'", '"').replace('True', 'true').replace('False',
                                                                                                          'false')
                    field.set('modifiers', modifiers_str)
                #kashif 4july23: readonly status field for non accounting users
                status_field = doc.xpath("//field[@name='status']")
                if status_field:
                    status_field= status_field[0]
                    status_field.set('readonly', '1')
                    modifiers = json.loads(status_field.get("modifiers"))
                    modifiers['readonly'] = True
                    status_field.set("modifiers", json.dumps(modifiers))
                #end
                res['arch'] = etree.tostring(doc)

            # kashif 3oct23: readonly prospect field for DSR users
            params = self.env.context.get('params')
            record = False
            if params and params.get('id'):
                record = self.env[params.get('model')].search([('id', '=', params.get('id'))])
            if record:
                if record.user_id.id == self.env.user.id:
                    doc = etree.XML(res['arch'])
                    prospect_field = doc.xpath("//field[@name='is_prospect']")
                    if prospect_field:
                        prospect_field = prospect_field[0]
                        prospect_field.set('readonly', '1')
                        modifiers = json.loads(prospect_field.get("modifiers"))
                        modifiers['readonly'] = True
                        prospect_field.set("modifiers", json.dumps(modifiers))
                        res['arch'] = etree.tostring(doc)

        return res


class CrosSaleProduct(models.Model):
    _name = 'cros.sale.product'
    _description = 'Cros Sale Product'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    product_id = fields.Many2one('product.product', string="Product", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class UpSaleProduct(models.Model):
    _name = 'up.sale.product'
    _description = 'Up Sale Product'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    product_id = fields.Many2one('product.product', string="Product", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class BestFittedProduct(models.Model):
    _name = 'best.fitted.product'
    _description = 'Best Fitted Product'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    product_id = fields.Many2one('product.product', string="Product", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class SalespersonCustomerHistory(models.Model):
    _name = 'salesperson.customer.history'
    _description = 'Salesperson Customer History'

    partner_id = fields.Many2one('res.partner', string="Customer")
    user_id = fields.Many2one('res.users', string="SalesPerson")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")


# class CustomerStatus(models.Model):
#     _name = "customer.status"
#     _description = "Customer Status"

#     @api.model
#     def _get_company(self):
#         return self.env.user.company_id
#     name = fields.Char(string="Name")
