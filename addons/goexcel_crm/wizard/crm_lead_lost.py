# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date


class CrmLeadLost(models.TransientModel):
    _name = 'crm.lead.lost'
    _description = 'crm lost Reason'

    lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost Reason')
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")

    @api.multi
    def action_lost_reason_apply(self):
        partner = False
        res_partner = self.env['res.partner']
        data = {
            'name': self.crm_lead_id.name,
            'street': self.crm_lead_id.street or False,
            'street2': self.crm_lead_id.street2 or False,
            'city': self.crm_lead_id.city or False,
            'state_id': self.crm_lead_id.state_id.id or False,
            'zip': self.crm_lead_id.zip or False,
            'country_id': self.crm_lead_id.country_id.id or False,
            'phone': self.crm_lead_id.phone or False,
            'mobile': self.crm_lead_id.mobile or False,
            # 'fax': self.crm_lead_id.fax or False,
            # 'email': self.crm_lead_id.email or False,
            'company_type': 'company',
            'user_id': self.crm_lead_id.env.user.id,
            'customer': False,
            'is_prospect': True,
            }
        partner = res_partner.create(data)
        stage_id = self.env['crm.stage'].search([('stage_type', '=', 'close')], limit=1)
        if self.crm_lead_id:
            data = {
                'lost_stage_id': stage_id and stage_id.id or False,
                'lost_date': date.today(),
                'probability': 0,
                'stage_id': stage_id and stage_id.id or False,
                'partner_id': partner.id or False
            }
            self.crm_lead_id.write(data)
        if partner:
            data = {
                    #'status': 'lost_customer',
                    'lost_reason_id': self.lost_reason_id.id,
                    'lost_date': date.today()
                }
            self.crm_lead_id.partner_id.write(data)
