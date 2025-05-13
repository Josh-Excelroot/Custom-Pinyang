from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError


class PartnerCreditApprovwiz(models.TransientModel):
    _name = "partner.credit.approval.wiz"
    _description = "Partner Credit Approval"

    partner_id = fields.Many2one('res.partner', string="Customer")
    order_id = fields.Many2one('sale.order', string="Quotation/Order")
    old_credit_term_id = fields.Many2one('account.payment.term', string="Old credit Term")
    new_credit_term_id = fields.Many2one('account.payment.term', string="New credit Term")
    old_credit_limit = fields.Float(string="Old Credit Limit")
    new_credit_limit = fields.Float(string="New Credit Limit")
    requested_by_id = fields.Many2one('res.users', string="Requested By")
    remark = fields.Text(string="Remark")

    @api.multi
    def action_for_create_data(self):
        if self.new_credit_term_id or self.new_credit_limit:
            data = {
                'partner_id': self.partner_id.id,
                'old_credit_term_id': self.old_credit_term_id.id,
                'new_credit_term_id': self.new_credit_term_id.id,
                'old_credit_limit': self.old_credit_limit,
                'new_credit_limit': self.new_credit_limit,
                'requested_by_id': self.env.uid,
                'remark': self.remark
            }
            self.env['partner.credit.approval'].create(data)


