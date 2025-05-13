from odoo import models, fields, api, _
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)


class Visit(models.Model):
    _name = "visit"
    _description = "Visit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'visit_id'
    _order = "visit_id desc"

    color = fields.Integer("Color Index", default=0)
    is_readonly = fields.Boolean(string="Is Readonly")
    display_name = fields.Char(compute='_compute_display_name')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.visit_id

    @api.model
    def _default_visit_purpose(self):
        visit_purpose = self.env["visit.purpose"].search([("code", "=", "01")])
        return visit_purpose

    @api.depends("customer_name", "contact")
    def _default_last_visit_purpose_spanco(self):
        for res in self:
            if res.contact:
                visit = res.env["visit"].search(
                    [
                        ("contact", "=", res.contact.id),
                        ("check_out_date_time", "!=", False),
                        ("visit_status", "=", "03"),
                    ],
                    order="check_out_date_time desc",
                    limit=1,
                )
                if visit and visit.visit_spanco_ids:
                    res.last_visit_purpose = (
                        visit.visit_spanco_ids[0].visit_spanco_purpose_id.name or ''
                        + "-"
                        + visit.visit_spanco_ids[0].visit_spanco_value_id.name or ''
                    )

                # res.last_visit_purpose = visit_purpose
            elif res.customer_name:
                visit = res.env["visit"].search(
                    [
                        ("customer_name", "=", res.customer_name.id),
                        ("visit_status", "=", "03"),
                        ("check_out_date_time", "!=", False),
                    ],
                    order="check_out_date_time desc",
                    limit=1,
                )
                if visit and visit.visit_spanco_ids:
                    if visit.visit_spanco_ids[0].visit_spanco_purpose_id.name:
                        res.last_visit_purpose = visit.visit_spanco_ids[
                            0
                        ].visit_spanco_purpose_id.name
                    if visit.visit_spanco_ids[0].visit_spanco_value_id.name:
                        res.last_visit_purpose = (
                            res.last_visit_purpose
                            + "-"
                            + visit.visit_spanco_ids[0].visit_spanco_value_id.name
                        )

                    # res.last_visit_purpose = (
                    #     visit.visit_spanco_ids[0].visit_spanco_purpose_id.name
                    #     + "-"
                    #     + visit.visit_spanco_ids[0].visit_spanco_value_id.name
                    # )
                # opp_ids = []
                # opportunity_ids = self.env['crm.lead'].search([('partner_id', '=', res.customer_name.id)],)
                # for line in opportunity_ids:
                #     opp_ids.append(line.id)
                # res.opportunity_list = [(6,0, opp_ids)]
            # visit_purpose = visit.visit_purpose.id
            # self.last_visit_purpose = visit_purpose
        # return visit_purpose

    opportunity_id = fields.Many2one("crm.lead", string="Opportunity", copy=False)
    last_opportunity_stage_id = fields.Many2one('crm.stage',string="Stage")
    visit_status = fields.Selection(
        [("01", "Open"), ("02", "In Process"), ("03", "Done"),],
        copy=False,
        default="01",
    )
    sequence = fields.Integer(string="sequence")
    customer_name = fields.Many2one(
        "res.partner", string="Customer", track_visibility="onchange"
    )
    contact = fields.Many2one(
        "res.partner", string="Contact", track_visibility="onchange"
    )
    visit_purpose = fields.Many2one(
        "visit.purpose",
        default=_default_visit_purpose,
        string="Visit Purpose",
        track_visibility="onchange",
    )

    def _get_current_date_time(self):
        # current_timezone = pytz.timezone(self.env.context.get('tz'))
        # print('>>>>>>>>>>>>> _get_current_date_time tz=', pytz.timezone(self.env.context.get('tz')))
        # Get the current time in UTC, and convert to the Odoo will convert to the user's date time zone.
        current_utc = datetime.utcnow()
        # now_utc = datetime.now(pytz.UTC)
        # now_user = now_utc.astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
        # print('>>>>>>>>>>>>> _get_current_date_time current_utc=', current_utc)
        # print('>>>>>>>>>>>>> _get_current_date_time now_utc=', now_utc)
        # print('>>>>>>>>>>>>> _get_current_date_time now_user=', now_user)

        # now_user_time = pytz.timezone(current_timezone).localize(current_utc)
        # user_datetime = datetime.datetime.now(current_timezone)
        # print('>>>>>>>>>>>>> _get_current_date_time now_user_time=', now_user_time)
        # now_utc = datetime.now(pytz.UTC)
        # now_user = now_utc.astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
        # now= datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%Y-%m-%d %H:%M:%S")
        # print('>>>>>>>>>>>>> _get_current_date_time now=', now)
        return current_utc

    # visit_planned_start_date_time = fields.Datetime(
    #    string="Planned Start Date Time", track_visibility="onchange",default=datetime.today()
    # )
    visit_planned_start_date_time = fields.Datetime(
        string="Planned Start Date Time",
        track_visibility="onchange",
        default=_get_current_date_time,
    )
    visit_planned_end_date_time = fields.Datetime(
        string="Planned End Date Time", track_visibility="onchange"
    )
    sales_person = fields.Many2one(
        "res.users",
        string="Salesperson",
        readonly=True,
        default=lambda self: self.env.user.id,
        track_visibility="onchange",
    )
    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Low"),
            ("2", "Normal"),
            ("3", "High"),
            ("4", "Very High"),
        ],
        string="Priority",
        default="2",
        track_visibility="onchange",
    )
    visit_id = fields.Char(string="Visit ID", copy=False, readonly=True, index=True)
    check_in_date_time = fields.Datetime(
        string="Check In Date & Time", readonly=True, track_visibility="onchange"
    )
    check_out_date_time = fields.Datetime(
        string="Check Out Date & Time", readonly=True, track_visibility="onchange"
    )
    visit_duration = fields.Float(
        string="Visit Duration (min)",
        compute="_compute_visit_duration",
        readonly=True,
        store=True,
        track_visibility="onchange",
    )
    visit_count = fields.Integer(string="Visit Count", default=1, store=True)
    visit_duration_char = fields.Char(
        string="Visit Duration", readonly=True, store=True
    )
    destination = fields.Char(string="Destination", compute="_compute_address")
    partner_latitude = fields.Char(compute="_compute_address")
    partner_longitude = fields.Char(compute="_compute_address")
    current_location = fields.Char(string="Current Location", copy=False)
    check_in_gps_location = fields.Char(
        string="Check In Location", readonly=True, track_visibility="onchange"
    )
    check_out_gps_location = fields.Char(
        string="Check Out Location", readonly=True, track_visibility="onchange"
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        readonly=1,
        default=lambda self: self.env.user.company_id.id,
        track_visibility="onchange",
    )
    last_visit_remark = fields.Text(string="Last Visit Remark", readonly=True)
    remark = fields.Text(string="Remark", track_visibility="onchange")
    visit_reference = fields.Char(
        string="Visit Reference", copy=False, readonly=True, index=True
    )
    next_visit_count = fields.Integer(compute="_compute_next_visit_count", store=True)
    visit_latitude = fields.Float(
        string="WG Latitude", related="customer_name.partner_latitude"
    )
    visit_longitude = fields.Float(
        string="WG Longitude", related="customer_name.partner_longitude"
    )
    visit_display_name = fields.Char(string="WG Name", related="customer_name.name")
    visit_phone = fields.Char(string="Phone", related="customer_name.phone")
    visit_is_company = fields.Boolean(
        string="Is Company", related="customer_name.is_company"
    )
    visit_email = fields.Char(string="Email", related="customer_name.email")
    visit_street = fields.Char(string="Street", related="customer_name.street")
    visit_street2 = fields.Char(string="Street2", related="customer_name.street2")
    visit_zip = fields.Char(string="Postcode", related="customer_name.zip")
    visit_city = fields.Char(string="City", related="customer_name.city")
    visit_country_id = fields.Many2one(
        string="Country", related="customer_name.country_id"
    )
    visit_state_id = fields.Many2one(string="State", related="customer_name.state_id")
    visit_type = fields.Selection(string="Type", related="customer_name.type")
    # visit_image_small = fields.Binary(
    #     string="Small Image", related="customer_name.image_small"
    # )
    # visit_image = fields.Binary(string="Image", related="customer_name.image")
    visit_color = fields.Integer(string="Color", related="customer_name.color")
    # last_visit_purpose = fields.Many2one('visit.purpose', default=lambda self: self._default_last_visit_purpose(), string="Last Visit Purpose")
    last_visit_purpose = fields.Text(
        string="Last Visit Purpose",
        store=True,
        compute=_default_last_visit_purpose_spanco,
    )
    partner_visit_frequency = fields.Selection(string='Customer Visit Frequency',
                                               related='customer_name.partner_visit_frequency', readonly=True)
    last_visit_date = fields.Datetime(string="Last Visit Date", readonly=True)
    gap_day = fields.Integer('Gap Day',
                             compute="_compute_gap_day",
                             readonly="True",
                             store=False)
    visit_outcome = fields.Many2one("visit.outcome", string="Outcome")
    visit_spanco_ids = fields.One2many(
        "visit.spanco.line", "visit_id", string="SPANCO(S)"
    )
    visit_spanco_id = fields.Many2one("visit.spanco", string="SPANCO")
    manager_review = fields.Boolean(
        string="Manager Review", track_visibility="onchange"
    )
    remark_customer = fields.Text(string="Remark Customer", track_visibility="onchange")
    remark_salesman = fields.Text(
        string="Remark SalesPerson", track_visibility="onchange"
    )
    improvement_customer = fields.Text(
        string="Improvement For Customer", track_visibility="onchange"
    )
    improvement_salesperson = fields.Text(
        string="Improvement For SalesPerson", track_visibility="onchange"
    )

    # @api.model
    # def _default_currency(self):
    #     return self.env.user.company_id.currency_id
    #
    # currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
    #                               default=_default_currency, track_visibility='always')
    # outstanding_invoices_amount = fields.Monetary(string="Outstanding Invoices", compute="get_total_outstanding")

    # define the format and sequence of visit ID in the visit_view.xml
    @api.model
    def create(self, vals):
        if vals.get('name'):
            # create from calendar
            vals['remark'] = vals['name']
            del vals['name']
        vals["visit_id"] = self.env["ir.sequence"].next_by_code("visit")
        contact = vals.get("contact")
        customer_name = vals.get("customer_name")
        last_visit_remark = vals.get("last_visit_remark")
        if contact:
            visit = self.env["visit"].search(
                [("contact", "=", contact), ("visit_status", "=", "03")],
                order="check_out_date_time desc",
                limit=1,
            )
        elif customer_name:
            visit = self.env["visit"].search(
                [("customer_name", "=", customer_name), ("visit_status", "=", "03")],
                order="check_out_date_time desc",
                limit=1,
            )
            if visit:
                if visit.remark and not last_visit_remark:
                    vals["last_visit_remark"] = visit.remark
                    vals["last_visit_date"] = visit.check_in_date_time
        res = super(Visit, self).create(vals)  # ERROR invalid field name on model visit
        return res

    # @api.multi
    def write(self, vals):

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        # dt = self.visit_planned_start_date_time.strptime("%Y-%m-%d %H:%M:%S")
        # print('>>>>>> Visit Write=', )
        customer_id = False
        visit_date_time = False
        if "visit_planned_start_date_time" in vals or "customer_name" in vals:
            # print('>>>>>> Visit Write=', vals.get("customer_name"))
            if not vals.get("customer_name"):
                customer_id = self.customer_name.id
            else:
                # print('>>>>>>> vals.get("customer_name")=', vals.get("customer_name"))
                customer_id = vals.get("customer_name")
            if not vals.get("visit_planned_start_date_time"):
                visit_date_time = self.visit_planned_start_date_time
            else:
                visit_date_time = datetime.strptime(vals.get("visit_planned_start_date_time"), DATETIME_FORMAT)
            # print('>>>>>> Visit Write customer id=', customer_id, ' , visit date time=', visit_date_time)
            dt = visit_date_time
            start_date_time = dt.replace(minute=00, hour=00)  # ERROR replace takes no arg
            end_date_time = dt.replace(minute=59, hour=23)
            # print('>>>>>start date time=', start_date_time, ' , end date time=', end_date_time)
            # TS - check if there is existing visit to the same customer, in the same day.
            duplicate_visit = self.env["visit"].search(
                [
                    ("sales_person", "=", self.env.user.id),
                    ("customer_name", "=", customer_id),
                    ("visit_planned_start_date_time", "<=", end_date_time),
                    ("visit_planned_start_date_time", ">=", start_date_time),
                ]
            )
            # print('>>>>>duplicate_visi=', duplicate_visit)
            if duplicate_visit and len(duplicate_visit) > 0:
                for visit in duplicate_visit:
                    if visit.id != self.id:
                        raise UserError(
                            _(
                                "You already have a Visit to %s on the same day, Visit %s"
                            )
                            % (visit.customer_name.name, visit.visit_id)
                        )
        res = super(Visit, self).write(vals)
        return res

    @api.onchange("opportunity_id")
    def _onchange_opportunity_id(self):
        if self.opportunity_id and self.opportunity_id.stage_id:
            visit_spanco = self.env["visit.spanco"].search(
                [("stage", "=", self.opportunity_id.stage_id.id)], limit=1
            )
            if visit_spanco:
                self.visit_spanco_id = visit_spanco.id

    # @api.multi
    def action_check_in(self):
        if not self.customer_name:
            raise ValidationError(_("Please Select Customer"))
        count = 0
        check_ids = self.env["visit"].search(
            [("sales_person", "=", self.sales_person.id)]
        )
        for i in check_ids:
            if i.check_in_date_time and not i.check_out_date_time:
                count = 1
        if count == 1:
            raise ValidationError(_("Please Checkout from Last Visit"))

        self.visit_status = "02"
        self.check_in_date_time = datetime.today()
        self.last_visit_date = self.check_in_date_time

    # @api.multi
    def action_check_out(self):
        if not self.check_in_date_time:
            raise ValidationError(_("You can't check out without check-in"))

        self.visit_status = "03"
        self.check_out_date_time = datetime.today()
        t1 = self.check_out_date_time - self.check_in_date_time
        t2 = t1.total_seconds()
        self.visit_duration = float(t2 / 60)
        days = int(t2 / 86400)
        print(days)
        daysinmin = days * 1440
        mins = int((t2 / 60) - daysinmin)
        duration = ""
        if days > 0:
            duration = duration + str(days) + " day(s) "
        if mins > 0:
            duration = duration + str(mins) + " min(s) "
        if days == 0 and mins == 0:
            duration = "0"
        self.visit_duration_char = duration
        self.is_readonly = True

        return self

    @api.depends("last_visit_date")
    def _compute_gap_day(self):
        self.customer_visit_frequency = self.customer_name.partner_visit_frequency
        if self.last_visit_date:
            total_days = datetime.today() - self.last_visit_date
            self.gap_day = total_days.days
        else:
            self.gap_day = 0

    # @api.multi
    def run_visit_notify(self):
        visit_records = self.env["visit"].search(
            [
                ("visit_status", "=", "01"),
                ("visit_planned_start_date_time", "!=", False),
                ("check_in_date_time", "=", False),
            ]
        )
        for record in visit_records:

            if (
                not record.check_in_date_time
                and datetime.today() > record.visit_planned_start_date_time
            ):
                user_name = user = ""
                if record.customer_name:
                    user_name = record.customer_name.name
                    user = record.customer_name.id
                if record.contact:
                    user_name = record.contact.name
                    user = record.contact.id

                body_text = (
                    """<p>Dear Sir/Madam <br/>You have Not yet checked in to preplanned visit %s </p><br/>"""
                    % (user_name)
                )

                body_html = _(body_text)
                recipient_ids = [user]

                if datetime.today() > record.visit_planned_start_date_time + timedelta(
                    hours=record.sales_person.notify_time
                ):
                    mail = (
                        self.env["mail.mail"]
                        .sudo()
                        .create(
                            {
                                "subject": "Visit Pending",
                                "body_html": body_html,
                                "notification": True,
                                "state": "outgoing",
                                "recipient_ids": recipient_ids,
                                # 'attachment_ids': [(6, 0, attachment_ids)],
                            }
                        )
                    )
                    mail.send()
                return True

    # @api.multi
    def action_reset_status(self):
        self.visit_status = "01"
        self.check_in_date_time = ""
        self.check_out_date_time = ""
        self.visit_duration = ""
        self.visit_duration_char = ""
        self.is_readonly = False

    # @api.multi
    def name_get(self):
        result = []
        for visit in self:
            name = str(visit.visit_id)
        result.append((visit.id, name))
        return result

    # @api.one
    @api.depends("check_out_date_time")
    def _compute_visit_duration(self):
        for rec in self:
            if rec.check_in_date_time and rec.check_out_date_time:
                t1 = rec.check_out_date_time - rec.check_in_date_time
                t2 = t1.total_seconds()
                rec.visit_duration = float(t2 / 60)

    # @api.multi
    def _compute_next_visit_count(self):
        for visit in self:
            next_visit = self.env["visit"].search(
                [("visit_reference", "=", visit.visit_id)]
            )
            visit.next_visit_count = len(next_visit)

    # @api.multi
    def action_next_visit(self):
        if self:
            current_date = datetime.now()
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
            date_format = current_date
            visit_frequency = self.customer_name.partner_visit_frequency
            if visit_frequency:
                if visit_frequency == "01":
                    visit_planned_start_date_time = date_format + timedelta(days=7)
                if visit_frequency == "02":
                    visit_planned_start_date_time = date_format + timedelta(days=14)
                if visit_frequency == "03":
                    visit_planned_start_date_time = date_format + relativedelta(
                        months=1
                    )
                if visit_frequency == "04":
                    visit_planned_start_date_time = date_format + relativedelta(
                        months=2
                    )
                if visit_frequency == "06":
                    visit_planned_start_date_time = date_format + relativedelta(
                        months=3
                    )
                if visit_frequency == "07":
                    visit_planned_start_date_time = date_format + relativedelta(
                        months=6
                    )
                if visit_frequency == "08":
                    visit_planned_start_date_time = date_format + relativedelta(years=1)
            else:
                visit_planned_start_date_time = ""

            return {
                "name": "Create Next Visit",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "visit",
                "target": "new",
                "context": {
                    "default_customer_name": self.customer_name.id,
                    "default_contact": self.contact.id,
                    "default_visit_purpose": self.visit_purpose.id,
                    "default_visit_planned_start_date_time": visit_planned_start_date_time,
                    "default_priority": self.priority,
                    "default_last_visit_remark": self.remark,
                    "default_sales_person": self.sales_person.id,
                    "default_company_id": self.company_id.id,
                    "default_destination": self.destination,
                    "default_visit_reference": self.visit_id,
                },
            }

    @api.model
    def update_check_in_location(self, gps_location, record_id):
        # context = self.env.context
        visits = self.env["visit"].search([("id", "=", record_id)])
        for visit in visits:
            if visit.customer_name:
                visit.check_in_gps_location = gps_location
                if visit.customer_name.partner_latitude:
                    return
                else:
                    coordinates = [x.strip() for x in gps_location.split(",")]
                    visit.customer_name.partner_latitude = float(coordinates[0])
                    visit.customer_name.partner_longitude = float(coordinates[1])

    @api.model
    def update_check_out_location(self, gps_location, record_id):
        visits = self.env["visit"].search([("id", "=", record_id)])
        for visit in visits:
            visit.check_out_gps_location = gps_location

    # @api.multi
    def open_customer_map(self):
        if self.partner_latitude and self.partner_longitude:
            url = "https://maps.google.com/?q=" + self.partner_latitude + ',' + self.partner_longitude
            return {"type": "ir.actions.act_url", "target": "new", "url": url}

    @api.model
    def save_customer_location(self, gps_location, record_id):
        visits = self.env["visit"].search([("id", "=", record_id)])
        for visit in visits:
            if visit.customer_name:
                coordinates = [x.strip() for x in gps_location.split(",")]
                visit.customer_name.partner_latitude = float(coordinates[0])
                visit.customer_name.partner_longitude = float(coordinates[1])

    # @api.multi
    def open_save_customer_location(self):
        pass

    # @api.multi
    def open_check_in_location(self):
        if self.check_in_gps_location:
            url = "https://maps.google.com/?q=" + self.check_in_gps_location
            return {"type": "ir.actions.act_url", "target": "new", "url": url}

    # @api.multi
    def open_check_out_location(self):
        if self.check_out_gps_location:
            url = "https://maps.google.com/?q=" + self.check_out_gps_location
            return {"type": "ir.actions.act_url", "target": "new", "url": url}

    # @api.one
    def _compute_address(self):
        destination,lat,long = "","",""
        if self.customer_name:
            if self.customer_name.street:
                destination += self.customer_name.street.replace(" ", "%20")
            if self.customer_name.street2:
                destination += "%20" + self.customer_name.street2.replace(" ", "%20")
            if self.customer_name.city:
                destination += "%20" + self.customer_name.city.replace(" ", "%20")
            if self.customer_name.zip:
                destination += "%20" + self.customer_name.zip.replace(" ", "%20")
            if self.customer_name.state_id:
                destination += "%20" + self.customer_name.state_id.name.replace(
                    " ", "%20"
                )
            if self.customer_name.country_id:
                destination += "%20" + self.customer_name.country_id.name.replace(
                    " ", "%20"
                )
            if self.customer_name.partner_latitude and self.customer_name.partner_longitude:
                lat = self.customer_name.partner_latitude
                long = self.customer_name.partner_longitude
        self.destination = destination
        self.partner_latitude = lat
        self.partner_longitude = long

    @api.onchange("visit_planned_start_date_time")
    def _onchange_visit_planned_start_date_time(self):
        if self.visit_planned_start_date_time:
            # print('>>>>>>>>>> _onchange_visit_planned_start_date_time=', self.visit_planned_start_date_time.date())
            # DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            # visit_planned_start_date_time = datetime.strptime(
            #     str(self.visit_planned_start_date_time), DATETIME_FORMAT
            # )
            visit_planned_start_date_time_1 = self.visit_planned_start_date_time
            self.visit_planned_end_date_time = visit_planned_start_date_time_1 + timedelta(minutes=30)

            # dt = self.visit_planned_start_date_time.strptime("%Y-%m-%d %H:%M:%S")
            # dt = datetime.strptime(
            #     str(self.visit_planned_start_date_time), DATETIME_FORMAT
            # )
            # start_date_time = dt.replace(minute=00, hour=00)
            # end_date_time = dt.replace(minute=59, hour=23)
            # # TS - check if there is existing visit to the same customer, in the same day.
            # duplicate_visit = self.env["visit"].search(
            #     [
            #         ("sales_person", "=", self.env.user.id),
            #         ("customer_name", "=", self.customer_name.id),
            #         ("visit_planned_start_date_time", "<=", end_date_time),
            #         ("visit_planned_start_date_time", ">=", start_date_time),
            #     ]
            # )
            # if duplicate_visit and len(duplicate_visit) > 1:
            #     for visit in duplicate_visit:
            #         if visit.id != self._origin.id:
            #             raise UserError(
            #                 _(
            #                     "You already have a Visit to %s on the same day, Visit %s"
            #                 )
            #                 % (visit.customer_name.name, visit.visit_id)
            #             )

    # @api.multi
    def view_next_visit(self):
        next_visit = self.env["visit"].search(
            [("visit_reference", "=", self.visit_id),]
        )
        print(next_visit)
        if len(next_visit) > 1:
            views = [
                (self.env.ref("goexcel_visit.view_tree_visit").id, "tree"),
                (self.env.ref("goexcel_visit.view_form_visit").id, "form"),
            ]
            return {
                "view_type": "form",
                "view_mode": "tree,form",
                "view_id": False,
                "res_model": "visit",
                "views": views,
                "domain": [("id", "in", next_visit.ids)],
                "type": "ir.actions.act_window",
            }
        else:
            return {
                "view_type": "form",
                "view_mode": "form",
                "res_model": "visit",
                "res_id": next_visit.id or False,
                "type": "ir.actions.act_window",
                "target": "popup",
            }

    # @api.multi
    def action_prospect_creation(self):
        pass
        self.ensure_one()
        view = self.env.ref("goexcel_visit.prospect_creation_view_form")
        return {
            "name": "Create Prospect",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "prospect.creation.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
        }

    def action_create_new_sale_order(self):
        for rec in self:
            so = self.env['sale.order'].create({
                'partner_id': rec.customer_name.id,
                "user_id": rec.sales_person.id or rec.env.uid,
                "company_id": rec.company_id.id,
            })
            return {
                "name": "Create New SO",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "sale.order",
                "target": "new",
                'res_id': so.id,
            }

    def action_create_new_opportunity(self):
        for rec in self:
            opportunity = self.env['crm.lead'].create({
                'name': f'Opportunity on {rec.visit_id}',
                'partner_id': rec.customer_name.id,
                "user_id": rec.sales_person.id or rec.env.uid,
                "company_id": rec.company_id.id,
                "visit_id": rec.id,
            })
            rec.opportunity_id = opportunity.id
            return {
                "name": "Create New Opportunity",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "crm.lead",
                "target": "new",
                'res_id': opportunity.id,
            }

    def action_create_new_opportunity(self):
        for rec in self:
            # kashif 14nov23: added type Opertunity in visit opertunity create button
            wiz = self.env['crm.lead'].create(
                {'partner_id': rec.customer_name.id,
                 "name": rec.customer_name.name,
                 "user_id": rec.env.uid,
                 "company_id": rec.company_id.id,
                 "type": "opportunity",
                 })
            if wiz:
                self.opportunity_id = wiz.id
                self.last_opportunity_stage_id = wiz.stage_id.id
            return {
                "name": "Create New Opportunity",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "crm.lead",
                "target": "new",
                'res_id': wiz.id,
                "context": {},
            }