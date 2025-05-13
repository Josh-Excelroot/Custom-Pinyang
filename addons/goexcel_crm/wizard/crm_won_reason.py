# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLeadWon(models.TransientModel):
    _name = 'crm.lead.won'
    _description = 'Get won Reason'

    won_reason_id = fields.Many2one('crm.won.reason', 'Won Reason')
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")

    @api.multi
    def action_won_reason_apply(self):
        print ("sdfsdbfjksdhbfkj")
        self.ensure_one()
        self.crm_lead_id.won_reason = self.won_reason_id.id
        # self.crm_lead_id.action_set_won()

        self.crm_lead_id.set_crm_analysis_history()
        stage_id = self.env['crm.stage'].search([('stage_type', '=', 'order')], limit=1) or False
        if stage_id:
            self.crm_lead_id.write({'stage_id': stage_id.id})

        if self.crm_lead_id.user_id and self.crm_lead_id.team_id and self.crm_lead_id.planned_revenue:
            query = """
                SELECT
                    SUM(CASE WHEN user_id = %(user_id)s THEN 1 ELSE 0 END) as total_won,
                    MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '30 days' AND user_id = %(user_id)s THEN planned_revenue ELSE 0 END) as max_user_30,
                    MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '7 days' AND user_id = %(user_id)s THEN planned_revenue ELSE 0 END) as max_user_7,
                    MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '30 days' AND team_id = %(team_id)s THEN planned_revenue ELSE 0 END) as max_team_30,
                    MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '7 days' AND team_id = %(team_id)s THEN planned_revenue ELSE 0 END) as max_team_7
                FROM crm_lead
                WHERE
                    type = 'opportunity'
                AND
                    active = True
                AND
                    probability = 100
                AND
                    DATE_TRUNC('year', date_closed) = DATE_TRUNC('year', CURRENT_DATE)
                AND
                    (user_id = %(user_id)s OR team_id = %(team_id)s)
            """
            self.env.cr.execute(query, {'user_id': self.crm_lead_id.user_id.id,
                                        'team_id': self.crm_lead_id.team_id.id})
            query_result = self.env.cr.dictfetchone()

            message = False
            if query_result['total_won'] == 1:
                message = _('Go, go, go! Congrats for your first deal.')
            elif query_result['max_team_30'] == self.crm_lead_id.planned_revenue:
                message = _('Boom! Team record for the past 30 days.')
            elif query_result['max_team_7'] == self.crm_lead_id.planned_revenue:
                message = _('Yeah! Deal of the last 7 days for the team.')
            elif query_result['max_user_30'] == self.crm_lead_id.planned_revenue:
                message = _('You just beat your personal record for the past 30 days.')
            elif query_result['max_user_7'] == self.crm_lead_id.planned_revenue:
                message = _('You just beat your personal record for the past 7 days.')
            
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': message,
                        'img_url': '/web/image/%s/%s/image' % (self.crm_lead_id.team_id.user_id._name, self.crm_lead_id.team_id.user_id.id) if self.crm_lead_id.team_id.user_id.image else '/web/static/src/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }

        return True
