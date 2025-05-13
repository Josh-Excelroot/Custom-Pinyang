# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    technical_plan_approver_ids = fields.Many2many(related='company_id.technical_plan_approver_ids', readonly=False, string="Technical Plan Approver")
    gift_approver_ids = fields.Many2many(related='company_id.gift_approver_ids', readonly=False, string="Gift Approver")
    gift_approved_notification = fields.Many2many(related="company_id.gift_approved_notification", readonly=False, string="Gift Approved Notification")
