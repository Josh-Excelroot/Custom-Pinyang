# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class RejectReason(models.TransientModel):
    _name = 'reject.reason'
    _description = 'Reject Reason'

    reject_reason = fields.Text(string='Reject Reason', track_visibility='onchange')
    #Link to the main invoice
    invoice_id = fields.Many2one('account.invoice', string="Invoice")


    @api.multi
    def action_reject_reason(self):
        self.ensure_one()
        self.invoice_id.write({'state': 'draft'})
        self.invoice_id.write({'reject_reason': self.reject_reason
                               })

        return True
