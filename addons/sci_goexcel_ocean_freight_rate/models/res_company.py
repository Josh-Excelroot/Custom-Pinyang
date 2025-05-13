# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    ocean_freight_rate_approval_user_ids = fields.Many2many('res.users', 'ocean_freight_rate_approval_user_default_rel',
                                                      string='Ocean Freight Rate Approvers')
    ocean_freight_rate_notification_user_ids = fields.Many2many('res.users', 'ocean_freight_rate_notification_user_default_rel',
                                                          string='Ocean Freight Rate Approval Notification Recipient')
