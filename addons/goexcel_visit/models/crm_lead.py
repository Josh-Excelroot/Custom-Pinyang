from odoo import models, fields, api
from datetime import datetime, timedelta, date


class VisitCrmLead(models.Model):
    _inherit = "crm.lead"

    visit_id = fields.Many2one('visit')

    def action_create_opportunity_visit(self):
        for rec in self:
            visit_planned_start_date_time = datetime.utcnow()
            wiz = self.env['visit'].create({'customer_name': rec.partner_id.id, 'opportunity_id': rec.id})
            rec.visit_id = wiz.id
            return {
                "name": "Create Next Visit",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "visit",
                "target": "new",
                'res_id': wiz.id,
                "context": {
                    "default_visit_planned_start_date_time": visit_planned_start_date_time,
                    "default_last_visit_remark": rec.partner_id.last_visit_remark_followup,
                    "default_sales_person": rec.user_id.id,
                    "default_company_id": rec.company_id.id,
                },
            }
