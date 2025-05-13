# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
from datetime import datetime


class SalesOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales Order Validate View"

    approve_by = fields.Many2one(
        "res.users", string="Approved By", track_visibility="always", copy=False
    )
    approve_date_time = fields.Datetime(
        string="Approved Date", track_visibility="always", copy=False
    )
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("approve", "To Approve"),
            ("approved", "Approved"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        index=True,
        track_visibility="onchange",
        default="draft",
    )
    sq_min_amount = fields.Integer(
        string="SQ Minimum Amount", compute="_get_sq_min_amount"
    )
    approve_show_button = fields.Boolean(compute="_set_access_for_approve_button")

    def _set_access_for_approve_button(self):
        """Ensure the method works for multiple records."""
        list_of_user = self.env.user.company_id.sq_approval_user_ids
        for rec in self:
            rec.approve_show_button = bool(list_of_user and rec.env.user in list_of_user)

    def read(self, fields=None, load="_classic_read"):
        """Override read method to trigger button visibility when opening the record."""
        records = super(SalesOrder, self).read(fields, load)
        self._set_access_for_approve_button()
        return records



    def _get_sq_min_amount(self):
        self.sq_min_amount = self.company_id.sq_amount
        # print("sq min amount=" + str(self.sq_min_amount))
        # if self.env['res.users'].has_group('sales_team.group_sale_manager'):
        # if self.state == 'draft':
        #    self.write({'state': 'approved'})

    # @api.multi
    # def action_to_approve(self):
    #     self.write({'state': 'approve'})

    # @api.one
    # def _set_access_for_approve_reject(self):
    #     list_of_user = self.company_id.sq_approval_user_ids
    #     # print('list_of_user=' + str(list_of_user) + ' vs uid=' + str(self.env.uid))
    #     if list_of_user:
    #         if self.env.user in list_of_user:
    #             self.approve_reject_sq = True
    #         else:
    #             self.approve_reject_sq = False
    #     else:
    #         self.approve_reject_sq = False
    #     print("self.approve_reject_sq=" + str(self.approve_reject_sq))
    #
    # approve_reject_sq = fields.Boolean(
    #     compute="_set_access_for_approve_reject",
    #     string="Is user able to approve/reject sq?",
    # )

    @api.onchange("state")  # Trigger when state changes
    def _onchange_state(self):
        """Ensure button visibility updates in real-time."""
        list_of_user = self.env.user.company_id.sq_approval_user_ids
        for rec in self:
            rec.approve_show_button = rec.env.user in list_of_user

    @api.multi
    def action_request_approve(self):
        if not self.sale_order_template_id:
            raise UserError("Please select a Quotation Template.")
        ctx = {}
        ctx["type"] = "Sales Quotation"
        action = self.env.ref("sale.action_orders").id
        amount = self.company_id.sq_amount
        if float(amount) <= self.amount_total:
            # _logger.warning("true")
            self.state = "approve"
            list_of_user = self.env.user.company_id.sq_approval_user_ids
            email_list = [user.email for user in list_of_user]
            # email_list = [user.email for user in self.env['res.users'].sudo().search(
            #     [('company_ids', 'in', self.company_id.ids)]) if user.has_group('sales_team.group_sale_manager')]
            if email_list:
                ctx["partner_manager_email"] = ",".join(
                    [email for email in email_list if email]
                )
                ctx["email_from"] = self.env.user.email
                ctx["partner_name"] = self.env.user.name
                ctx["customer_name"] = self.partner_id.name
                ctx["amount_total"] = self.amount_total
                ctx["lang"] = self.env.user.lang
                ctx["sq"] = self.name
                template = self.env.ref(
                    "sales_quote_approval_workflow_branches.sales_quotation_validate_email_template"
                )
                base_url = (
                    self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                )
                ctx[
                    "action_url"
                ] = "{}/web?db={}#id={}&action={}&view_type=form&model=sale.order".format(
                    base_url, self.env.cr.dbname, self.id, action
                )
                template.with_context(ctx).sudo().send_mail(
                    self.id, force_send=True, raise_exception=False
                )
        else:
            self.write({"state": "approved"})

    @api.multi
    def action_approve(self):
        self.approve_by = self.env.user.id
        self.approve_date_time = datetime.now()
        self.write({"state": "approved"})
        ctx = {}
        ctx["type"] = "Sales Quotation"
        action = self.env.ref("sale.action_orders").id
        list_of_user = self.company_id.sq_notification_user_ids
        email_list = [user.email for user in list_of_user]
        email_list.append(self.create_uid.email)
        # email_list = [user.email for user in self.env['res.users'].sudo().search(
        # [('company_ids', 'in', self.company_id.ids)]) if user.has_group('sales_team.group_sale_manager')]
        if email_list:
            ctx["partner_manager_email"] = ",".join(
                [email for email in email_list if email]
            )
            ctx["email_from"] = self.env.user.email
            ctx["email_salesperson"] = self.user_id.email
            ctx["approver_name"] = self.env.user.name
            ctx["customer_name"] = self.partner_id.name
            ctx["amount_total"] = self.amount_total
            ctx["lang"] = self.env.user.lang
            ctx["sq"] = self.name
            template = self.env.ref(
                "sales_quote_approval_workflow_branches.sales_quotation_approve_email_template"
            )
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            ctx[
                "action_url"
            ] = "{}/web?db={}#id={}&action={}&view_type=form&model=sale.order".format(
                base_url, self.env.cr.dbname, self.id, action
            )
            template.with_context(ctx).sudo().send_mail(
                self.id, force_send=True, raise_exception=False
            )

            #print("send approved email")

    @api.multi
    def action_reject(self):
        self.write({"state": "draft"})
        ctx = {}
        ctx["type"] = "Sales Quotation"
        action = self.env.ref("sale.action_orders").id
        list_of_user = self.company_id.sq_notification_user_ids
        email_list = [user.email for user in list_of_user]
        email_list.append(self.create_uid.email)
        # email_list = [user.email for user in self.env['res.users'].sudo().search(
        #     [('company_ids', 'in', self.company_id.ids)]) if user.has_group('sales_team.group_sale_manager')]
        if email_list:
            ctx["partner_manager_email"] = ",".join(
                [email for email in email_list if email]
            )
            ctx["email_from"] = self.env.user.email
            ctx["email_salesperson"] = self.user_id.email
            ctx["approver_name"] = self.env.user.name
            ctx["customer_name"] = self.partner_id.name
            ctx["amount_total"] = self.amount_total
            ctx["lang"] = self.env.user.lang
            ctx["sq"] = self.name
            template = self.env.ref(
                "sales_quote_approval_workflow_branches.sales_quotation_reject_email_template"
            )
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            ctx[
                "action_url"
            ] = "{}/web?db={}#id={}&action={}&view_type=form&model=sale.order".format(
                base_url, self.env.cr.dbname, self.id, action
            )
            template.with_context(ctx).sudo().send_mail(
                self.id, force_send=True, raise_exception=False
            )
            print("send reject email")

    @api.multi
    def action_quotation_send(self):
        res = super(SalesOrder, self).action_quotation_send()
        self.write({"state": "sent"})
        return res

    @api.multi
    def print_quotation(self):
        # res = super(SalesOrder, self).print_quotation()
        if self.state != "sale":
            self.write({"state": "sent"})
        return (
            self.env.ref("sale.action_report_saleorder")
            .with_context({"discard_logo_check": True})
            .report_action(self)
        )

    @api.onchange("amount_total")
    def onchange_amount_total(self):
        if self.state == "approved":
            self.state = "draft"

