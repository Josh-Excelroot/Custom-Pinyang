# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sq_approval = fields.Boolean(
        "SQ Approval", related="company_id.sq_approval", readonly=False
    )
    sq_amount = fields.Monetary(
        related="company_id.sq_amount", string="SQ Minimum Amount", readonly=False
    )

    sq_approval_user_ids = fields.Many2many(
        "res.users",
        related="company_id.sq_approval_user_ids",
        readonly=False,
        string="SQ Approvers",
    )
    sq_notification_user_ids = fields.Many2many(
        "res.users",
        related="company_id.sq_notification_user_ids",
        readonly=False,
        string="SQ Approval Notification Recipients",
    )
