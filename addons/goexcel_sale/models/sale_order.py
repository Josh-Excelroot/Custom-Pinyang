from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import datetime as DT
import odoo.addons.decimal_precision as dp
import re
from odoo.tools import float_round
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        partner_invoice = []
        partner_shipping = []
        partner_related_company = []
        domain = {}
        for record in self:
            if record.partner_id:
                record.partner_invoice_id = record.partner_id.id
                record.partner_shipping_id = record.partner_id.id
                if record.partner_id.child_ids:
                    for partner in record.partner_id.child_ids:
                        if partner.type == 'invoice':
                            partner_invoice.append(partner.id)
                        elif partner.type == 'delivery':
                            partner_shipping.append(partner.id)
                        elif partner.type == 'related_company':
                            partner_related_company.append(partner.id)
                if partner_invoice:
                    domain['partner_invoice_id'] = [('id', 'in', partner_invoice)]
                else:
                    partner_invoice.append(record.partner_id.id)
                    domain['partner_invoice_id'] = [('id', 'in', partner_invoice)]
                if partner_shipping:
                    domain['partner_shipping_id'] = [('id', 'in', partner_shipping)]
                else:
                    partner_shipping.append(record.partner_id.id)
                    domain['partner_shipping_id'] = [('id', 'in', partner_shipping)]
                if partner_related_company:
                    domain['related_company_ids'] = [('id', 'in', partner_related_company)]
            else:
                domain['partner_invoice_id'] = [('type', '=', 'invoice')]
                domain['partner_shipping_id'] = [('type', '=', 'delivery')]
                domain['related_company_ids'] = [('type', '=', 'related_company')]
        return {'domain': domain}

    @api.onchange('partner_id', 'user_id')
    def check_overdue_invoice(self):
        if self.order_type == 'cash_order':
            return {}
        # date_due
        # print('>>>>>>>check_overdue_invoice BEFORE search invoice OPEN')
        invoice_ids = self.env['account.invoice'].sudo().search(
            [('partner_id', '=', self.partner_id.id), ('type', '=', 'out_invoice'), ('state', '=', 'open')])
        partner_ids = self.env['res.partner'].sudo().search(
            [('parent_id', '=', self.partner_id.id), ('type', '=', 'related_company')])
        # print('>>>>>>>check_overdue_invoice AFTER search invoice OPEN')
        # self.related_company_ids = [(6, 0, partner_ids and partner_ids.ids or [])]
        if len(invoice_ids) > 0:
            msg = "for %s due Invoice Detail\n" % self.partner_id.name
            msg += "\nNumber  >>  Due Amount >> Due Date >> Sales Person\n"
            for res in invoice_ids:
                msg += "%s >> %s >> %s >> %s\n" % (res.number, res.residual, res.date_due, res.user_id.name)
            res = {'title': _('Due Invoice of this Customer'), 'message': msg}
            return {'warning': res}

    @api.depends('req_discount_approval', 'req_credit_limit_approval', 'payment_term_approval', 'amount_total',
                 'user_id', 'payment_term_id', 'pricelist_id', 'state',
                 'company_id.max_discount_approver_ids', 'company_id.sq_credit_limit_approver_ids',
                 'company_id.payment_term_approver_ids')
    def _set_access_for_approve_reject(self):
        current_user_id = self.env.uid
        for res in self:
            if current_user_id in res.company_id.max_discount_approver_ids.ids and res.req_discount_approval:
                res.approve_reject_sq = True
            elif current_user_id in res.company_id.sq_credit_limit_approver_ids.ids:
                res.approve_reject_sq = True
            elif current_user_id in res.company_id.payment_term_approver_ids.ids:
                res.approve_reject_sq = True
            else:
                res.approve_reject_sq = False

    # kashif 22 may23 - check discount request and payment request and return the reason
    def get_discount_request_reason(self):
        for res in self:
            if res.order_type != 'cash_order':
                dic_per = 0.00
                for rec in res.order_line:
                    if rec.discount_fixed > 0 and rec.price_unit > 0:
                        dic_per = (rec.discount_fixed * 100) / rec.price_unit
                    if rec.discount:
                        dic_per = rec.discount
                    if dic_per > rec.product_id.max_discount:
                        return "Discount Requested: " + str(dic_per) + ' is higher than ' + str(
                            rec.product_id.max_discount) + '\n'
            return False

    def get_payment_term_reason(self):
        for res in self:
            if res.order_type != 'cash_order':
                if res.payment_term_id.id != res.partner_id.property_payment_term_id.id:
                    return "Payment Term Changed To: " + res.payment_term_id.name + " " '\n'
            return False

    @api.constrains('order_line', 'order_line.discount_fixed', 'order_line.discount')
    def check_partner_discount_constrains(self):
        for res in self:
            if res.state in ['draft', 'approve'] and res.order_type != 'cash_order':
                dic_per = 0.00
                for rec in res.order_line:
                    if rec.discount_fixed > 0 and rec.price_unit > 0:
                        dic_per = (rec.discount_fixed * 100) / rec.price_unit
                    if rec.discount:
                        dic_per = rec.discount
                    if dic_per > rec.product_id.max_discount:
                        # res.req_discount_approval = True
                        # kashif 29may23 - bug fix .. approval reason not updating. have to use api constrains method

                        if not str(res.approval_reasons).__contains__('Discount Requested'):
                            if res.approval_reasons:
                                # res.write({'approval_reasons': ""})
                                res.write({'approval_reasons': res.approval_reasons + "Discount Requested: " + str(
                                    dic_per) + ' is higher than ' + str(rec.product_id.max_discount) + '\n'})
                            else:

                                res.write({'approval_reasons': "Discount Requested: " + str(
                                    dic_per) + ' is higher than ' + str(rec.product_id.max_discount) + '\n'})

    # end
    # @api.depends('order_line.discount_fixed','order_line.discount')
    def check_partner_discount(self):
        for res in self:
            if res.state in ['draft', 'approve'] and res.order_type != 'cash_order':
                dic_per = 0.00
                for rec in res.order_line:
                    if rec.discount_fixed > 0 and rec.price_unit > 0:
                        dic_per = (rec.discount_fixed * 100) / rec.price_unit
                    if rec.discount:
                        dic_per = rec.discount
                    if dic_per > rec.product_id.max_discount:
                        pass
                        # res.req_discount_approval = True
                        # kashif 22may23 - bug fix .. approval reason not updating in compute function. have to use write method

                        # if not str(res.approval_reasons).__contains__('Discount Requested'):
                        #     if res.approval_reasons:
                        #         # res.write({'approval_reasons': ""})
                        #         res.write({'approval_reasons': res.approval_reasons + "Discount Requested: " + str(
                        #             dic_per) + ' is higher than ' + str(rec.product_id.max_discount) + '\n'})
                        #     else:
                        #
                        #         res.write({'approval_reasons': "Discount Requested: " + str(
                        #             dic_per) + ' is higher than ' + str(rec.product_id.max_discount) + '\n'})
                        # end
                        #
                        # if res.approval_reasons:
                        #     res.approval_reasons = res.approval_reasons + \
                        #                            "Discount Requested: ", str(dic_per) + ' is higher than ', str(
                        #         rec.product_id.max_discount) + '\n'
                        # else:
                        #     res.approval_reasons = "Discount Requested: ", str(dic_per) + ' is higher than ', str(
                        #         rec.product_id.max_discount) + '\n'

                        # print('>>>>>>>>>>>>>>>>>> check_partner_discount=', res.approval_reasons)

    contact_person_id = fields.Many2one('res.partner', string='Contact Peson', copy=False)
    approve_reject_sq = fields.Boolean(compute="_set_access_for_approve_reject",
                                       string='Is user able to approve/reject sq?', copy=False)

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('approve', 'To Approve'),
        ('approved', 'Approved'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('lost', 'Lost'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange',
        default='draft')
    approved_by_id = fields.Many2one('res.users', string="Approved By", readonly=True, track_visibility='onchange',
                                     copy=False)
    rejected_by_id = fields.Many2one('res.users', string="Reject By", readonly=True, track_visibility='onchange',
                                     copy=False)
    sale_lost_reason_id = fields.Many2one('crm.lost.reason', string="Lost Reason", track_visibility='onchange',
                                          copy=False)
    sale_won_reason_id = fields.Many2one('crm.won.reason', string='Won Reason', index=True, track_visibility='onchange',
                                         copy=False)
    sale_extend_reason_id = fields.Many2one('sale.extend.reason', string="Extend Reason", track_visibility='onchange',
                                            copy=False)
    sale_extend_remark = fields.Text(string="Extend Remark", copy=False)
    sq_sent_date = fields.Date(string="SQ Sent Date", track_visibility='onchange', copy=False)
    related_company_ids = fields.Many2many('res.partner', string="Related Companies", copy=False)
    manage_review = fields.Text(string="Manager Review", copy=False)
    manager_review = fields.Boolean(string="Review?", copy=False)
    is_first_order = fields.Boolean(string="First Order", copy=False)
    first_order_date = fields.Date(string="First Order Date", copy=False)
    technical_plan_id = fields.Many2one('technical.plan', string="Technical Plan", copy=False)
    req_discount_approval = fields.Boolean(string="Req. Discount Approval", compute="check_partner_discount",
                                           copy=False)
    req_credit_limit_approval = fields.Boolean("Req. Credit Limit Approval", default=False, copy=False)
    req_credit_limit_approved = fields.Boolean("Req. Credit Limit Approved", default=False, copy=False)

    signature_type = fields.Selection(
        [('no_signature', 'No Signature'), ('digital_signate', 'Digital Signature'), ('manual', 'Manual Signature')],
        default="no_signature", sting="Signature Type")
    print_signature = fields.Boolean(string="Print Signature", default=True, copy=False)
    signature_id = fields.Many2one("user.signature", compute="get_signature", copy=False)
    po_no = fields.Char(string="P.O. No.")
    order_type = fields.Selection([('sale_order', 'Sale Order')], string="Order type",
                                  default='sale_order',
                                  track_visibility='onchange')
    make_auto_delivery = fields.Boolean(string="Auto Delivey", default=True)
    cash_order_payment_method_id = fields.Many2one('account.journal', string="Payment Journal",
                                                   domain="[('type', 'in', ['bank', 'cash'])]")
    cash_contact_name = fields.Char(string="Contact Name")
    cash_address = fields.Text(string="Delivery Address")
    payment_term_approval = fields.Boolean(string="Req. Payment Term Approval")
    delivery_note = fields.Text(related='partner_id.delivery_note', track_visibility='onchange', store=True)
    approval_reasons = fields.Text(string="Approval Reasons", track_visibility='onchange')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
                                      track_visibility='onchange')
    is_payment_term_change = fields.Boolean(string="Is Payment Term change")
    fork_lift = fields.Boolean(related='partner_shipping_id.fork_lift', string='Fork Lift')

    def get_credit_list(self):
        for res in self:
            credit_id = self.env['partner.credit.approval'].sudo().search(
                [('order_id', '=', res.id), ('company_id', '=', res.company_id.id)], limit=1)
            res.credit_count = len(credit_id)

    credit_count = fields.Integer(string="Credit", compute="get_credit_list")

    @api.multi
    def action_view_credit_request(self):
        for res in self:
            credit_id = self.env['partner.credit.approval'].sudo().search(
                [('order_id', '=', res.id), ('company_id', '=', res.company_id.id)], limit=1)

        return {
            "type": "ir.actions.act_window",
            "res_model": "partner.credit.approval",
            "views": [[False, "form"]],
            "res_id": credit_id.id,
            "context": {"create": False},
        }

    @api.onchange('order_type')
    def onchange_cash_Sale(self):
        if self.order_type == "cash_order":
            self.make_auto_delivery = True

    @api.depends('user_id', 'state', 'print_signature', 'signature_type')
    def get_signature(self):
        for res in self:
            if res.signature_type == 'digital_signate' and res.print_signature:
                sign_id = self.env['user.signature'].sudo().search(
                    [('company_id', '=', res.company_id.id), ('user_id', '=', res.user_id.id)], limit=1)
                res.signature_id = sign_id and sign_id.id or False

    @api.multi
    def action_sale_lost(self):
        if self.order_type == 'cash_order':
            return True
        wiz_id = self.env['sale.lost.reason.wiz'].create({'sale_order_id': self.id})
        return {
            'name': _('Select Lost Reason'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.lost.reason.wiz',
            'views': [(self.env.ref('goexcel_sale.sale_lost_wiz_view_form').id, 'form')],
            'view_id': self.env.ref('goexcel_sale.sale_lost_wiz_view_form').id,
            'target': 'new',
            'res_id': wiz_id.id,

        }

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_quotation_sent(self):
        for res in self:
            res.state = 'sent'

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state in ['draft', 'approved']).write({'state': 'sent'})
        return self.env.ref('sale.action_report_saleorder').with_context(discard_logo_check=True).report_action(self)

    @api.model
    def create(self, vals):
        if 'order_type' in vals and vals['order_type'] == 'cash_order':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'cash.sale') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('cash.sale') or _('New')
        res = super(SaleOrder, self).create(vals)
        # res.check_blocked_partner()
        return res

    def check_blocked_partner(self):
        # for res in self:
        return
        # TODO
        # if self.partner_id.is_overdue_block and self.order_type != 'cash_order':
        #     #wiz_id = self.env['unblock.credit.request.wiz'].create({'sale_order_id': self.id})
        #     #print('>>>>>>>>>>>>>>>> check_blocked_partner')
        #     return {
        #         'name': _('Create UnBlock Request'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'unblock.credit.request.wiz',
        #         'views': [(self.env.ref('goexcel_sale.partner_unblock_form_view').id, 'form')],
        #         'view_id': self.env.ref('goexcel_sale.partner_unblock_form_view').id,
        #         'target': 'new',
        #         #'res_id': wiz_id.id,
        #         'context': dict(so_id=self.id),
        #     }

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update(
            {'po_no': self.po_no, 'all_do': ",".join([pic.name for pic in self.picking_ids if pic.state != 'cancel'])})
        return res

    @api.multi
    def write(self, values):
        if 'validity_date' in values and self.state in ['sale', 'sent', 'approved']:
            if 'sale_extend_reason_id' not in values:
                raise UserError(_("Please Select extend reason"))
        if 'state' in values:
            if values['state'] == 'sent':
                values['sq_sent_date'] = fields.Date.today()
        if 'payment_term_id' in values or 'pricelist_id' in values:
            # kashif 29may23: commented status approve . when payment term change
            # values['state'] = 'approve'
            # end
            values['payment_term_approval'] = True
            old_payment_term = ''
            if self.payment_term_id:
                old_payment_term = self.payment_term_id.name
            payment_term_name = ''
            # if values.get('payment_term_id'):

        old_pricelist = self.pricelist_id.name

        # check first order
        # old_id = self.get_first_order_date()
        # if old_id:
        #     values['is_first_order'] = True
        #     values['first_order_date'] = old_id.confirmation_date
        # else:
        #     values['is_first_order'] = False
        #     values['first_order_date'] = False
        res = super(SaleOrder, self).write(values)
        if self.state in ['approved', 'sent', 'sale', 'lock'] and 'order_line' in values:
            if not self.user_has_groups('sales_team.group_sale_manager'):
                raise UserError(_("You can not change Product related detail after Approved"))
        # set first order id in Partner
        if self.is_first_order:
            self.partner_id.first_sale_order_id = self.id
        new_payment_term = self.payment_term_id.name
        new_pricelist = self.pricelist_id.name
        if 'payment_term_id' in values:
            values['is_payment_term_change'] = True
            payment_term = self.env['account.payment.term'].sudo().browse(values.get('payment_term_id'))
            if payment_term:
                payment_term_name = payment_term.name
            is_valid_term = self.get_payment_term_reason()
            if is_valid_term:
                if not self.sudo().approval_reasons:
                    # print('>>>>>>>>>>>> Payment Term 1 change=')
                    self.sudo().approval_reasons = "Payment Changed: " + old_payment_term + ' to ' + payment_term_name + '\n'
                else:
                    # print('>>>>>>>>>>>> Payment Term 2 change=')
                    self.sudo().approval_reasons = self.sudo().approval_reasons + "Payment Changed: " + old_payment_term + ' to ' + payment_term_name + '\n'
            self.message_post(body=_(
                'Payment term <a href=# data-oe-model=sale.order data-oe-id=%d>%s to %s</a> has been Changed.') % (
                                       self.id, old_payment_term, new_payment_term))
        if 'pricelist_id' in values:
            self.message_post(
                body=_('Pricelist <a href=# data-oe-model=sale.order data-oe-id=%d>%s to %s</a> has been Changed.') % (
                    self.id, old_pricelist, new_pricelist))

        if 'req_discount_approval' in values and self.req_discount_approval:
            msg = "Approval for Discount Limit"
            self.message_post(body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (self.id, msg))
            if not self.sudo().approval_reasons:
                values['approval_reasons'] = "Discount Limit Approval." + '\n'
            else:
                self.sudo().approval_reasons = self.sudo().approval_reasons + "Discount Limit Approval." + '\n'
        # if 'payment_term_id' in values or 'pricelist_id' in values:
        #    self.send_approval_payment_term_pricelist_mail()

        # send for discount approval mail
        # self.send_approval_max_discount_mail()
        if self.state == 'sale':
            self.set_order_place()
        return res

    def get_first_order_date(self):
        for res in self:
            sale_id = self.env['sale.order'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('state', 'in', ['sale', 'done'])])
            if len(sale_id) == 1:
                if sale_id.opportunity_id:
                    sale_id.opportunity_id.is_first_order = True
                    sale_id.opportunity_id.first_order_id = sale_id.id
                return sale_id
            else:
                return False

    def set_order_place(self):
        for res in self:
            # find gift
            gift_id = self.env['gift.line'].sudo().search(
                [('partner_id', '=', res.partner_id.id), ('sale_order_id', '=', False)], limit=1)
            if gift_id:
                gift_id.sale_order_id = res.id
            # set technical Plan sale order
            plan_id = self.env['technical.customer.plan'].sudo().search(
                [('partner_id', '=', res.partner_id.id), ('sale_order_id', '=', False)], limit=1)
            if plan_id:
                plan_id.sale_order_id = res.id

    @api.multi
    def action_to_approve(self):
        self.write({'state': 'approve'})

    @api.multi
    def action_to_approved(self):
        current_user_id = self.env.uid
        username = self.env['res.users'].sudo().search([('id', '=', current_user_id)], limit=1).name
        for res in self:
            # for all in one
            flag = False
            if current_user_id in res.company_id.max_discount_approver_ids.ids:
                flag = True
            if current_user_id in res.company_id.sq_credit_limit_approver_ids.ids:
                flag = True
            if current_user_id in res.company_id.payment_term_approver_ids.ids:
                flag = True
            update_data = {'state': 'approved', 'approved_by_id': self.env.uid}
            if flag and res.order_type != 'cash_order':
                # if  and flag and res.req_discount_approval or res.req_credit_limit_approval or res.payment_term_approval:
                if res.req_discount_approval:
                    res.send_approved_max_discount_mail()
                    msg = "Approved Discount Limit by %s " % username
                    res.message_post(
                        body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
                    update_data.update({'req_discount_approval': False})
                if res.req_credit_limit_approval:
                    msg = "Approved Order credit Limit by %s " % username
                    res.message_post(
                        body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
                    # send credit limit approved mail
                    res.send_approved_credit_limit_mail()
                    update_data.update({'req_credit_limit_approval': False, 'req_credit_limit_approved': True})
                if res.payment_term_approval:
                    msg = "Approved Payment term/pricelist by %s " % username
                    res.message_post(
                        body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
                    # send payment term approved mail
                    res.send_approved_payment_term_pricelist_mail()
                    update_data.update({'payment_term_approval': False})
                update_data.update({'req_credit_limit_approved': True})
            res.write(update_data)
            # for check one by one condition
            # if res.req_discount_approval and res.order_type != 'cash_order':
            #     if current_user_id in res.company_id.max_discount_approver_ids.ids:
            #         res.write({'state': 'approved', 'req_discount_approval': False, 'approved_by_id': self.env.uid})
            #         msg = "Approved Discount Limit by %s " % username
            #         res.message_post(body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
            #         # send discount approved mail
            #         res.send_approved_max_discount_mail()
            #     else:
            #         raise UserError(_("You can not Approve Max Discount Sale Quotation."))
            # if res.req_credit_limit_approval and res.order_type != 'cash_order':
            #     if current_user_id in res.company_id.sq_credit_limit_approver_ids.ids:
            #         res.write({'state': 'approved', 'req_credit_limit_approval': False, 'req_credit_limit_approved': True, 'approved_by_id': self.env.uid})
            #         msg = "Approved Order credit Limit by %s " % username
            #         res.message_post(body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
            #         # send credit limit approved mail
            #         res.send_approved_credit_limit_mail()
            #     else:
            #         raise UserError(_("You can not Approve for Customer Credit Limit."))
            # if res.payment_term_approval and res.order_type != 'cash_order':
            #     if current_user_id in res.company_id.payment_term_approver_ids.ids:
            #         res.write({'state': 'approved', 'payment_term_approval': False, 'approved_by_id': self.env.uid})
            #         msg = "Approved Payment term/pricelist by %s " % username
            #         res.message_post(body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (res.id, msg))
            #         # send payment term approved mail
            #         res.send_approved_payment_term_pricelist_mail()
            #     else:
            #         raise UserError(_("You can not Approve for Payment Term/Price list"))

            # res.write()

    @api.multi
    def action_reject(self):
        for res in self:
            # print('>>>>>>>>>>>> action_reject')
            res.write({'state': 'draft', 'rejected_by_id': self.env.uid})
            # send rejected mail for both as per req
            flag = True
            if res.req_credit_limit_approval and not res.req_credit_limit_approved:
                # print('>>>>>>>>>>>> action_reject send_reject_credit_limit_mail')
                flag = False
                res.send_reject_credit_limit_mail()
            elif flag and res.req_discount_approval:
                flag = False
                # print('>>>>>>>>>>>> action_reject send_reject_max_discount_mail')
                res.send_reject_max_discount_mail()
            elif flag and res.payment_term_approval:
                # print('>>>>>>>>>>>> action_reject send_reject_payment_term_pricelist_mail')
                res.send_reject_payment_term_pricelist_mail()

    @api.multi
    def check_partner_credit(self):
        msg = ""

        # print('>>>>>>>>check partner_credit AFTER search')

        # print('>>>>>>>>check partner_credit AFTER search')
        # kashif 6may23 - changes the below code to avoid partial invoice to record the amount
        confirm_so = [('invoice_status', 'not in', ['invoiced']), ('partner_id', '=', self.partner_id.id),
                      ('state', 'in', ['sale', 'done'])]
        sale_order = self.env['sale.order'].sudo().search(confirm_so)
        invoice_partail_paid = False
        if sale_order:
            invoice_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                              ('partner_id', '=', self.partner_id.id), ('origin', 'not in', sale_order.mapped('name')),
                              ('state', 'in', ['open', 'draft', 'approve', 'in payment'])]
            invoice_paid_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                           ('partner_id', '=', self.partner_id.id),
                                           ('origin', 'in', sale_order.mapped('name')),
                                           ('state', 'in', ['paid'])]

            invoice_partail_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                           ('partner_id', '=', self.partner_id.id),
                                           ('origin', 'in', sale_order.mapped('name')),
                                           ('state', 'in', ['open'])]

            invoice_partail = self.env['account.invoice'].sudo().search(invoice_partail_domain)
            invoice_paid = self.env['account.invoice'].sudo().search(invoice_paid_domain)

            invoice_partail_paid = sum([inv.amount_total for inv in invoice_paid]) + sum([(inv.amount_total - inv.residual) if inv.residual!=inv.amount_total else 0 for inv in invoice_partail])
        else:
            invoice_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                              ('partner_id', '=', self.partner_id.id),
                              ('state', 'in', ['open', 'draft', 'approve', 'in payment'])]

        # invoice_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
        #                   ('partner_id', '=', self.partner_id.id),
        #                   ('state', 'in', ['open', 'draft', 'approve', 'in payment'])]
        # print('>>>>>>>>check partner_credit BEFORE search')
        open_due_invoices = self.env['account.invoice'].sudo().search(invoice_domain)
        confirm_so = [('invoice_status', 'not in', ['invoiced']), ('partner_id', '=', self.partner_id.id),
                      ('state', 'in', ['sale', 'done'])]
        sale_order = self.env['sale.order'].sudo().search(confirm_so)
        invoice_amount = sum([inv.residual for inv in open_due_invoices])
        sale_amount = sum([sale.amount_total for sale in sale_order])
        if invoice_partail_paid:
            sale_amount = (sale_amount - invoice_partail_paid)
        sale_amount = sale_amount + self.amount_total
        # print('>>>>>>>>>>>>>>>  check_partner_credit Inv Amount=', invoice_amount, ' , sale amount=', sale_amount)
        if not self.sudo().partner_id.over_credit or self.sudo().partner_id.credit_limit > 0 and self.sudo().order_type != 'cash_order':
            # credit_limit = float_round(self.sudo().partner_id.credit_limit, 2, rounding_method='HALF-UP')
            credit_limit = self.partner_id.credit_limit
            old_credit = float_round((invoice_amount + sale_amount), 2, rounding_method='HALF-UP')
            # print('>>>>>>>>>>>>>>>check partner_credit old credit=', old_credit, ' , credit limit=', credit_limit)
            if old_credit > credit_limit:
                msg = "Approval over for Credit Limit"
                self.sudo().message_post(
                    body=_('<a href=# data-oe-model=sale.order data-oe-id=%d></a> %s.') % (self.id, msg))
                self.sudo().write({'req_credit_limit_approval': True})
                if not self.sudo().approval_reasons:
                    if old_credit > credit_limit:
                        self.sudo().approval_reasons = "Credit Limit Approval - " + \
                                                       str(old_credit) + ' is more than ' + str(credit_limit) + '\n'
                    else:
                        self.sudo().approval_reasons = "Credit Limit Approval - " + \
                                                       str(old_credit) + ' is less than ' + str(credit_limit) + '\n'
                elif 'Credit Limit Approval' not in self.sudo().approval_reasons:
                    if old_credit > credit_limit:
                        self.sudo().approval_reasons = self.sudo().approval_reasons + "Credit Limit Approval - " + \
                                                       str(old_credit) + ' is more than ' + str(credit_limit) + '\n'
                    else:
                        self.sudo().approval_reasons = "Credit Limit Approval - " + \
                                                       str(old_credit) + ' is less than ' + str(credit_limit) + '\n'
            # send for credit limit approval mail
            # self.send_approval_credit_limit_mail()
            else:
                # kashif 11 july23 : removed bug logic state change to (to approve) when click on cancel
                self.sudo().write(
                    {'req_credit_limit_approval': False, 'req_credit_limit_approved': True})
                # print('>>>>>>>>>>>>>>>check partner_credit after check limit 1')
                # return False
                # return True
            # print('>>>>>>>>>>>>>>>check partner_credit after check limit 2')
        else:
            self.sudo().write(
                {'req_credit_limit_approval': False, 'req_credit_limit_approved': True})
        # end
        # print('>>>>>>>>>>>>>>>check partner_credit after check limit 3')
        # return True

    @api.multi
    def _run_sq_reminder(self):
        if self.env.user.company_id.use_sq_remider_days and self.env.user.company_id.sq_remider_days >= 0:
            template = self.env.ref('goexcel_sale.email_sq_state_reminder')
            assert template._name == 'mail.template'
            today = DT.date.today()
            last_day = today - DT.timedelta(days=self.company_id.use_sq_remider_days)
            all_so_ids = self.env['sale.order'].sudo().search(
                [('state', '=', 'sent'), ('sq_sent_date', '<=', last_day)])
            for so in all_so_ids:
                if so.user_id:
                    template_values = {
                        'email_to': '${object.user_id.partner_id.email|safe}',
                        'email_cc': False,
                        'auto_delete': True,
                        'partner_to': '${object.user_id.partner_id.id|safe}',
                        'scheduled_date': False,
                    }
                    template.sudo().write(template_values)
                    with self.env.cr.savepoint():
                        template.with_context(lang=so.user_id.partner_id.lang).sudo().send_mail(so.id, force_send=True,
                                                                                                raise_exception=True)

    @api.multi
    def action_confirm(self):
        # kashif 22may23 - if partner is prospect.. cannot allow to confirm sale order
        if self.partner_id.is_prospect:
            raise ValidationError(_("Cannot confirm for the prospect customer."))
        # end
        if self.order_type == 'cash_order':
            super(SaleOrder, self).action_confirm()
            # self._action_confirm()
            # self.action_done()
            imediate_obj = self.env['stock.immediate.transfer']

            if self.make_auto_delivery and self.picking_ids:
                for picking in self.picking_ids:
                    picking.action_confirm()
                    picking.action_assign()
                    imediate_rec = imediate_obj.create({'pick_ids': [(4, self.picking_ids.id)]})
                    imediate_rec.process()
                    if picking.state != 'done':
                        for move in picking.move_ids_without_package:
                            move.quantity_done = move.product_uom_qty
                        picking.button_validate()
                self._cr.commit()
            if not self.invoice_ids:
                self.action_invoice_create()
                for invoice in self.invoice_ids:
                    invoice.action_invoice_open()
                    if self.cash_order_payment_method_id:
                        payment = self.env['account.payment'].create(
                            {'payment_type': 'inbound',
                             'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                             'partner_type': 'customer',
                             'partner_id': invoice.partner_id.id,
                             'amount': invoice.residual,
                             'currency_id': invoice.currency_id.id,
                             'payment_date': invoice.date_invoice,
                             'journal_id': self.cash_order_payment_method_id.id,
                             'invoice_ids': [(6, 0, [invoice.id])]
                             })
                        if payment:
                            payment.post()
            return

        # self.find_over_due_invoice()
        if self.order_type != 'cash_order':
            self.sudo().approval_reasons = ''
            # print('>>>>>>>>>>>>>>>  action_confirm=', self.sudo().approval_reasons)
            aging = 0
            next_date = datetime.today().date()
            # print('>>>>>>>action_confirm BEFORE search invoice OVERDUE')
            overdue_invoices = self.env['account.invoice'].sudo().search(
                [('type', '=', 'out_invoice'), ('state', '=', 'open'),
                 ('date_due', '<=', next_date), ('partner_id', '=', self.partner_id.id),
                 ('company_id', '=', self.company_id.id)])
            # print('>>>>>>>action_confirm AFTER  search invoice OVERDUE=', self.partner_id.sudo().is_overdue_block
            #       , ' approval_reason=', self.sudo().approval_reasons)
            if overdue_invoices:
                for inv in overdue_invoices:
                    if not inv.partner_id.sudo().is_overdue_block:
                        inv.partner_id.sudo().is_overdue_block = True
                        break
            else:
                self.partner_id.sudo().is_overdue_block = False
            # print('>>>>>>>action_confirm AFTER search invoice OVERDUE 2=', self.partner_id.sudo().is_overdue_block)
            if self.partner_id.is_overdue_block:
                overdue_amount = sum([inv.residual for inv in overdue_invoices])

                # print('>>>>>>>action_confirm AFTER search invoice OPEN DUE')
                confirm_so = [('invoice_status', 'not in', ['invoiced']), ('partner_id', '=', self.partner_id.id),
                              ('state', 'in', ['sale', 'done'])]

                sale_order = self.env['sale.order'].sudo().search(confirm_so)
                invoice_partail_paid = False
                if sale_order:
                    invoice_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                      ('partner_id', '=', self.partner_id.id),
                                      ('name', 'not in', sale_order.mapped('name')),
                                      ('state', 'in', ['open', 'draft', 'approve', 'in payment'])]
                    invoice_paid_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                              ('partner_id', '=', self.partner_id.id),
                                              ('origin', 'in', sale_order.mapped('name')),
                                              ('state', 'in', ['paid'])]

                    invoice_partail_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                              ('partner_id', '=', self.partner_id.id),
                                              ('origin', 'in', sale_order.mapped('name')),
                                              ('state', 'in', ['open'])]

                    invoice_partail = self.env['account.invoice'].sudo().search(invoice_partail_domain)
                    invoice_paid = self.env['account.invoice'].sudo().search(invoice_paid_domain)

                    invoice_partail_paid = sum([inv.amount_total for inv in invoice_paid]) + sum(
                        [(inv.amount_total - inv.residual) if inv.residual != inv.amount_total else 0 for inv in
                         invoice_partail])
                else:
                    invoice_domain = [('type', '=', 'out_invoice'), ('company_id', '=', self.company_id.id),
                                      ('partner_id', '=', self.partner_id.id),
                                      ('state', 'in', ['open', 'draft', 'approve', 'in payment'])]

                open_due_invoices = self.env['account.invoice'].sudo().search(invoice_domain)

                invoice_amount = sum([inv.residual for inv in open_due_invoices])
                sale_amount = sum([sale.amount_total for sale in sale_order])
                if invoice_partail_paid:
                    sale_amount = (sale_amount - invoice_partail_paid)
                sale_amount = float_round((sale_amount + self.amount_total + invoice_amount), 2,
                                          rounding_method='HALF-UP')
                # print('>>>>>>>action_confirm AFTER search Sale Order 1')
                # sort by billing date
                aging_day = 0
                if overdue_invoices:
                    sorted_invoices = overdue_invoices.sudo().sorted(key=lambda t: t.date_invoice, reverse=True)
                    aging_day = sorted_invoices[0].date_invoice - datetime.today().date()
                new_overdue_amount = float_round(overdue_amount, 2, rounding_method='HALF-UP')
                # print('>>>>>>>action_confirm AFTER search Sale Order 2')
                # if new_overdue_amount > 0 and  aging_day.days > 0:
                if new_overdue_amount > 0:
                    if not self.sudo().approval_reasons:
                        self.sudo().approval_reasons = "Invoice Overdue Block - Overdue Amount=" + str(
                            new_overdue_amount) + '\n'
                        if sale_amount:
                            self.sudo().approval_reasons = self.sudo().approval_reasons + "Outstanding Invoice Amount is " + str(
                                sale_amount) + '\n'
                        # if aging_day.days > 0:
                        if aging_day != 0:
                            self.sudo().approval_reasons = self.sudo().approval_reasons + "Aging Day is " + str(
                                aging_day) + '\n'
                    elif "Invoice Overdue" not in self.sudo().approval_reasons:
                        self.sudo().approval_reasons = self.sudo().approval_reasons + "Invoice Overdue Block - Overdue Amount=" + str(
                            new_overdue_amount) + '\n'
                        if sale_amount:
                            self.sudo().approval_reasons = self.sudo().approval_reasons + "Outstanding Invoice Amount is " + str(
                                sale_amount) + '\n'
                        # if aging_day.days > 0:
                        if aging_day != 0:
                            self.sudo().approval_reasons = self.sudo().approval_reasons + "Aging Day is " + str(
                                aging_day) + '\n'
            # print('>>>>>>>action_confirm check if any discount reason to fill')
            # kashif - 22may23 : include discount and payment term change
            discount_reason = self.sudo().get_discount_request_reason()
            if discount_reason:
                self.sudo().approval_reasons = self.sudo().approval_reasons + \
                                               discount_reason
            payment_term_reason = self.sudo().get_payment_term_reason()
            # kashif 29may23: also check if payment term change . added new field that will cehck this
            if payment_term_reason and self.is_payment_term_change:
                self.sudo().approval_reasons = self.sudo().approval_reasons + \
                                               payment_term_reason
            # end
            self.check_partner_credit()
            # return self.check_blocked_partner()
        # If credit limit is OK
        # if self.state in ['approved', 'sent', 'draft'] and not self.req_credit_limit_approved and not self.req_discount_approval:
        # if self.check_partner_credit():
        # print('confirm_so SO state=', self.state, ' ,  req_credit_limit_approved=', self.req_credit_limit_approved,
        #      ' , overdue block=', self.partner_id.is_overdue_block)
        credit_id = self.env['partner.credit.approval'].sudo().search([('order_id', '=', self.id),
                                                                       ('company_id', '=', self.company_id.id)],
                                                                      limit=1)
        so_approved = False
        if credit_id:
            if credit_id.status == 'approved':
                so_approved = True
        if self.state in ['approve', 'approved', 'sent', 'draft'] and (not self.sudo().approval_reasons or so_approved) \
                and self.req_credit_limit_approved:
            wiz_id = self.env['sale.won.reason.wiz'].create({'sale_order_id': self.id})
            return {
                'name': _('Select Won Reason'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.won.reason.wiz',
                'views': [(self.env.ref('goexcel_sale.sale_won_wiz_view_form').id, 'form')],
                'view_id': self.env.ref('goexcel_sale.sale_won_wiz_view_form').id,
                'target': 'new',
                'res_id': wiz_id.id
            }
        else:
            return {
                'name': _('Create UnBlock Request'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'unblock.credit.request.wiz',
                'views': [(self.env.ref('goexcel_sale.partner_unblock_form_view').id, 'form')],
                'view_id': self.env.ref('goexcel_sale.partner_unblock_form_view').id,
                'target': 'new',
                # 'res_id': wiz_id.id,
                'context': dict(so_id=self.id),
            }

            # wiz_id = self.env['sale.won.reason.wiz'].create({'sale_order_id': self.id})
            # return {
            #     'name': _('Select Won Reason'),
            #     'type': 'ir.actions.act_window',
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'res_model': 'sale.won.reason.wiz',
            #     'views': [(self.env.ref('goexcel_sale.sale_won_wiz_view_form').id, 'form')],
            #     'view_id': self.env.ref('goexcel_sale.sale_won_wiz_view_form').id,
            #     'target': 'new',
            #     'res_id': wiz_id.id
            # }

    # @api.multi
    # def find_over_due_invoice(self):
    #     for rec in self:
    #         next_date = datetime.today().date() + relativedelta(days=1)
    #         invoice_ids = self.env['account.invoice'].search([('type', '=', 'out_invoice'), ('state', '=', 'open'),
    #                                                           ('date_due', '>=', next_date),
    #                                                           ('partner_id', '=', rec.partner_id.id)])
    #         if invoice_ids:
    #             for inv in invoice_ids:
    #                 if not inv.partner_id.is_overdue_block:
    #                     inv.partner_id.is_overdue_block = True
    #                     break
    #         else:
    #             rec.partner_id.is_overdue_block = False
    # for credit limit
    @api.multi
    def send_approval_credit_limit_mail(self):
        template = self.env.ref('goexcel_sale.email_credit_limit_approval_sale_order')
        assert template._name == 'mail.template'
        email_lst = []
        email_lst += [user.email for user in filter(lambda x: x.email, self.company_id.sq_credit_limit_approver_ids)]
        email_to = ','.join(map(str, email_lst))
        if template and email_lst:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def send_reject_credit_limit_mail(self):
        # print('>>>>>>>>> send_reject_credit_limit_mail 1 >>>>>>>>>> ')
        template = self.env.ref('goexcel_sale.email_credit_limit_reject_sale_order')
        # print('>>>>>>>>> send_reject_credit_limit_mail 2 >>>>>>>>>> ')
        assert template._name == 'mail.template'
        # print('>>>>>>>>> send_reject_credit_limit_mail 3 >>>>>>>>>> ')
        email_to = self.user_id.email
        template.write({'email_to': email_to})
        # print('>>>>>>>>> send_reject_credit_limit_mail 4 >>>>>>>>>> ')
        template.send_mail(self.id, force_send=True)

    @api.multi
    def send_approved_credit_limit_mail(self):
        template = self.env.ref('goexcel_sale.email_credit_limit_approved_sale_order')
        assert template._name == 'mail.template'
        email_to = self.user_id.email
        template.write({'email_to': email_to})
        template.send_mail(self.id, force_send=True)

    # for discount
    @api.multi
    def send_approval_max_discount_mail(self):
        template = self.env.ref('goexcel_sale.email_max_discount_approval_sale_order')
        assert template._name == 'mail.template'
        email_lst = []
        email_lst += [user.email for user in filter(lambda x: x.email, self.company_id.max_discount_approver_ids)]
        email_to = ','.join(map(str, email_lst))
        if template and email_lst:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def send_reject_max_discount_mail(self):
        # print('>>>>>>>>> send_reject_max_discount_mail 1 >>>>> ')
        template = self.env.ref('goexcel_sale.email_max_discount_reject_sale_order')
        # print('>>>>>>>>> send_reject_max_discount_mail 2 >>>>> ')
        assert template._name == 'mail.template'
        # print('>>>>>>>>> send_reject_max_discount_mail 3 >>>>> ')
        email_to = self.user_id.email
        # print('>>>>>>>>> send_reject_max_discount_mail 4 >>>>> ')
        template.write({'email_to': email_to})
        # print('>>>>>>>>> send_reject_max_discount_mail 5 >>>>> ')
        template.send_mail(self.id, force_send=True)

    @api.multi
    def send_approved_max_discount_mail(self):
        template = self.env.ref('goexcel_sale.email_max_discount_approved_sale_order')
        assert template._name == 'mail.template'
        email_to = self.user_id.email
        template.write({'email_to': email_to})
        template.send_mail(self.id, force_send=True)

    # payment term / pricelist
    @api.multi
    def send_approval_payment_term_pricelist_mail(self):
        # print ("::::::::::send_approval_payment_term_pricelist_mail::::::::::")
        template = self.env.ref('goexcel_sale.email_payment_term_pricelist_approval_sale_order')
        assert template._name == 'mail.template'
        email_lst = []
        email_lst += [user.email for user in filter(lambda x: x.email, self.company_id.payment_term_approver_ids)]
        email_to = ','.join(map(str, email_lst))
        if template and email_lst:
            template.write({'email_to': email_to})
            template.send_mail(self.id, force_send=True)

    @api.multi
    def send_reject_payment_term_pricelist_mail(self):
        # print (":::::::::::send_reject_payment_term_pricelist_mail 1::::::::::::::::::")
        template = self.env.ref('goexcel_sale.email_payment_term_pricelist_reject_sale_order')
        # print(":::::::::::send_reject_payment_term_pricelist_mail 2::::::::::::::::::")
        assert template._name == 'mail.template'
        # print(":::::::::::send_reject_payment_term_pricelist_mail 3::::::::::::::::::")
        email_to = self.user_id.email
        # print(":::::::::::send_reject_payment_term_pricelist_mail 4::::::::::::::::::")
        template.write({'email_to': email_to})
        # print(":::::::::::send_reject_payment_term_pricelist_mail 5::::::::::::::::::")
        template.send_mail(self.id, force_send=True)

    @api.multi
    def send_approved_payment_term_pricelist_mail(self):
        # print ("::::::::::::send_approved_payment_term_pricelist_mail::::::::::::::::::::::")
        template = self.env.ref('goexcel_sale.email_payment_term_pricelist_approved_sale_order')
        assert template._name == 'mail.template'
        email_to = self.user_id.email
        template.write({'email_to': email_to})
        template.send_mail(self.id, force_send=True)

    # @api.multi
    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, **kwargs):
    #     # if self.env.context.get('mark_so_as_sent'):
    #     #     self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
    #     #     self.env.user.company_id.set_onboarding_step_done('sale_onboarding_sample_quotation_state')
    #     return super(SaleOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    avaible_qty = fields.Float(string="Available Qty", readonly=True, copy=False)
    sale_product_category = fields.Char(related='product_id.categ_id.name', string="Product Category", store=True,
                                        copy=False)
    sale_order_date = fields.Datetime(related='order_id.confirmation_date', string="Order Date", store=True, copy=False)
    sale_uom = fields.Char(related='product_id.uom_id.name', string="UoM", store=True, copy=False)
    sale_volume = fields.Float(string="Volume(L)", compute="_get_volume", copy=False)
    # sale_total_volume = fields.Float(string="Volume(L)", compute="get_sale_total_volume", copy=False, store=True)
    sale_invoiced_volume = fields.Float(string="Inv. Vol", compute="_get_sale_invoiced_volume", copy=False)
    sale_invoiced_amount = fields.Float(string="Inv. Amt", compute="_get_sale_invoiced_amount", copy=False)
    sale_invoiced_volume_2 = fields.Float(related='sale_invoiced_volume', string="Inv. Vol", copy=False, store=True)
    sale_invoiced_amount_2 = fields.Float(related='sale_invoiced_amount', string="Inv. Amt", copy=False, store=True)

    # sale_invoiced_amount_1 = fields.Float(string="Inv. Amt 1", compute="_get_sale_invoiced_amount", copy=False)

    # @api.depends('product_id')
    def _get_volume(self):
        for rec in self:
            vol_litre = 0.00
            if rec.product_id and rec.sale_uom:
                vol = rec.sale_uom[rec.sale_uom.find("(") + 1:rec.sale_uom.find(")")]
                if vol and len(vol) > 1:
                    vol_litre = re.sub("[LMKGUNIniCarto]", "", vol)
                    # print('>>>>>>>>>>> get_volume vol_litre=', vol_litre)
                    # rec.sale_volume = vol_litre
                if rec.product_id and rec.qty_invoiced and rec.price_unit:
                    rec.sale_invoiced_volume = rec.sale_volume * rec.qty_invoiced
                if rec.product_id and rec.qty_invoiced and rec.sale_volume:
                    rec.sale_invoiced_volume = rec.sale_volume * rec.qty_invoiced

    @api.depends('product_id')
    def _get_sale_invoiced_volume(self):
        for rec in self:
            if rec.product_id and rec.qty_invoiced and rec.sale_volume:
                rec.sale_invoiced_volume = rec.sale_volume * rec.qty_invoiced

    def _get_sale_invoiced_amount(self):
        for rec in self:
            if rec.product_id and rec.qty_invoiced and rec.price_unit:
                rec.sale_invoiced_amount = rec.price_unit * rec.qty_invoiced

    @api.multi
    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def product_id_qty(self):
        if not self.product_id:
            self.avaible_qty = 0
        if self.product_id and self.product_id.type == 'product':
            self.avaible_qty = self.product_id.qty_available

    discount_fixed = fields.Float(string="Discount (Fixed)", digits=dp.get_precision('bps percentage'),
                                  help="Fixed amount discount.", copy=False)

    @api.onchange('discount')
    def _onchange_discount_percent(self):
        # _onchange_discount method already exists in core,
        # but discount is not in the onchange definition
        if self.discount:
            self.discount_fixed = 0.0

    @api.onchange('discount_fixed')
    def _onchange_discount_fixed(self):
        if self.discount_fixed:
            self.discount = 0.0

    @api.constrains('discount', 'discount_fixed')
    def _check_only_one_discount(self):
        for line in self:
            if line.discount and line.discount_fixed:
                raise ValidationError(_("You can only set one type of discount per line."))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_fixed')
    def _compute_amount(self):
        vals = {}
        for line in self.filtered(lambda l: l.discount_fixed):
            real_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0
                                            ) - (line.discount_fixed or 0.0)
            twicked_price = real_price / (1 - (line.discount or 0.0) / 100.0)
            vals[line] = {
                'price_unit': line.price_unit,
            }
            line.update({
                'price_unit': twicked_price,
            })
        res = super(SaleOrderLine, self)._compute_amount()
        for line in vals.keys():
            line.update(vals[line])
        return res

    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({
            'discount_fixed': self.discount_fixed,
        })
        return res


class SaleLostReason(models.Model):
    _name = 'sale.lost.reason'
    _description = "Sale Lost Reason"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Reason", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Reason must be unique within an application!')]


class SaleExtendReason(models.Model):
    _name = 'sale.extend.reason'
    _description = 'Sale Extend Reason'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Reason", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Reason must be unique within an application!')]


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    inv_volume = fields.Float(string="Volume", compute='_get_volume', store=True)

    # kashif 15june23 : update code so it can handel float volume number
    def isValidNum(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    # end

    @api.depends('uom_id', 'quantity')
    def _get_volume(self):
        for rec in self:
            rec.inv_volume = 1.0
            name = rec.uom_id.name
            if rec.product_id and rec.uom_id:
                vol = name[name.find("(") + 1:name.find(")")]
                if vol and len(vol) > 1:
                    vol_litre = re.sub("[LMKGUNIniCarto]", "", vol)
                    # kashif 15june23 : update code so it can handel float volume number
                    is_valid = self.isValidNum(vol_litre)
                    # print (">>>>>>>>", vol_litre)
                    if is_valid:
                        rec.inv_volume = float(vol_litre)
                    else:
                        rec.inv_volume = 1.0
                    # End Kashif
                else:
                    rec.inv_volume = 1
