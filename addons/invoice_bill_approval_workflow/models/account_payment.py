# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _
from datetime import datetime


class AccountPayment(models.Model):
    _inherit = "account.payment"

    approve_by = fields.Many2one(
        'res.users', string='Approved By', track_visibility='always', copy=False)
    approve_date_time = fields.Datetime(string='Approved Date', track_visibility='always', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('approve', 'To Approve'), ('posted', 'Posted'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    #reject_reason = fields.Text(string='Reject Reason', track_visibility='onchange')


    @api.multi
    def action_vendor_payment_approve(self):
        for payment in self:
            payment.write({'state': 'draft'})
            payment.approve_by = self.env.user.id
            payment.approve_date_time = datetime.now()
            payment.post()

    @api.multi
    def action_vendor_payment_reject(self):
        for payment in self:
            payment.write({'state': 'draft'})


    @api.multi
    def post_vendor_payment(self):
        for payment in self:
            if payment.company_id.vendor_payment_approval:
                if payment.amount > payment.company_id.vendor_payment_amount:
                    payment.write({'state': 'approve'})
            else:
                payment.post()
        a=1
        b=1




