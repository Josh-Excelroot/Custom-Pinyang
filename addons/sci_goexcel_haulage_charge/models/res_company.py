# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    haulage_charge_approval_user_ids = fields.Many2many('res.users', 'haulage_charge_approval_user_default_rel',
                                                      string='Haulage Charge Approvers')
    haulage_charge_notification_user_ids = fields.Many2many('res.users', 'haulage_charge_notification_user_default_rel',
                                                          string='Haulage Charge Approval Notification Recipient')
