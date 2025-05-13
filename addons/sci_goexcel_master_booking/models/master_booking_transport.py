from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo import exceptions
import logging
from odoo.tools import float_round
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FreightMasterBookingTransport(models.Model):
    _name = "freight.master.booking.transport"
    _description = "Master Booking"
    _order = "booking_date desc, write_date desc"
    color = fields.Integer("Color Index", default=0, store=False)
    _inherit = ["mail.thread", "mail.activity.mixin"]

    job_status = fields.Selection(
        [
            ("01", "Draft"),
            ("08", "Pending Bkg"),
            ("02", "Confirmed"),
            ("07", "Reserved"),
            ("03", "Invoiced"),
            ("04", "Paid"),
            ("05", "Done"),
            ("06", "Cancelled"),
        ],
        string="Job Status",
        default="01",
        copy=False,
        track_visibility="onchange",
        store=True,
    )
    master_booking_no = fields.Char(
        string="Master Booking No", copy=False, readonly=True, index=True
    )
    status_date_time = fields.Datetime(
        string="Status Date", track_visibility="onchange"
    )
    # direction = fields.Selection([('import', 'Import'), ('export', 'Export'), ('thailand', 'Thailand'), ('mt', 'MLO MT Repo')], string="Shipment Type", default="export", track_visibility='onchange')
    direction = fields.Selection(
        [("import", "Import"), ("export", "Export")],
        string="Direction",
        default="export",
        track_visibility="onchange",
    )
    vessel_name = fields.Many2one(
        "freight.vessels", string="Vessel Name", track_visibility="onchange"
    )
    voyage_no = fields.Char(string="Voyage No", track_visibility="onchange")
    scn_no = fields.Char(string="SCN No", track_visibility="onchange", copy=False)
    booking_date = fields.Date(
        string="ETA/ETD Date",
        copy=False,
        default=datetime.now().date(),
        track_visibility="onchange",
        index=True,
    )
    # master_booking_no = fields.Char(string='Master Booking No', track_visibility='onchange', copy=False, index=True)
    carrier = fields.Many2one(
        "res.partner", string="Carrier", track_visibility="onchange"
    )
    # obl_no = fields.Char(
    #     string="OBL No", copy=False, track_visibility="onchange", store=True
    # )
    container_qty = fields.Float(
        string="Qty", digits=(8, 0), track_visibility="onchange"
    )
    transhipment1 = fields.Many2one(
        "freight.ports", string="Transhipment 1", track_visibility="onchange"
    )
    transhipment1_eta = fields.Date(
        string="Transhipment 1 ETA", track_visibility="onchange"
    )
    transhipment2 = fields.Many2one(
        "freight.ports", string="Transhipment 2", track_visibility="onchange"
    )
    transhipment2_eta = fields.Date(
        string="Transhipment 2 ETA", track_visibility="onchange"
    )
    # TS - add TEUS
    teus = fields.Float(
        string="TEUS", digits=(8, 0), compute="_compute_teus", store=True, copy=False
    )
    container_product_id = fields.Many2one(
        "product.product", string="Container Type", track_visibility="onchange"
    )

    booking_ids = fields.One2many(
        "freight.booking", "booking_id", string="booking", copy=True, auto_join=True
    )
    # bol_ids = fields.One2many('freight.bol', 'bol_id', string="bol", copy=False,
    #                               auto_join=True)
    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Low"),
            ("2", "Normal"),
            ("3", "High"),
            ("4", "Very High"),
        ],
        string="Priority",
        select=True,
        default="2",
        track_visibility="onchange",
    )
    remark = fields.Text(string="Remarks", track_visibility="onchange")
    owner = fields.Many2one(
        "res.users",
        string="Owner",
        default=lambda self: self.env.user.id,
        track_visibility="onchange",
    )
    sales_person = fields.Many2one(
        "res.users", string="Salesperson", track_visibility="onchange"
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        readonly=1,
        default=lambda self: self.env.user.company_id.id,
    )

    # balance_container = fields.Float(string="Balance Containers", digits=(8,0), track_visibility='onchange',
    #                                  compute="_compute_balance", store=True)
    name = fields.Char(compute="name_get", store=True, readonly=True)

    port_of_loading = fields.Many2one(
        "freight.ports", string="Port of Loading", track_visibility="onchange"
    )
    port_of_discharge = fields.Many2one(
        "freight.ports", string="Port of Discharge", track_visibility="onchange"
    )
    port_of_discharge_eta = fields.Date(
        string="Port of Discharge ETA", track_visibility="onchange"
    )

    scn_code = fields.Char(
        string="SCN Code", track_visibility="onchange", help="Ship Call Number"
    )
    vessel_id = fields.Char(string="Vessel ID", track_visibility="onchange")
    type_code = fields.Many2one("freight.type", string="Type")

    @api.one
    @api.depends("container_qty", "container_product_id")
    def _compute_teus(self):
        if self.container_qty > 0:
            container = ""
            if self.container_product_id:
                container = self.container_product_id.name
                if "20" in container:
                    self.teus = self.container_qty * 1
                elif "40" in container:
                    self.teus = self.container_qty * 2

    # def create_sequence(self, res, type_code, branch_str):
    #
    #     search_sequence = (
    #         branch_str
    #         + type_code
    #         + (self.env["ir.sequence"].next_by_code("master_booking")[0:7] + "%")
    #     )
    #     size = len(search_sequence)
    #     old_sequence = self.env["freight.master.booking.transport"].search(
    #         [("master_booking_no", "=ilike", search_sequence)],
    #         order="create_date desc",
    #         limit=1,
    #     )
    #
    #     if not old_sequence:
    #         sequence = search_sequence[: size - 1]
    #         res["master_booking_no"] = sequence + "-" + "0001"
    #         res["display_name"] = sequence + "-" + "0001"
    #     else:
    #         running_no = int(old_sequence["master_booking_no"].split("-")[2][1:])
    #         current_running_no = str(running_no + 1)
    #         current_running_no = current_running_no.zfill(4)
    #         sequence = search_sequence[: size - 1]
    #         res["master_booking_no"] = sequence + "-" + current_running_no
    #         res["display_name"] = sequence + "-" + current_running_no
    #     return res
    #
    # @api.model
    # def create(self, vals):
    #     branch_id = self.env.user.default_branch.id
    #     if branch_id:
    #         branch = (
    #             self.env["account.analytic.tag"]
    #             .search([("id", "=", branch_id)], limit=1)
    #             .name.upper()
    #         )
    #
    #     else:
    #         branch = ""
    #     if "booking_ids" in vals:
    #         if "type_code" in vals:
    #             for i in range(0, len(vals["booking_ids"])):
    #                 vals["booking_ids"][i][2]["type_code"] = vals["type_code"]
    #     res = super(FreightMasterBookingTransport, self).create(vals)
    #     type_obj = self.env["freight.type"].search(
    #         [("id", "=", vals["type_code"])], limit=1
    #     )
    #     if type_obj:
    #         type_code = type_obj.code
    #
    #     else:
    #         type_code = ""
    #
    #     if branch == "SELANGOR":
    #         branch_str = "B"
    #         res = self.create_sequence(res, type_code, branch_str)
    #     elif branch == "PENANG":
    #         branch_str = "P"
    #         res = self.create_sequence(res, type_code, branch_str)
    #     else:
    #         branch_str = ""
    #         res = self.create_sequence(res, type_code, branch_str)
    #
    #     return res
    #
    # def update_sequence(self, res, type_code, branch_str):
    #
    #     search_sequence = (
    #         branch_str
    #         + type_code
    #         + (self.env["ir.sequence"].next_by_code("master_booking")[0:7] + "%")
    #     )
    #     size = len(search_sequence)
    #     old_sequence = self.env["freight.master.booking.transport"].search(
    #         [("master_booking_no", "=ilike", search_sequence)],
    #         order="create_date desc",
    #         limit=1,
    #     )
    #
    #     if not old_sequence:
    #         sequence = search_sequence[: size - 1]
    #         res["master_booking_no"] = sequence + "-" + "0001"
    #         res["display_name"] = sequence + "-" + "0001"
    #     else:
    #         running_no = int(old_sequence["master_booking_no"].split("-")[2][1:])
    #         current_running_no = str(running_no + 1)
    #         current_running_no = current_running_no.zfill(4)
    #         sequence = search_sequence[: size - 1]
    #         res["master_booking_no"] = sequence + "-" + current_running_no
    #         res["display_name"] = sequence + "-" + current_running_no
    #     return res
    #
    # @api.multi
    # def write(self, values):
    #     if "booking_ids" in values:
    #         if "type_code" in values:
    #             for i in range(0, len(values["booking_ids"])):
    #                 if type(values["booking_ids"][i][2]) is dict:
    #                     values["booking_ids"][i][2]["type_code"] = values["type_code"]
    #
    #         if self.type_code:
    #             for i in range(0, len(values["booking_ids"])):
    #                 if type(values["booking_ids"][i][2]) is dict:
    #                     values["booking_ids"][i][2]["type_code"] = self.type_code.id
    #     res = super(FreightMasterBookingTransport, self).write(values)
    #     if "type_code" in values:
    #
    #         branch_id = self.env.user.default_branch.id
    #         if branch_id:
    #             branch = (
    #                 self.env["account.analytic.tag"]
    #                 .search([("id", "=", branch_id)], limit=1)
    #                 .name.upper()
    #             )
    #
    #         else:
    #             branch = ""
    #
    #         type_obj = self.env["freight.type"].search(
    #             [("id", "=", values["type_code"])], limit=1
    #         )
    #         if type_obj:
    #             type_code = type_obj.code
    #
    #         else:
    #             type_code = ""
    #
    #         if self.booking_ids:
    #             lines_array = []
    #             for line in self.booking_ids:
    #                 line.write(
    #                     {"type_code": type_obj.id,}
    #                 )
    #
    #         if branch == "SELANGOR":
    #             branch_str = "B"
    #             self = self.update_sequence(self, type_code, branch_str)
    #         elif branch == "PENANG":
    #             branch_str = "P"
    #             self = self.update_sequence(self, type_code, branch_str)
    #         else:
    #             branch_str = ""
    #             self = self.update_sequence(self, type_code, branch_str)
    #
    #     return self

    @api.onchange("vessel_name")
    def onchange_vessel_name(self):
        self.vessel_id = self.vessel_name.code

    @api.multi
    def name_get(self):
        result = []
        for transport in self:
            name = str(transport.master_booking_no)
        result.append((transport.id, name))
        return result

    @api.multi
    def action_cancel_master_booking_transport(self):
        self.job_status = "06"

    @api.onchange("voyage_no")
    def _onchange_voyage_no(self):
        # vals = {}
        if self.voyage_no:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.voyage_no = self.voyage_no

    @api.onchange("booking_date")
    def _onchange_booking_date(self):
        # vals = {}
        if self.booking_date:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.booking_date_time = self.booking_date


    @api.onchange("vessel_name")
    def _onchange_vessel_name(self):
        # vals = {}
        if self.vessel_name:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.vessel_name = self.vessel_name

    @api.onchange("vessel_id")
    def _onchange_vessel_id(self):
        # vals = {}
        if self.vessel_id:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.vessel_id = self.vessel_id

    @api.onchange("vessel_name")
    def _onchange_vessel_name(self):
        # vals = {}
        if self.vessel_name:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.vessel_name = self.vessel_name

    @api.onchange("scn_code")
    def _onchange_scn_code(self):
        # vals = {}
        if self.scn_code:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.scn_code = self.scn_code

    @api.onchange("port_of_discharge")
    def _onchange_port_of_discharge(self):
        # vals = {}
        if self.port_of_discharge:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.port_of_discharge = self.port_of_discharge.id


    @api.onchange("port_of_loading")
    def _onchange_port_of_loading(self):
        # vals = {}
        if self.port_of_loading:
            if self.booking_ids:
                for booking in self.booking_ids:
                    # vals['voyage_no'] = self.voyage_no
                    booking.port_of_loading = self.port_of_loading.id


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    sequence = fields.Integer(string="sequence")
    booking_id = fields.Many2one(
        "freight.master.booking.transport",
        string="Split Booking",
        ondelete="cascade",
        index=True,
        copy=True,
    )
    container_qty = fields.Float(
        string="Qty", digits=(8, 0), track_visibility="onchange", copy=False
    )
    bl_status = fields.Selection(
        [
            ("hold", "Hold"),
            ("released", "Released"),
            ("telex", "Telex"),
            ("swb", "SWB"),
        ],
        string="BL Status",
        default="hold",
        track_visibility="onchange",
    )
    billing_address = fields.Many2one(
        "res.partner", string="Billing Party", track_visibility="onchange"
    )
    booking_confirmation_note = fields.Text(
        string="Book. Confirm. Note", track_visibility="onchange"
    )
    note = fields.Text(string="Remarks", track_visibility="onchange")

    master_booking_no = fields.Char(
        string="Master Booking No",
        track_visibility="onchange",
        # compute="_compute_master_booking_no",
        store=True,
    )
    port_of_tranship_2 = fields.Many2one(
        "freight.ports", string="2nd Port of Tranship", track_visibility="onchange"
    )
    port_of_tranship_eta_2 = fields.Date(
        string="2nd Tranship ETA", track_visibility="onchange", copy=False
    )
    port_of_tranship_3 = fields.Many2one(
        "freight.ports", string="3rd Port of Tranship", track_visibility="onchange"
    )
    port_of_tranship_eta_3 = fields.Date(
        string="3rd Tranship ETA", track_visibility="onchange", copy=False
    )
    book_confirm_revised = fields.Boolean(
        string="Revised", copy=False, default=False, track_visibility="onchange"
    )
    booked_date = fields.Date(
        string="Booked Date", track_visibility="onchange", copy=False
    )
    contact_name = fields.Many2one(
        "res.partner", string="Attention", track_visibility="onchange"
    )
    # vgm_done = fields.Boolean(string='VGM', copy=False, track_visibility='onchange')
    intended_si_cut_off = fields.Datetime(
        string="Intended SI Cut Off", track_visibility="onchange"
    )
    intended_si_cut_off_1 = fields.Datetime(
        string="Intended SI Cut Off", track_visibility="onchange"
    )
    # carrier_booking_no = fields.Char(string='MLO Split Booking No', track_visibility='onchange', copy=False)

    # running_no = fields.Char(string='Running No', copy=False, track_visibility='onchange')
    laden_back_terminal2 = fields.Many2one(
        "freight.terminal", string=" Laden Cntr Return To", track_visibility="onchange"
    )
    pick_up_terminal = fields.Many2one(
        "freight.terminal", string="Pick Up Terminal", track_visibility="onchange"
    )
    drop_off_terminal = fields.Many2one(
        "freight.terminal", string="Drop Off Terminal", track_visibility="onchange"
    )
    empty_pick_up_depot = fields.Many2one(
        "transport.depot", string="Empty Pick Up Depot", track_visibility="onchange"
    )
    gate_out_date = fields.Date(string="Gate Out Date", track_visibility="onchange")
    packing_remark = fields.Text(string="Packing Remark")
    place_of_delivery_eta = fields.Date(
        string="Place of Delivery ETA", track_visibility="onchange"
    )
    customer_reference_no = fields.Char(string="Customer Ref. No")
    slot_type = fields.Selection(
        [("df", "DF"), ("ndf", "NDF"), ("os", "OS")], string="Slot Type"
    )
    slot_owner = fields.Many2one(
        "res.partner", string="Slot Owner", domain="[('is_slot_owner', '=', True)]"
    )
    shipment_term = fields.Many2one("shipment.term", string="Shipment Term")
    operator_code = fields.Many2one("operator.code", string="Operator Code")
    billing_port = fields.Many2one("freight.ports", "Billing Port")

    @api.depends("port_of_discharge_eta")
    @api.onchange("port_of_discharge_eta")
    def _onchange_port_of_discharge_eta(self):
        # self.ensure_one()
        for operation in self:
            if operation.port_of_discharge_eta:
                operation.place_of_delivery_eta = operation.port_of_discharge_eta

    @api.depends("vessel_name", "port_of_discharge")
    def _onchange_vessel_pod(self):
        # self.ensure_one()
        for operation in self:
            if operation.booking_id.voyage_no:
                operation.voyage_no = operation.booking_id.voyage_no

    @api.multi
    def name_get(self):
        result = []
        for booking in self:
            name = str(booking.carrier_booking_no) + "-" + str(booking.booking_no)
            result.append((booking.id, name))
        return result

    # TODO - update the sequence
    @api.model
    def create(self, vals):
        # vals["booking_no"] = self.env["ir.sequence"].next_by_code("fb-s")
        res = super(FreightBooking, self).create(vals)
        for rec in res:
            # print('rec.booking_id=' + str(rec.booking_id))
            if rec.booking_id:
                rec.direction = rec.booking_id.direction
                rec.scn_code = rec.booking_id.scn_code

        return res

    @api.onchange("shipment_close_date_time")
    def _onchange_shipment_close_date_time(self):
        if self.shipment_close_date_time:
            self.intended_cy_cut_off = self.shipment_close_date_time

    @api.onchange("port_of_loading")
    def _onchange_port_of_loading(self):
        if self.port_of_loading:
            self.place_of_receipt = self.port_of_loading.name

    @api.onchange("container_qty")
    def _onchange_container_qty(self):
        vals = {}
        # if not self.booking_date_time:
        if self.booking_id.booking_date:
            vals["booking_date_time"] = self.booking_id.booking_date
            # self.update(vals)

        if self.booking_id.voyage_no:
            # print('>>>>>>>>>>>>>> _onchange_container_qty voyage no=', self.booking_id.voyage_no)
            vals["voyage_no"] = self.booking_id.voyage_no
        if self.booking_id.vessel_id:
            vals["vessel_id"] = self.booking_id.vessel_id
        if self.booking_id.scn_code:
            vals["scn_code"] = self.booking_id.scn_code
        if self.booking_id.carrier:
            vals["carrier"] = self.booking_id.carrier.id
            # self.update(vals)
        # if not self.direction:
        if self.booking_id.direction:
            # print('self.booking_id.direction=' + self.booking_id.direction)
            vals["direction"] = self.booking_id.direction

        if self.booking_id.port_of_loading:
            vals["port_of_loading"] = self.booking_id.port_of_loading.id

        # if not self.vessel_name:
        if self.booking_id.vessel_name:
            vals["vessel_name"] = self.booking_id.vessel_name.id

        if self.booking_id.transhipment1:
            vals["port_of_tranship"] = self.booking_id.transhipment1

        if self.booking_id.transhipment1_eta:
            vals["port_of_tranship_eta"] = self.booking_id.transhipment1_eta

        if self.booking_id.transhipment2:
            vals["port_of_tranship_2"] = self.booking_id.transhipment2

        if self.booking_id.transhipment2_eta:
            vals["port_of_tranship_eta_2"] = self.booking_id.transhipment2_eta

        if self.booking_id.port_of_discharge:
            vals["port_of_discharge"] = self.booking_id.port_of_discharge.id

        if self.booking_id.port_of_discharge_eta:
            vals["port_of_discharge_eta"] = self.booking_id.port_of_discharge_eta

        if vals:
            self.update(vals)

    def action_edit_booking_job(self):
        # Returns an action that will open a form view (in a popup)
        self.ensure_one()

        view = self.env.ref("sci_goexcel_freight.view_form_booking")
        return {
            "name": "Edit Booking Job Form",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "freight.booking",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "flags": {"initial_mode": "edit"},
            "target": "current",
            "res_id": self.id,
        }

    @api.onchange("carrier_booking_no")
    def _onchange_carrier_booking_no(self):
        vals = {}
        if self.booking_id.direction:
            # print('carrier booking onchange self.booking_id.direction=' + self.booking_id.direction)
            vals["direction"] = self.booking_id.direction
        if self.booking_id.booking_date:
            if not self.booking_date_time:
                vals["booking_date_time"] = self.booking_id.booking_date
            # self.update(vals)
            # if not self.vessel_name:

        if self.booking_id.voyage_no:
            if not self.voyage_no:
                vals["voyage_no"] = self.booking_id.voyage_no
                # self.write({'voyage_no': self.booking_id.voyage_no})
        if self.booking_id.carrier:
            if not self.carrier:
                vals["carrier"] = self.booking_id.carrier.id

        if self.booking_id.port_of_loading:
            vals["port_of_loading"] = self.booking_id.port_of_loading.id

        if self.booking_id.port_of_discharge:
            vals["port_of_discharge"] = self.booking_id.port_of_discharge.id
        # CR5
        if self.booking_id.vessel_name:
            if not self.vessel_name:
                vals["vessel_name"] = self.booking_id.vessel_name.id

        if vals:
            self.update(vals)

    @api.onchange("operation_line_ids")
    def _onchange_operation_line_ids(self):
        if self.operation_line_ids:
            self.container_qty = len(self.operation_line_ids)


    @api.multi
    def action_copy_job(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_master_booking.copy_booking_wizard_form')
        return {
            'name': 'Copy Job',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'copy.booking.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(booking_id=self.id),
        }


class OperatorCode(models.Model):
    _name = "operator.code"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class ShipmentTerm(models.Model):
    _name = "shipment.term"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class CargoType(models.Model):
    _name = "cargo.type"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class FreightOperationsLine(models.Model):
    _inherit = "freight.operations.line"

    cargo_type = fields.Many2one("cargo.type", string="Cargo Type")
    container_type = fields.Selection(
        [
            ("GP", "GP"),
            ("DG", "DG"),
            ("RF", "RF"),
            ("OOG", "OOG"),
            ("TK", "TK"),
            ("HC", "HC"),
        ],
        string="Type",
    )
    vgm = fields.Float(string="VGM (kg)", digits=(12, 2))
    dg_flash_point = fields.Float(string="DG", digits=(12, 2))
    harmonized_id = fields.Char(string="Harmonized ID")
    temperature = fields.Char(string="Temp.(C)")
    depot_out_req_date = fields.Datetime(string="Depot Out Req Date")
    depot_out_date = fields.Datetime(string="Depot Out Date")
    terminal_in_date = fields.Datetime(string="Terminal In Date")
    vessel_loading_date_time = fields.Datetime(string="Vessel Loading Date Time")

