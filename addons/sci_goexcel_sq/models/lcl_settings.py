# -*- coding: utf-8 -*-
from odoo import fields, models


class LCLSettings(models.Model):
    _name = "lcl.settings"

    # sq_approval_user_ids = fields.Many2many(
    #     "res.users", "sq_approvers", "user_id", "approver_id", string="SQ Approvers",
    # )
    # sq_notification_user_ids = fields.Many2many(
    #     "res.users",
    #     "sq_recipients",
    #     "user_id",
    #     "recipient_id",
    #     string="SQ Approval Notification Recipients",
    # )

    lcl_product = fields.Many2one("product.product", string="Product", )
    lcl_round_up_method = fields.Selection(
        [('round_up_to_single', 'Round up to Single Digit'), ('no_round_up', 'No Round Up'), ('round_up_to_1', 'Round up to 1 d.p')],
        string='Round-up Method')

    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air')],
                                    string='Service Type')
