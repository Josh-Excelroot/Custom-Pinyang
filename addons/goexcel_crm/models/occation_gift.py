from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class GiftCelebration(models.Model):
    _name = 'gift.celebration'
    _description = 'Gift Celebration Detail'
    _order = 'date desc, id desc'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    occasion_id = fields.Many2one('gift.occasion', string="Occasion")
    date = fields.Date(string="Date", track_visibility='always')
    sequence = fields.Integer(default=10)
    gift_line_ids = fields.One2many('gift.line', 'gift_id')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled'), ('reject', 'Reject')], string="Status",
                             default="draft", track_visibility='always')
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True, track_visibility='always')
    rejected_by = fields.Many2one('res.users', string="Rejected By", readonly=True, track_visibility='always')
    is_approver = fields.Boolean(string="Is Approver", compute="get_approver_detail", track_visibility='always')
    gift_type = fields.Selection([('occasion', 'Occasion')], string="Gift Type", default='occasion', track_visibility='always')
    requested_user_id = fields.Many2one('res.users', string="Request By", default=lambda self: self.env.uid,
                                        track_visibility='always')
    remark = fields.Text(string="Remark", track_visibility='always')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('gift.celebration') or 'New'
        return super(GiftCelebration, self).create(vals)

    def get_approver_detail(self):
        current_user_id = self.env.uid
        for res in self:
            if current_user_id in res.company_id.gift_approver_ids.ids:
                res.is_approver = True
            else:
                res.is_approver = False

    #kashif 4july23: fix multi Do issue creation in gift
    @api.multi
    def action_done(self):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
        customer_loc, supplier_loc = warehouse_id._get_partner_locations()
        location_id = warehouse_id.wh_output_stock_loc_id
        location_dest_id = customer_loc
        partner = self.gift_line_ids.mapped('partner_id')
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', warehouse_id.id)], limit=1)
        if not picking_type:
            raise ValidationError(_("There is no Picking Type for internal transfer"))
        picking = {
            'picking_type_id': picking_type.id,
            'origin': self.name,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': partner[0].id,
            'is_from_gift': True,
            'name': self.env['ir.sequence'].next_by_code('gift.delivery.order')
        }
        picking_id = self.env['stock.picking'].create(picking)
        for line in self.gift_line_ids.filtered(lambda x: not x.picking_id):
            self.env['stock.move'].create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'quantity_done': line.product_uom_qty,
                    'product_uom': line.product_uom.id if line.product_uom else line.product_id.uom_id.id,
                    'name': self.name + line.product_id.name,
                    'picking_id': picking_id.id,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                })

            line.picking_id = picking_id.id
        picking_id.button_validate()
        self.write({'state': 'done'})
    #end
    @api.multi
    def action_reject(self):
        self.write({'state': 'reject', 'rejected_by': self.env.uid})
        template = self.env.ref('goexcel_crm.gift_rejected_mail_template')
        assert template._name == 'mail.template'
        email_lst = [self.requested_user_id.partner_id.email]
        email_to = ','.join(map(str, email_lst))
        if template:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def action_to_approve(self):
        self.write({'state': 'to_approve'})
        template = self.env.ref('goexcel_crm.gift_approval_req_mail_template')
        assert template._name == 'mail.template'
        email_lst = []
        email_lst += [partner.email for partner in filter(lambda x: x.email, self.company_id.gift_approver_ids)]
        email_to = ','.join(map(str, email_lst))
        if template:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def action_to_approved(self):
        self.write({'state': 'approved', 'approved_by': self.env.uid})
        template = self.env.ref('goexcel_crm.gift_approved_mail_template')
        assert template._name == 'mail.template'
        email_lst = [self.requested_user_id.partner_id.email]
        email_to = ','.join(map(str, email_lst))
        if template:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

        template = self.env.ref('goexcel_crm.gift_approved_ntfy_mail_template')
        assert template._name == 'mail.template'
        email_lst += [partner.email for partner in filter(lambda x: x.email, self.company_id.gift_approved_notification)]
        email_to = ','.join(map(str, email_lst))
        if template:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def action_to_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})


class GiftLine(models.Model):
    _name = 'gift.line'
    _description = 'Gift Line Detail'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.depends('product_id', 'product_uom_qty', 'price')
    def get_total(self):
        for res in self:
            res.sub_total = res.product_uom_qty * res.price

    gift_id = fields.Many2one('gift.celebration', string="Gift")
    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Customer")
    product_uom_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    gift_date = fields.Date("Gift Date")
    price = fields.Float("Cost")
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    sub_total = fields.Float(string="Total", compute="get_total")
    picking_id = fields.Many2one('stock.picking', 'Delivery Order')

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
        vals['price'] = self.product_id.standard_price
        self.update(vals)

        return result


class GiftOccation(models.Model):
    _name = 'gift.occasion'
    _description = "Gift Occasion"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]
