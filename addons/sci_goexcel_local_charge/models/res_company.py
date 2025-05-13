# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    local_charge_approval_user_ids = fields.Many2many('res.users', 'local_charge_approval_user_default_rel',
                                                      string='Local Charge Approvers')
    local_charge_notification_user_ids = fields.Many2many('res.users', 'local_charge_notification_user_default_rel',
                                                          string='Local Charge Approval Notification Recipient')
