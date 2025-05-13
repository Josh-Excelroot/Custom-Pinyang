from odoo import api, models, fields, _
from odoo.addons import decimal_precision as dp
import datetime as DT


class SaleJournary(models.Model):
    _name = 'sale.journary'
    _description = 'Sale Journary'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=10)
    stage_id = fields.Many2one('crm.stage', string="Stage")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class BuyingJournary(models.Model):
    _name = 'buying.journary'
    _description = 'Buying Journary'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=10)
    stage_id = fields.Many2one('crm.stage', string="Stage")
    sale_journay_id = fields.Many2one('sale.journary', string="Sale Journary")
    buyer_id = fields.Many2one('res.partner', string="Buyer")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    buying_journary_detail_ids = fields.One2many('buying.journary.detail', 'buying_journry_id', string="Detail")

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class BuyingJournaryDetail(models.Model):
    _name = 'buying.journary.detail'
    _description = 'Buying Journary Detail'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    buying_journry_id = fields.Many2one('buying.journary', string="Buying Journary", required=True, ondelete='cascade')
    sale_journay_id = fields.Many2one('sale.journary', string="Sale Journary")
    crm_id = fields.Many2one('crm.lead', string="Lead")
    sequence = fields.Integer(default=10)
    stage_id = fields.Many2one('crm.stage', string="Stage")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, crm_id, stage_id)', 'Data must be unique within an application!')]

    @api.onchange('buying_journry_id')
    def onchanage_buying_journry_id(self):
        for res in self:
            if self.buying_journry_id:
                self.sale_journay_id = self.buying_journry_id.sale_journay_id and self.buying_journry_id.sale_journay_id.id or False


class CommunicationMethod(models.Model):
    _name = 'communication.method'
    _description = 'Communication Method'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(default=10)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    line_ids = fields.One2many('communication.method.line', 'com_method_id', string="Customer Detail")

    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class CommunicationMethodLine(models.Model):
    _name = 'communication.method.line'
    _description = 'Communication Method'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    com_method_id = fields.Many2one('communication.method', string="Communication", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)
    active = fields.Boolean('Active', default=True)


class CustomerPriority(models.Model):
    _name = 'customer.priority'
    _description = 'Customer Priority'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text(string="Description")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)
    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class CustomerSector(models.Model):
    _name = 'customer.sector'
    _description = 'Customer Sector'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True, required=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    industry_ids = fields.One2many('res.partner.industry', 'sector_id', string="Industry")
    sequence = fields.Integer(default=10)
    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"
    _description = 'Industry'
    _order = "name"

    sector_id = fields.Many2one('customer.sector', string="Principal Sector")
    sequence = fields.Integer(default=10)


