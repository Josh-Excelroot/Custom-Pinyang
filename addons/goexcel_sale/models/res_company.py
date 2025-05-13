# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    sq_remider_days = fields.Integer(default=7, string="Reminder for Sale Quotation Days After")
    use_sq_remider_days = fields.Boolean(string="Send SQ Reminder?")
    cr_limit_app_user_ids = fields.Many2many('res.users', 'credlimit_user_default_rel', string='Credit Approver Approver')
    max_discount_approver_ids = fields.Many2many('res.users', 'max_discount_user_default_rel', string="Max Discount Approver")
    sq_credit_limit_approver_ids = fields.Many2many('res.users', 'sq_credit_limit_user_default_rel', string="SQ Credit Limit Approver")
    payment_term_approver_ids = fields.Many2many('res.users', 'payment_term_user_default_rel', string="Payment Term/Pricelist Approver")

    # cash_order_payment_method_id = fields.Many2one('account.journal', string="Payment Journal", domain="[('type', 'in', ['bank', 'cash'])]")
    customer_code = fields.Char(string="Customer Code")
    vendor_code = fields.Char(string="Vendor Code")
    enble_cust_code = fields.Boolean(string="Enable Customer Code?")
    enble_ven_code = fields.Boolean(string="Enable Vendor Code?")
