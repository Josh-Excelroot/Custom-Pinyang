from odoo import models, fields, api
from datetime import datetime, timedelta, date

class VisitSaleOrder(models.Model):

    _inherit = "sale.order"

    def action_create_order_visit(self):
        for rec in self:
            visit_planned_start_date_time = datetime.utcnow()
            wiz = self.env['visit'].create({'customer_name': rec.partner_id.id})
            return {
                "name": "Create Next Visit",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "visit",
                "target": "new",
                'res_id': wiz.id,
                #'context': self.env.context,
                "context": {
                    #"default_customer_name": rec.id,
                    #"default_contact": self.contact.id,
                    #"default_visit_purpose": self.visit_purpose.id,
                    "default_visit_planned_start_date_time": visit_planned_start_date_time,
                    #"default_priority": self.priority,
                    "default_last_visit_remark": rec.partner_id.last_visit_remark_followup,
                    "default_sales_person": rec.env.uid,
                    "default_company_id": rec.company_id.id,
                },
            }