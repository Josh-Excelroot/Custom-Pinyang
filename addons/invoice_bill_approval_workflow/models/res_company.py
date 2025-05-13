# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    invoice_bill_approval = fields.Boolean("Invoice/Bill Approval")
    invoice_ammount = fields.Monetary(string='Invoice Double validation amount')
    bill_ammount = fields.Monetary(string='Bill Double validation amount')
    customer_vendor_credit_approval = fields.Boolean("Customer/Vendor Credit Note Approval")
    customer_credit_note_ammount_ammount = fields.Monetary(string='Customer credit note alidation amount')
    vendor_credit_note_ammount = fields.Monetary(string='Vendor credit note validation amount')
    # code added by shivam-laxicon solution
    invoice_user_ids = fields.Many2many('res.users', 'invoice_user_default_rel', string='invoice User')
    bill_user_ids = fields.Many2many('res.users', 'bill_user_default_rel', string='Bill User')
    invoice_cn_user_ids = fields.Many2many('res.users', 'invoice_cn_user_default_rel', string='Invoice CN User')
    bill_cn_user_ids = fields.Many2many('res.users', 'bill_cn_user_default_rel', string='Bill CN User')

    #Vendor payment approval
    vendor_payment_approval = fields.Boolean("Vendor Payment Approval")
    vendor_payment_amount = fields.Monetary(string="Vendor Payment Minimum Amount")
    vendor_payment_user_ids = fields.Many2many('res.users', string="Vendor Payment Users")

    invoice_notification_user_ids = fields.Many2many('res.users', 'invoice_notification_user_default_rel',
                                                     string='Invoice Approval Notification Recipient')
    bill_notification_user_ids = fields.Many2many('res.users', 'bill_notification_user_default_rel',
                                                  string='Bill Approval Notification Recipient')
    invoice_cn_notification_user_ids = fields.Many2many('res.users', 'invoice_cn_notification_user_default_rel',
                                                        string='Invoice CN Approval Notification Recipient')
    bill_cn_notification_user_ids = fields.Many2many('res.users', 'bill_cn_notification_user_default_rel',
                                                     string='Bill CN Approval Notification Recipient')

    # added this constrain by Shivam- Laxicon Solution
    @api.constrains('invoice_user_ids', 'bill_user_ids', 'invoice_cn_user_ids', 'bill_cn_user_ids')
    def check_user_group_validation(self):
        for res in self:
            print('check_user_group_validation')
            # if res.invoice_bill_approval and res.invoice_ammount > 0:
            #     if len(self.invoice_user_ids) == 0:
            #         raise ValidationError('You need to select Invoice Approver')
            # if res.invoice_bill_approval and res.bill_ammount > 0:
            #     if len(self.bill_user_ids) == 0:
            #         raise ValidationError('You need to select Bill Approver')
            # if res.customer_vendor_credit_approval and res.customer_credit_note_ammount_ammount > 0:
            #     if len(self.invoice_cn_user_ids) == 0:
            #         raise ValidationError('You need to select Invoice Credit Note Approver')
            # if res.customer_vendor_credit_approval and res.vendor_credit_note_ammount > 0:
            #     if len(self.bill_cn_user_ids) == 0:
            #         raise ValidationError('You need to select Bill Credit Note Approver')
