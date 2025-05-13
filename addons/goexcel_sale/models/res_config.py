# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sq_remider_days = fields.Integer(related='company_id.sq_remider_days', default=7, string="Reminder for Sale Quotation Days After", readonly=False)
    use_sq_remider_days = fields.Boolean(related='company_id.use_sq_remider_days', string="Send SQ Reminder?", readonly=False)
    cr_limit_app_user_ids = fields.Many2many('res.users', related='company_id.cr_limit_app_user_ids', readonly=False, string="Credit Approver User")
    max_discount_approver_ids = fields.Many2many('res.users', related='company_id.max_discount_approver_ids', readonly=False, string="Max Discount Approver")
    sq_credit_limit_approver_ids = fields.Many2many('res.users', related='company_id.sq_credit_limit_approver_ids', readonly=False, string="SQ Credit Limit Approver")
    payment_term_approver_ids = fields.Many2many('res.users', related='company_id.payment_term_approver_ids', string="Payment Term/Pricelist Approver", readonly=False)

    # cash_order_payment_method_id = fields.Many2one('account.journal', related="company_id.cash_order_payment_method_id", string="Payment Journal", domain="[('type', 'in', ['bank', 'cash'])]", readonly=False)
    customer_code = fields.Char(related="company_id.customer_code", string="Customer Code", readonly=False)
    vendor_code = fields.Char(related="company_id.vendor_code", string="Vendor Code", readonly=False)
    enble_cust_code = fields.Boolean(related="company_id.enble_cust_code", string="Enable customer Code?", readonly=False)
    enble_ven_code = fields.Boolean(related="company_id.enble_ven_code", string="Enable Vendor Code?", readonly=False)
