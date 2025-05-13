# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleApprovalSettings(models.Model):
    _name = "sale.approval.settings"

    sq_approval_user_ids = fields.Many2many(
        "res.users", "sq_approvers", "user_id", "approver_id", string="SQ Approvers",
    )
    sq_notification_user_ids = fields.Many2many(
        "res.users",
        "sq_recipients",
        "user_id",
        "recipient_id",
        string="SQ Approval Notification Recipients",
    )
    sq_branch = fields.Many2one("account.analytic.tag", string="Branch",)

