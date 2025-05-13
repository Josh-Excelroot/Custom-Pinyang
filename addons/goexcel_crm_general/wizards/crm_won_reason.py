# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLeadWon(models.TransientModel):
    _name = 'crm.lead.won'
    _description = 'Lead Won Reason'

    won_reason_id = fields.Many2many('crm.won.reason', string='Won Reason')
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")

    @api.multi
    def action_won_reason_apply(self):
        for record in self:
            self.crm_lead_id.won_reason_id = record.won_reason_id.ids
            record.crm_lead_id.action_set_won()

