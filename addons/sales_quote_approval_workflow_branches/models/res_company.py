# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    sq_approval = fields.Boolean("SQ Approval")
    sq_amount = fields.Monetary(string='SQ Double validation amount')

    sq_approval_user_ids = fields.Many2many('res.users', 'sq_approval_user_default_rel', string='SQ Approvers')
    sq_notification_user_ids = fields.Many2many('res.users', 'sq_notification_user_default_rel',
                                                string='SQ Approval Notification Recipient')