class CustomerBrand(models.Model):
    _name = 'customer.brand'
    _description = 'Customer Brand'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True, required=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    customer_ids = fields.One2many('customer.brand.line', 'brand_id', string="Brand Detail")
    competitor_brand_ids = fields.One2many('competetitor.brand.line', 'brand_id', string="Brand Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CustomerBrandLine(models.Model):
    _name = 'customer.brand.line'
    _description = 'Customer Brand'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    brand_id = fields.Many2one('customer.brand', string="Brand", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string="SKU")
    product_uom_id = fields.Many2one('uom.uom', string='UOM')
    vol_ltr_usag = fields.Char(string="Vol-Ltr/Usag")


class CompetetitorBrandLine(models.Model):
    _name = 'competetitor.brand.line'
    _description = 'Competetitor Brand'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    brand_id = fields.Many2one('customer.brand', string="Brand", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    remark = fields.Text('Remark')
    sequence = fields.Integer(default=10)
    product_group_id = fields.Many2one('product.group', string="Product Group")
    inventory_vol = fields.Char(string="Inventory Vol")
    vol_mnt_date = fields.Char(string="Vol-Ltr/Usag")


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = "Product Group"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class ProductGrade(models.Model):
    _name = 'product.grade'
    _description = "Product Grade"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = "Product Group"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = "Product Brand"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class TypeOfProduct(models.Model):
    _name = 'type.of.product'
    _description = "Type of Product"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class ReligiousFestival(models.Model):
    _name = 'religious.fetsival'
    _description = 'Religious Festival'
    _order = 'id desc'

    name = fields.Char(string="Religious Festival", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    line_ids = fields.One2many('religious.fetsival.line', 'religious_id', string="Customer Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class ReligiousFestivalLine(models.Model):
    _name = 'religious.fetsival.line'
    _description = 'Religious Festival'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    religious_id = fields.Many2one('religious.fetsival', string="Religious Festival", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    # @api.multi
    # def create(self, vals):
    #     if 'partner_id' in vals and 'religious_id' in vals:
    #         domain = [('partner_id', '=', vals['partner_id']), ('religious_id', '=', vals['religious_id']), ('company_id', '=', self.env.user.company_id)]
    #         if not self.search(domain):
    #             return super(ReligiousFestivalLine, self).create(vals)
    #     return 

class OrderStyle(models.Model):
    _name = 'order.style'
    _description = 'Order Style'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    line_ids = fields.One2many('order.style.line', 'style_id', string="Cust Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class OrderStyleLine(models.Model):
    _name = 'order.style.line'
    _description = 'Srder Style'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    style_id = fields.Many2one('order.style', string="Order Style", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class InvoiceMethod(models.Model):
    _name = 'invoice.method'
    _description = 'Invoice Method'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True, required=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    invoice_method_line_ids = fields.One2many('invoice.method.line', 'method_id', string="Cust Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class InvoiceMethodLine(models.Model):
    _name = 'invoice.method.line'
    _description = 'Invoice Method Line'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    method_id = fields.Many2one('invoice.method', string="Method", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(string='Color Index')
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    payment_mode_lines_ids = fields.One2many('payment.mode.line', 'payment_mode_id', string="Partner Detail")
    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class PaymentModeLine(models.Model):
    _name = 'payment.mode.line'
    _description = 'Payment Mode'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Contact", required=True, ondelete='cascade')
    payment_mode_id = fields.Many2one('payment.mode', string="Mode", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class PersonalityContact(models.Model):
    _name = 'personality.contact'
    _description = 'Personality Contact'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, track_visibility='onchange')
    contact_1_id = fields.Many2one('res.partner', string="Contact 1", track_visibility='onchange')
    contact_2_id = fields.Many2one('res.partner', string="Contact 2", track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True}, track_visibility='onchange')
    relationship = fields.Selection([('dotted_line', 'Dotted Line To'), ('reported_to', 'Reported To')], string="Relationship", track_visibility='onchange')
    occupation = fields.Selection([('initiator', 'Initiator'), ('purchaser', 'Purchaser'), ('influencer', 'Influencer'), ('gatekeeper', 'Gatekeeper'), ('decider', 'Decider'), ('user', 'User'), ('supporter', 'Supporter')],
                                  track_visibility='onchange', string="Influence Type")
    buyer_relationship_id = fields.Many2one('buyer.relationship', string="Influence Type")
    decision_per = fields.Float(string="Percentage", track_visibility='onchange', digits=dp.get_precision('bps percentage'))
    sequence = fields.Integer(default=10)


class BuyingRelationship(models.Model):
    _name = 'buyer.relationship'
    _description = "Buyer Relation"

    sequence = fields.Integer(default=10)
    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True}, track_visibility='onchange')


class TypeOfCustomer(models.Model):
    _name = 'type.of.partner'
    _description = 'Type Of Customer'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class TypeOfPurchase(models.Model):
    _name = 'type.of.purchase'
    _description = 'Type Of Purchase'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class TechnicalPlan(models.Model):
    _name = 'technical.plan'
    _description = 'Type Of Customer'
    _order = 'id desc'

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')
    ]


class TechnicalCustomerPlan(models.Model):
    _name = 'technical.customer.plan'
    _description = 'Technical Plan for Customer'

    name = fields.Char(string='Technical Plan No', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    technical_plan = fields.Many2one('technical.plan', string="Technical Plan")
    date = fields.Datetime(string="Date")
    remark = fields.Text(string="Remark")
    owner_id = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string="Customer")
    contact_person_id = fields.Many2one('res.partner', string="Contact Person")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)
    contact_person_ids = fields.Many2many('res.partner', string="Contact Person")
    involved_parties_ids = fields.Many2many('res.users', string="Involved Parties")
    schedule_reminder = fields.Date(string="Schedule Reminder")
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled'), ('reject', 'Reject')], string="Status", default="draft")
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    rejected_by = fields.Many2one('res.users', string="Rejected By", readonly=True)
    volume_per_month = fields.Char(string="Volume per Month")
    purpose = fields.Text(stibng="Purpose")
    objective = fields.Text(stibng="Objective")
    premise = fields.Text(stibng="Premise")
    strategy = fields.Text(stibng="Strategy")
    anticipate = fields.Text(stibng="Anticipate")
    is_approver = fields.Boolean(string="Is Approver", compute="get_approver_detail")

    def get_approver_detail(self):
        current_user_id = self.env.uid
        for res in self:
            if current_user_id in res.company_id.technical_plan_approver_ids.ids:
                res.is_approver = True
            else:
                res.is_approver = False

    @api.multi
    def action_to_approve(self):
        self.write({'state': 'to_approve'})

    @api.multi
    def action_to_approved(self):
        self.write({'state': 'approved'})

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        pass

    @api.multi
    def action_to_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('technical.customer.plan') or 'New'
        return super(TechnicalCustomerPlan, self).create(vals)

    @api.multi
    def send_reminder(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('goexcel_crm', 'technical_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'technical.customer.plan',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'default_partner_ids': [i.id for i in self.contact_person_ids]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_reminder_scheduler(self):
        data_ids = self.env['technical.customer.plan'].search([('schedule_reminder', '=', DT.date.today())])
        print ("data_ids:::::", data_ids)
        if data_ids:
            template = self.env.ref('goexcel_crm.technical_mail_template')
            assert template._name == 'mail.template'
            for so in data_ids:
                email_lst = []
                email_lst += [partner.email for partner in filter(
                    lambda x: x.email, so.contact_person_ids)]
                email_lst += [user.email for user in filter(
                    lambda x: x.email, so.involved_parties_ids)]
                print ("email_lst:::::", email_lst)
                email_to = ','.join(map(str, email_lst))
                if template:
                    template.write({'email_to': email_to})
                    template.send_mail(so.id, force_send=True)


class DepartmentDepartment(models.Model):
    _name = 'department.department'
    _description = "Department"

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class MachinaryDetail(models.Model):
    _name = 'machine.machine'
    _description = "Machine Detail"

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(MachinaryDetail, self).name_search(name, args=None, operator='ilike', limit=100)
        sector_id = self._context.get('type_of_sector_id', False)
        industry_id = self._context.get('type_of_industry_id', False)
        domain = []
        if sector_id:
            domain = [('sector_id', '=', sector_id)]
        if industry_id:
            domain += [(('industry_id', '=', industry_id))]
            args = args or []
            ds_ids = self.env['discovery.sheet'].search(domain)
            machine_ids = []
            for ds in ds_ids:
                for d in ds.product_line_ids:
                    machine_ids.append(d.machine_id.id)
            recs = self.search([('id', 'in', machine_ids)] + args, limit=limit)
            return recs.name_get()
        return res


class DiscoverySheet(models.Model):
    _name = 'discovery.sheet'
    _description = "Discription Sheet"

    @api.depends('sector_id', 'industry_id')
    def compute_name(self):
        for res in self:
            res.name = 'New'
            if res.sector_id and res.industry_id:
                res.name = res.sector_id.name + " - " + res.industry_id.name
            elif res.sector_id and not res.industry_id:
                res.name = res.sector_id.name
            elif res.industry_id and not res.sector_id:
                res.name = res.industry_id.name

    name = fields.Char(string="Name", compute="compute_name", store=True)
    sector_id = fields.Many2one('customer.sector', string="Sector")
    industry_id = fields.Many2one('res.partner.industry', string="Industry")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})
    product_line_ids = fields.One2many('discovery.sheet.line', 'discovery_id', string="Products")


class DiscoverySheetLine(models.Model):
    _name = 'discovery.sheet.line'
    _description = "Discription Sheet Line"

    discovery_id = fields.Many2one('discovery.sheet', string="Discovery Sheet")
    machine_id = fields.Many2one('machine.machine', string="Machine")
    product_group_id = fields.Many2one('product.group', string="Product Group")
    product_category_id = fields.Many2one('product.category', string="Product Category")
    product_ids = fields.Many2many('product.product', 'product_partner_sheet_ref', 'product_id', 'machine_id', string="SKU")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    @api.onchange('product_group_id')
    def onchange_product_group_id(self):
        if self.product_group_id:
            return {'domain': {'product_category_id': [('product_group_id', '=', self.product_group_id.id)]}}
            # self.product_category_id = False
            # domain="[('product_group_id', '=', product_group_id)]"

    @api.onchange('product_category_id')
    def onchange_product_category_id(self):
        if self.product_category_id and not self.product_group_id:
            self.product_group_id = self.product_category_id.product_group_id and self.product_category_id.product_group_id.id or False


class CustomerMachineLne(models.Model):
    _name = 'customer.machine'
    _description = "Customer Machine Detail"

    partner_id = fields.Many2one('res.partner', string="Customer")
    machine_id = fields.Many2one('machine.machine', string="Machine")
    qty = fields.Float(string="Quantity")
    product_group_id = fields.Many2one('product.group', string="Product Group")
    product_category_id = fields.Many2one('product.category', string="Product Category")
    product_ids = fields.Many2many('product.product', 'product_partner_machine_ref', 'product_id', 'machine_id', string="SKU")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id, help='The company this user is currently working for.', context={'user_preference': True})

    @api.multi
    def give_sheet_details(self):
        domain = [('sector_id', '=', self.partner_id.type_of_sector_id.id)]
        domain += [(('industry_id', '=', self.partner_id.type_of_industry_id.id))]
        return self.env['discovery.sheet'].search(domain)

    @api.onchange('machine_id')
    def onchange_machine(self):
        if self.partner_id and self.partner_id.type_of_sector_id and self.partner_id.type_of_industry_id:
            sheet_ids = self.give_sheet_details()
            # find sheet line
            line_domain = [('machine_id', '=', self.machine_id.id)]
            line_domain += [('discovery_id', 'in', sheet_ids.ids)]
            line_ids = self.env['discovery.sheet.line'].search(line_domain)
            product_group_ids = [grp.product_group_id.id for grp in line_ids]
            product_category_ids = [grp.product_category_id.id for grp in line_ids]
            # product_ids = [grp.product_ids.ids for grp in line_ids]
            product_ids = [grp.product_ids for grp in line_ids if len(grp.product_ids) > 0]
            if len(product_group_ids) == 1:
                self.product_group_id = product_group_ids[0]
            if len(product_category_ids) == 1:
                self.product_category_id = product_category_ids[0]
            a_list = []
            for p_lst in product_ids:
                a_list += [grp.id for grp in p_lst if grp]
            return {'domain': {'product_group_id': [('id', 'in', product_group_ids)], 'product_category_id': [('id', 'in', product_category_ids)], 'product_ids': [('id', 'in', a_list)]}}

    @api.onchange('product_group_id')
    def onchange_product_group_id(self):
        if self.partner_id and self.partner_id.type_of_sector_id and self.partner_id.type_of_industry_id:
            sheet_ids = self.give_sheet_details()
            # find sheet line
            line_domain = [('machine_id', '=', self.machine_id.id)]
            line_domain += [('discovery_id', 'in', sheet_ids.ids)]
            line_domain += [('product_group_id', '=', self.product_group_id.id)]
            line_ids = self.env['discovery.sheet.line'].search(line_domain)
            product_category_ids = [grp.product_category_id.id for grp in line_ids]
            # product_ids = [grp.product_ids.ids for grp in line_ids]
            product_ids = [grp.product_ids for grp in line_ids if len(grp.product_ids) > 0]
            if len(product_category_ids) == 1:
                self.product_category_id = product_category_ids[0]
            a_list = []
            for p_lst in product_ids:
                a_list += [grp.id for grp in p_lst if grp]
            return {'domain': {'product_category_id': [('id', 'in', product_category_ids)], 'product_ids': [('id', 'in', a_list)]}}

    @api.onchange('product_category_id')
    def onchange_product_category_id(self):
        if self.partner_id and self.partner_id.type_of_sector_id and self.partner_id.type_of_industry_id:
            sheet_ids = self.give_sheet_details()
            # find sheet line
            line_domain = [('machine_id', '=', self.machine_id.id)]
            line_domain += [('discovery_id', 'in', sheet_ids.ids)]
            line_domain += [('product_group_id', '=', self.product_group_id.id)]
            line_domain += [('product_category_id', '=', self.product_category_id.id)]
            line_ids = self.env['discovery.sheet.line'].search(line_domain)
            product_ids = [grp.product_ids for grp in line_ids if len(grp.product_ids) > 0]
            a_list = []
            for p_lst in product_ids:
                a_list += [grp.id for grp in p_lst]
            return {'domain': {'product_ids': [('id', 'in', a_list)]}}
