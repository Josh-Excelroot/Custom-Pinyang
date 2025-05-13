from odoo import models, fields, api
from datetime import datetime, timedelta, date

class VisitResPartner(models.Model):

    _inherit = "res.partner"

    is_prospect = fields.Boolean(string="Is Prospect")
    visit_company_count = fields.Integer(compute="_compute_visit_company_count")
    visit_contact_count = fields.Integer(compute="_compute_visit_contact_count")
    partner_visit_frequency = fields.Selection(
        [
            ("01", "Weekly"),
            ("02", "Bi-Weekly"),
            ("03", "Monthly"),
            ("04", "Bi-Monthly"),
            ("06", "Quarterly"),
            ("07", "Half-Yearly"),
            ("08", "Yearly"),
        ],
        string="Visit Frequency",
    )
    method_visit_ids = fields.Many2many("visit.method", string="Visit Method")
    last_visit = fields.Many2one('visit', compute='_get_last_visit', string='Last Visit')
    last_visit_date = fields.Datetime(related='last_visit.check_in_date_time', string='Last Visit Date')
    last_visit_remark_followup = fields.Text(related='last_visit.remark', string="Last Visit Remark")
    destination = fields.Char(string="Destination", compute="_compute_address")


    # kashif 11 july 23 : added compute code to get partner lat lng first and then address as last
    @api.depends('street','partner_latitude')
    def _compute_address(self):
        for rec in self:
            destination = ""
            if rec.partner_latitude and rec.partner_longitude:
                destination = str(rec.partner_latitude) + ',' + str(rec.partner_longitude)
            elif rec.street and rec.city and rec.country_id:
                if rec.street:
                    destination += rec.street.replace(" ", "%20")
                if rec.street2:
                    destination += "%20" + rec.street2.replace(" ", "%20")
                if rec.city:
                    destination += "%20" + rec.city.replace(" ", "%20")
                if rec.zip:
                    destination += "%20" + rec.zip.replace(" ", "%20")
                if rec.state_id:
                    destination += "%20" + rec.state_id.name.replace(
                        " ", "%20"
                    )
                if rec.country_id:
                    destination += "%20" + rec.country_id.name.replace(
                        " ", "%20"
                    )

            rec.destination = destination

    # end

    def _get_last_visit(self):
        for res in self:
            visit_id = self.env['visit'].search(
                [('customer_name', '=', res.name), ('visit_status', 'in', ['03'])], order="check_in_date_time desc",
                limit=1)
            if visit_id.check_in_date_time:
                res.last_visit = visit_id.id
            else:
                res.last_visit = False

    def _compute_visit_company_count(self):
        for partner in self:
            visits = self.env["visit"].search([("customer_name", "=", partner.id),])
            partner.visit_company_count = len(visits)

    def _compute_visit_contact_count(self):
        for partner in self:
            visits = self.env["visit"].search([("contact", "=", partner.id),])
            partner.visit_contact_count = len(visits)

    def open_save_partner_location(self):
        pass

    @api.model
    def save_partner_location(self, gps_location, record_id):
        partner = self.env["res.partner"].search([("id", "=", record_id)])
        if partner:
            coordinates = [x.strip() for x in gps_location.split(",")]
            partner.partner_latitude = float(coordinates[0])
            partner.partner_longitude = float(coordinates[1])

    def open_partner_map(self):
        pass


    def action_next_create_visit(self):
        for rec in self:
            #current_date = datetime.now()
            #DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
            #date_format = datetime.strptime(str(current_date), DATETIME_FORMAT)
            #visit_frequency = self.partner_visit_frequency
            visit_planned_start_date_time = datetime.utcnow()
            #print('>>>>>>>>>>> action_next_create_visit=', visit_planned_start_date_time)
            wiz = self.env['visit'].create({'customer_name': rec.id})
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
                    "default_last_visit_remark": rec.last_visit_remark_followup,
                    "default_sales_person": rec.env.uid,
                    "default_company_id": rec.company_id.id,
                },
            }
