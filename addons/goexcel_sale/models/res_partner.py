# See LICENSE file for full copyright and licensing details.
import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?', track_visibility='onchange', copy=False)
    credit_limit = fields.Float(string='Credit limit', digits=dp.get_precision('Product Price'),
                                track_visibility='onchange',
                                company_dependent=True, default=7000, copy=False)
    sales_person_ids = fields.One2many('parter.sales.person', 'partner_id', string="List of SalesPerson", copy=False)
    is_overdue_block = fields.Boolean(string="Invoice Overdue Block", copy=False, default=True)
    check_overdue_block_readonly = fields.Boolean(string="Overdue Block Read Only", copy=False,
                                                  compute="get_overdue_block_readonly")
    first_sale_order_id = fields.Many2one('sale.order', string="First Sale Order", copy=False)
    first_order_date = fields.Date(related='first_sale_order_id.first_order_date', string="First Order Date",
                                   copy=False)
    last_invoice_date = fields.Date(copy=False, string='Last Invoice Date')
    # is_overdue_block = fields.Boolean(string="Invoice Overdue Block")
    vendor_credit_limit = fields.Float(string='Vendor Credit limit', digits=dp.get_precision('Product Price'),
                                       track_visibility='onchange', copy=False)
    ref = fields.Char(string="Code", track_visibility='onchange', copy=False)
    delivery_note = fields.Text(string='Delivery Note', track_visibility='onchange', store=True)
    fork_lift = fields.Boolean(string='Fork Lift', track_visibility='onchange')

    # kashif 4may23 - modified this onchange to get parent salesperson
    @api.onchange('parent_id')
    def onchange_parent_id(self):
        result = super(ResPartner, self).onchange_parent_id()
        if self.parent_id:
            self.user_id = self.parent_id.user_id.id or False
        return result

    # end

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     if args is None:
    #         args = []
    #     partner = self.search(['|', ('city', operator, name), ('ref', operator, name)] + args, limit=limit)
    #     return partner.name_get()

    # @api.multi
    # def action_update_delivery_address(self):
    #     delivery_addresses = self.env['res.partner'].search([
    #         ('type', '=', 'delivery'),('user_id', '=', False)
    #     ])
    #     print('>>>>>>>>>>>> delivery addresses=', len(delivery_addresses))
    #     count = 0
    #     for delivery in delivery_addresses:
    #         if delivery.parent_id:
    #             if delivery.parent_id.user_id and not delivery.user_id:
    #                 delivery.write({'user_id': delivery.parent_id.user_id.id})
    #                 print('>>>>>>>>>>>> delivery addresses id=', str(delivery.id))
    #                 if count>500:
    #                     break
    #                 else:
    #                     count += 1

    @api.multi
    def action_update_vendor_location(self):
        partners = self.env['res.partner'].search([
            ('company_id', '=', self.env.user.company_id.id),
        ])
        for partner in partners:
            # print('>>>>>>>>>>>>>>>>> action_update_vendor_location partner name 1=', partner.name,
            # ' , ref=', partner.ref, ' , location=', partner.property_stock_supplier)
            if partner.property_stock_supplier and partner.property_stock_supplier.id == 8:
                # print('>>>>>>>>>>>>>>>>> action_update_vendor_location partner name 2=', partner.name,
                #       ' , ref=', partner.ref)
                partner.property_stock_supplier = 44
                # partner.write({'property_stock_supplier': 44})
                # break;

    @api.multi
    def get_overdue_block_readonly(self):
        for res in self:
            if self.env['res.users'].has_group('account.group_account_manager'):
                res.check_overdue_block_readonly = False
            else:
                res.check_overdue_block_readonly = True

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        partner_id = self._search(expression.AND([['|', '|', ('name', operator, name), (
            'city', operator, name), ('ref', operator, name)], args]), limit=limit)
        return self.browse(partner_id).name_get()

    def name_get(self):
        res = []
        for field in self:
            if field.type == 'delivery':
                res.append((field.id, '%s, %s' % (field.city, field.name)))
            else:
                res.append((field.id, '%s' % (field.name)))

        return res

    def _compute_sale_order_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_order_groups = self.env['sale.order'].read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('state', '!=', 'cancel')],
            fields=['partner_id'], groupby=['partner_id']
        )
        for group in sale_order_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.sale_order_count += group['partner_id_count']
                partner = partner.parent_id

    @api.model
    def default_get(self, fields):
        rec = super(ResPartner, self).default_get(fields)
        price_list = self.env['product.pricelist'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)], limit=1)
        rec['property_product_pricelist'] = price_list and price_list.id or False
        return rec

    @api.multi
    def action_to_credit_change(self):
        data = {
            'partner_id': self.id,
            'old_credit_term_id': self.property_payment_term_id.id or False,
            'old_credit_limit': self.credit_limit or 0.0,
            'requested_by_id': self.env.user.id
        }
        wiz_id = self.env['partner.credit.approval.wiz'].create(data)
        return {
            'name': _('Select Credit Data'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.credit.approval.wiz',
            'views': [(self.env.ref('goexcel_sale.partner_credit_change_form_view').id, 'form')],
            'view_id': self.env.ref('goexcel_sale.partner_credit_change_form_view').id,
            'target': 'new',
            'res_id': wiz_id.id
        }

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res and not res.property_product_pricelist:
            price_list = self.env['product.pricelist'].search(
                [('currency_id', '=', self.env.user.company_id.currency_id.id)], limit=1)
            if price_list:
                res.property_product_pricelist = price_list.id
        new_ref = ""
        # TS - bug 26/4/2022 to cater for shipping address and contact creation
        # TS - bug 04/8/2022 to cater for prospect - onchange_is_prospect
        if res.customer and vals['parent_id'] is False:
            char = res.name[0].capitalize()
            p_type = 'customer'
            new_ref = self.get_last_number(p_type, char)
            res.ref = new_ref
        if res.supplier and vals['parent_id'] is False:
            # print ("fsfsfsdf")
            char = res.name[0].capitalize()
            p_type = 'supplier'
            new_ref = self.get_last_number(p_type, char)
            res.ref = new_ref
        if res.name:
            res.name = res.name.upper()
        if res.street:
            res.street = res.street.upper()
        if res.street2:
            res.street2 = res.street2.upper()
        if res.city:
            res.city = res.city.upper()
        return res

    @api.multi
    def write(self, values):
        for rec in self:
            # kashif 4may23 - added this to get parent salesperson
            if rec.parent_id and rec.type == 'contact':
                if rec.parent_id.user_id:
                    values['user_id'] = rec.parent_id.user_id.id
            #end
            if 'customer' in values and values['customer']:
                values['is_prospect'] = False
                if not rec.ref:
                    char = rec.name[0].capitalize()
                    p_type = 'customer'
                    values['ref'] = rec.get_last_number(p_type, char)
            if 'supplier' in values and values['supplier']:
                if not rec.ref:
                    char = rec.name[0].capitalize()
                    p_type = 'supplier'
                    values['ref'] = rec.get_last_number(p_type, char)
            # if 'name' in values and not values.get('name').isupper():
            #     rec.name = values.get('name').upper()
            # if 'street' in values and not values.get('street').isupper():
            #     rec.street = values.get('street').upper()
            # if 'street2' in values and not values.get('street2').isupper():
            #     rec.street2 = values.get('street2').upper()
            # if 'city' in values and not values.get('city').isupper():
            #     rec.city = values.get('city').upper()
            if values.get('name') and not values.get('name').isupper():
                rec.name = values.get('name').upper()
            if values.get('street') and not values.get('street').isupper():
                rec.street = values.get('street').upper()
            if values.get('street2') and not values.get('street2').isupper():
                rec.street2 = values.get('street2').upper()
            if values.get('city') and not values.get('city').isupper():
                rec.city = values.get('city').upper()

        return super(ResPartner, self).write(values)

    def get_last_number(self, p_type, char):
        compnay = self.env.user.company_id
        if p_type and char:
            if p_type == 'customer' and compnay.enble_cust_code and compnay.customer_code:
                number = compnay.customer_code + '-' + char
                ref = '01'
                number_list = []
                for reference in self.env['res.partner'].search([('customer', '=', True), ('ref', 'ilike', number)]):
                    slited = reference.ref and reference.ref.split(char)
                    number_list.append(int(slited[1]))
                if len(number_list) > 0:
                    ref = max(number_list) + 1
                    if ref < 9:
                        ref = "0" + str(ref)
                return number + str(ref)

            if p_type == 'supplier' and self.property_account_payable_id and self.property_account_payable_id.code:
                number = str(self.property_account_payable_id.code[:3]) + '-' + char
                ref = '01'
                number_list = []
                for reference in self.env['res.partner'].search([('supplier', '=', True), ('ref', 'ilike', number)]):
                    slited = reference.ref and reference.ref.split(char)
                    number_list.append(int(slited[1]))
                if len(number_list) > 0:
                    ref = max(number_list) + 1
                    if ref < 9:
                        ref = "0" + str(ref)
                return number + str(ref)

    def check_last_invoice_and_set_status(self):
        civon_company_id, tenton_company_id = 1, 2
        today_date = datetime.datetime.now().date()
        for company_id in (civon_company_id, tenton_company_id):
            status_configs = self.env['res.partner.inactive.config'] \
                .search([('company_id', '=', company_id)], order='last_invoice_gap_days ASC')
            status_and_days = status_configs.mapped(lambda c: (c.partner_status, c.last_invoice_gap_days))
            self.env.cr.execute(f"""
                    SELECT id, last_invoice_date, status FROM res_partner p
                        LEFT JOIN res_company_assignment_res_partner_rel c ON p.id = c.res_partner_id
                        WHERE c.res_company_assignment_id = {company_id} 
                            AND p.customer = true
                            AND (p.status != 'suspended' OR p.status IS NULL)
                            AND p.last_invoice_date <= \'{datetime.datetime.now()}\';""")
            customer_data = self.env.cr.fetchall()
            for id, last_invoice_date, old_status in customer_data:
                new_status = False
                last_inv_date_diff = (today_date - last_invoice_date).days
                for status, days in status_and_days:
                    if days <= last_inv_date_diff:
                        new_status = status
                if new_status and new_status != old_status:
                    self.env.cr.execute(f"""UPDATE res_partner SET status = '{new_status}' WHERE id = {id};""")
        self.env.cr.commit()

    # def update_last_invoice_date(self):
    #     self.env.cr.execute("""
    #                 SELECT partner_id, MAX(date_invoice) FROM account_invoice
    #         WHERE type = 'out_invoice' AND state NOT IN ('draft', 'cancel')
    #         GROUP BY partner_id;""")
    #     customer_and_last_inv_date = self.env.cr.fetchall()
    #     for id, last_invoice_date in customer_and_last_inv_date:
    #         self.env.cr.execute(f'UPDATE res_partner SET last_invoice_date = \'{last_invoice_date}\' '
    #                             f'AND status = \'active\' WHERE id = {id};')
    #     self.env.cr.commit()

    def update_last_invoice_date(self):
        self.env.cr.execute("""
        SELECT partner_id, MAX(date_invoice) FROM account_invoice
            WHERE type = 'out_invoice' AND state NOT IN ('draft', 'cancel') 
            GROUP BY partner_id;""")
        customer_and_last_inv_date = self.env.cr.fetchall()
        for id, last_invoice_date in customer_and_last_inv_date:
            print(id, last_invoice_date)
            self.env.cr.execute(
                f'UPDATE res_partner SET last_invoice_date = \'{last_invoice_date}\' WHERE id = {id};')
        self.env.cr.execute(f'UPDATE res_partner SET status = \'active\' where status is NULL')
        self.env.cr.commit()

    def action_create_new_opportunity(self):
        #kashif 26june23 : added type value to opportunity
        for rec in self:
            wiz = self.env['crm.lead'].create(
                {'partner_id': rec.id,
                 "name": rec.name,
                 "user_id": rec.env.uid,
                 "company_id": rec.company_id.id,
                 "type": 'opportunity'
                 })
            return {
                "name": "Create New Opportunity",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "crm.lead",
                "target": "new",
                'res_id': wiz.id,
                "context": {},
            }




class ResPartnerSalesperson(models.Model):
    _name = 'parter.sales.person'
    _description = "Partner Sales Person"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
    product_categ_id = fields.Many2one('product.category', string="Category", track_visibility='onchange')
    user_id = fields.Many2one('res.users', string="SalePerson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (partner_id, product_categ_id, user_id, company_id)',
                         'Reason must be unique within an application!')]


