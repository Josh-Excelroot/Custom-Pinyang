# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    technical_plan_approver_ids = fields.Many2many('res.users', 'technical_plan_user_default_rel', string="Technical Plan Approver")
    gift_approver_ids = fields.Many2many('res.users', 'gift_user_default_rel', string="Gift Approver")
    gift_approved_notification = fields.Many2many('res.users', 'gift_approved_notification_rel', string="Gift Approved Notification")