class CreditApproval(models.Model):
    _name = 'partner.credit.approval'
    _description = "Partner Credit Approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.model
    def _get_credit_term(self):
        if self.partner_id and self.partnere_id.property_payment_term_id:
            return self.partnere_id.property_payment_term_id.id

    @api.model
    def _get_credit_limit(self):
        if self.partner_id and self.partnere_id.credit_limit:
            return self.partnere_id.credit_limit

    name = fields.Char(string='Req. No', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'), track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
    old_credit_term_id = fields.Many2one('account.payment.term', string="Old credit Term", default=_get_credit_term,
                                         readonly=True, track_visibility='onchange')
    new_credit_term_id = fields.Many2one('account.payment.term', string="New credit Term", track_visibility='onchange')
    old_credit_limit = fields.Float(string="Old Limit", readonly=True, track_visibility='onchange',
                                    default=_get_credit_limit)
    new_credit_limit = fields.Float(string="New Limit", track_visibility='onchange')
    requested_by_id = fields.Many2one('res.users', string="Requested By", track_visibility='onchange')
    approved_by_id = fields.Many2one('res.users', string="Action By", track_visibility='onchange')
    remark = fields.Text(string="Remark", track_visibility='onchange')
    #kashif 3oct23: added reveiwed state
    status = fields.Selection(
        [('draft', 'Draft'),('reviewed', 'Reviewed'), ('approved', 'Approved'), ('reject', 'Reject'), ('cancel', 'Cancel')], string="State",
        default='draft', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True}, track_visibility='onchange')
    sequence = fields.Integer(default=10, track_visibility='onchange')
    current_is_overdue_block = fields.Boolean("Current Status for Overdue Block", track_visibility='onchange')
    unblock_is_overdue_block = fields.Boolean("Overdue UnBlock", track_visibility='onchange')
    order_id = fields.Many2one('sale.order', string="Quotation/Order")

    #kashif 3oct23: added code to have reveiwed state
    def action_reveiwed(self):
        self.write({'status': 'reviewed'})

    @api.one
    def _set_access_for_approve_reject(self):
        current_user_id = self.env.uid
        # print('>>>>>>>>>>>>>>> current_user_id =', current_user_id, ' VS Approvers=',
        #      self.company_id.cr_limit_app_user_ids)
        if self.company_id.cr_limit_app_user_ids:
            for approver_user_id in self.company_id.cr_limit_app_user_ids:
                # print('>>>>>>>>>>>>>>> current_user_id =', current_user_id, ' VS Approvers=',
                #      approver_user_id)
                if current_user_id == approver_user_id.id:
                    self.approve_reject_credit_limit = True
                    break
                else:
                    self.approve_reject_credit_limit = False
        else:
            self.approve_reject_credit_limit = False
        # print('>>>>>>>>>>>>> self.approve_reject_credit_limit=', self.approve_reject_credit_limit)

    approve_reject_credit_limit = fields.Boolean(compute="_set_access_for_approve_reject",
                                                 string='Is user able to approve/reject credit limit?', copy=False)

    @api.multi
    def action_approve_request(self):
        flag = False
        # for res in self.company_id.cr_limit_app_user_ids:
        #     if res.id == self.env.uid:
        #         flag = True
        for rec in self:
            if rec.partner_id:
                data = {}
                msg = ""
                if rec.new_credit_term_id:
                    data.update({'property_payment_term_id': self.new_credit_term_id.id})
                    # rec.partner_id.property_payment_term_id = self.new_credit_term_id.id
                    msg += "New Credit Term Updated"
                if rec.current_is_overdue_block:
                    if not self.unblock_is_overdue_block:
                        raise UserError(_("Please tick 'Overdue UnBlock'"))
                if rec.new_credit_limit:
                    data.update({'credit_limit': self.new_credit_limit})
                    # rec.partner_id.credit_limit = self.new_credit_limit
                    msg += "   \nNew Credit Limit Updated"
                if rec.unblock_is_overdue_block:
                    data.update({'is_overdue_block': False})
                    msg += "   \nOverDue Block now Unblocked"
                data.update({'is_overdue_block': False})
                # rec.partner_id.is_overdue_block = False
                rec.partner_id.write(data)
                user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
                rec.approved_by_id = self.env.uid
                # self.partner_id.message_post(body=_('%s  Request Approved by %s.') % (msg, user_id.name))
                rec.write({'status': 'approved'})
                if rec.order_id:
                    rec.order_id.write({
                        'state': 'approved',
                        'req_credit_limit_approved': True,
                    })
                    rec.order_id.message_post(body=_('%s  Request Approved by %s.') % (msg, user_id.name))
                rec.send_approved_mail()
                # TODO auto approve
                # rec.order_id.action_confirm()
                rec.order_id.action_to_approved()

            else:
                raise UserError(_("You can not Approve Credit Limit Request"))

    @api.multi
    def action_reject(self):
        flag = False
        for res in self.company_id.cr_limit_app_user_ids:
            if res.id == self.env.uid:
                flag = True
        msg = ""
        if flag:
            if self.new_credit_term_id:
                msg += "New Credit Term not Approved"
            if self.new_credit_limit:
                msg += "New Credit Limit not Approved"
            if not self.unblock_is_overdue_block and self.current_is_overdue_block:
                msg += "Overdue UnBlock not Approved"
            user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
            self.approved_by_id = self.env.uid
            self.partner_id.message_post(body=_('%s Request Rejected by %s.') % (msg, user_id.name))
            self.write({'status': 'reject'})
            if self.order_id:
                self.order_id.write({
                    'state': 'draft',
                })
                self.order_id.message_post(body=_('%s  Request Rejected by %s.') % (msg, user_id.name))
            self.send_reject_mail()
        else:
            raise UserError(_("You can not Reject Credit Limit Request"))

    @api.multi
    def action_cancel(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
        self.approved_by_id = self.env.uid
        self.partner_id.message_post(body=_('Credit Request Cancel by %s.') % (user_id.name))
        self.write({'status': 'cancel'})
        # self.send_cancel_mail()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('partner.credit.approval') or 'New'
        res = super(CreditApproval, self).create(vals)
        res.send_approval_mail()
        return res

    @api.multi
    def send_approval_mail(self):
        # data_ids = self.env['technical.customer.plan'].search([('schedule_reminder', '=', DT.date.today())])
        template = self.env.ref('goexcel_sale.email_credit_limit_approval')
        assert template._name == 'mail.template'
        email_lst = []
        email_lst += [user.email for user in filter(lambda x: x.email, self.company_id.cr_limit_app_user_ids)]
        email_to = ','.join(map(str, email_lst))
        if template and email_lst:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def send_reject_mail(self):
        # data_ids = self.env['technical.customer.plan'].search([('schedule_reminder', '=', DT.date.today())])
        template = self.env.ref('goexcel_sale.email_credit_limit_reject')
        assert template._name == 'mail.template'
        email_to = self.requested_by_id.email
        template.write({'email_to': email_to})
        template.send_mail(self.id, force_send=True)

    @api.multi
    def send_approved_mail(self):
        # data_ids = self.env['technical.customer.plan'].search([('schedule_reminder', '=', DT.date.today())])
        template = self.env.ref('goexcel_sale.email_credit_limit_approved')
        assert template._name == 'mail.template'
        email_to = self.requested_by_id.email
        template.write({'email_to': email_to})
        template.send_mail(self.id, force_send=True)

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        # if self.env.context.get('mark_so_as_sent'):
        #     self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
        #     self.env.user.company_id.set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        # return super(CreditApproval, self.partner_id.with_context(mail_post_autofollow=True)).message_post(**kwargs)
        return super(CreditApproval, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


class ResPartnerInactiveConfig(models.Model):
    _name = 'res.partner.inactive.config'
    _description = 'Customer Inactive Configuration'
    _rec_name = 'partner_status'

    _sql_constraints = [('partner_status_uniq', 'unique (partner_status, company_id)',
                         'Can not create more than one record for this status\n'
                         'Please update the already created record of this status')]

    partner_status = fields.Selection([
        ('active', 'Active'),
        ('lost_customer', 'Lost Customer'),
        ('lost_lead', 'Lost Lead'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive')
    ], string="Status", copy=False, required=True)
    last_invoice_gap_days = fields.Integer(strng='last invoice gap days')
    company_id = fields.Many2one('res.company', string='Company', index=True, readonly=True,
                                 default=lambda self: self.env.user.company_id.id)
