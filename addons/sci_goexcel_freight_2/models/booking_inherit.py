from odoo import api, fields, models,exceptions,_
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import float_round
from datetime import datetime, timedelta
import base64
from odoo.exceptions import UserError

class DeliveryService(models.Model):
    _name = 'delivery.service'
    _description = 'Delivery Service Options'
    _order = 'sequence, name'

    name = fields.Char(string='Service Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


class FreightBooking2(models.Model):
    _inherit = "freight.booking"

    cust_ref = fields.Char(string='Customer Reference', copy=False)
    bl_status = fields.Selection([('original', 'Original'),
                                  ('seaway', 'Seaway'),
                                  ('telex', 'Telex')],
                                 string="BL Status", track_visibility='onchange')
    booking_invoice_lines_ids = fields.One2many('booking.invoice.line', 'booking_id', string="Booking Invoices",
                                                copy=True, auto_join=True, track_visibility='always')
    inv_sales = fields.Float(string='Inv. Sales')
    inv_cost = fields.Float(string='Inv. Cost')
    inv_profit = fields.Float(string='Inv. Profit')
    diff_amount = fields.Float(string='Diff. Sales Amount')
    diff_cost_amount = fields.Float(string='Diff. Cost Amount')
    pivot_sale_total = fields.Float(string='Total Sales', compute="_compute_pivot_sale_total_new", store=True)
    pivot_cost_total = fields.Float(string='Total Cost', compute="_compute_pivot_cost_total_new", store=True)
    pivot_profit_total = fields.Float(string='Total Profit', compute="_compute_pivot_profit_total_new", store=True)
    pivot_margin_total = fields.Float(string='Margin %', compute="_compute_pivot_margin_total_new", digit=(8, 2),
                                      store=True, group_operator="avg")
    container_qty = fields.Float(string="Ctnr Qty", digits=(8, 0), track_visibility='onchange', default=0, copy=False)
    container_product_id = fields.Many2one('product.product', string='Container Type', track_visibility='onchange',
                                           copy=False)
    place_of_delivery_eta = fields.Date(string='Place of Delivery ETA', track_visibility='onchange')
    teus = fields.Float(string="TEUS", digits=(8, 0), compute="_compute_teus", store=True, copy=False)
    lcl_consolidation = fields.Boolean(string='LCL Consolidation', default=False)
    po_number = fields.Char(string='PO No')
    bill_status = fields.Selection([('01', 'New'),
                                    ('02', 'Partially Invoiced'),
                                    ('03', 'Fully Invoiced')],
                                   string="Bill Status", default="01", copy=False,
                                   track_visibility='onchange')
    bill_paid_status = fields.Selection([('01', 'New'),
                                         ('02', 'Partially Paid'),
                                         ('03', 'Fully Paid')],
                                        string="Bill Paid Status", default="01", copy=False,
                                        track_visibility='onchange')
    coloader_reference_no = fields.Char(string='Coloader Ref. No', copy=False)
    booking_type = fields.Selection([('T', 'TOTAL PACKAGE'), ('F', 'FREIGHT ONLY'),('H', 'HAULAGE ONLY'),
                                     ('C', 'FORWARDING ONLY'),('D', 'HAULAGE & FORWARDING'),('I', 'INSURANCE'),
                                     ('FLE', 'FLEXI BAG'),('A', 'AGENT'),('CF', 'SUBMIT CUSTOM FORM ONLY')],
                                    string='Job Type', readonly=False)
    status_transhipment = fields.Selection(related='shipment_booking_status', copy=False, string="Transhipment Status")
    #operator_code = fields.Many2one("operator.code", string="Operator Code")
    #kashif 5july23 : make below field copy=false so it will not create double refrence issue
    operation_line_ids_3 = fields.One2many(
        "freight.operations.line2",
        "operation_id2",
        string="FCL Order",
        copy=False,
        auto_join=True,
        track_visibility="always",
    )
    #end
    # @api.multi
    # def _get_default_depot_name(self):
    #     for op in self:
    #         if op.depot_name:
    #             return op.depot_name

    depot_name1 = fields.Many2one('transport.depot', string='Depot Name', track_visibility='onchange')
    pick_up_mode = fields.Selection([('01', 'Road'),
                                     ('02', 'Rail'),
                                     ('03', 'Barge')],
                                    string="Pick Up Mode ", default="01", copy=False,
                                    track_visibility='onchange')
    custom_clearance = fields.Boolean(string='Include Custom Clearance?', track_visibility='onchange', default=True)
    type_of_movement = fields.Selection(
        [('cy-cy', 'CY/CY'), ('cy-cfs', 'CY/CFS'), ('cfs-cfs', 'CFS/CFS'), ('cfs-cy', 'CFS/CY'), ('cy-ramp', 'CY-RAMP'),
         ('cy-sd', 'CY-SD')],
        string='Type Of Movement', track_visibility='onchange')
    intended_si_cut_off = fields.Datetime(string='Intended SI Cut Off', track_visibility='onchange')
    intended_bl_cut_off = fields.Datetime(string='Intended BL Cut Off', track_visibility='onchange')
    port_of_tranship_2 = fields.Many2one('freight.ports', string='Port of Tranship 2', track_visibility='onchange')
    tranship_3 = fields.Boolean(string='Tranship 3')
    port_of_tranship_3 = fields.Many2one('freight.ports', string='Port of Tranship 3', track_visibility='onchange')
    port_of_tranship_eta_2 = fields.Date(string='Tranship ETA 2', track_visibility='onchange', copy=False)
    port_of_tranship_eta_3 = fields.Date(string='Tranship ETA 3', track_visibility='onchange', copy=False)
    costing_date = fields.Date(string='Costing Date', track_visibility='onchange', copy=False)
    service_contract_no = fields.Char(string='Service Contract No', track_visibility='onchange')
    booking_no = fields.Char(string='Booking No', readonly=False)

    delivery_service_ids = fields.Many2many(
        'delivery.service',
        'booking_delivery_service_rel',
        'booking_id',
        'service_id',
        string='Delivery Services',
        help="Select the delivery services required for this booking"
    )

    # ////////////////////////////////////////////////////////////////
    # Josh 07052025: Edit copy/duplicate button function
    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'vendor_bill_count': 0,
        })
        return super(FreightBooking2, self).copy(default)

    # ////////////////////////////////////////////////////////////////
    # Josh 18042025: Add onchange function for port of receipt and discharge
    @api.onchange('port_of_loading')
    def _onchange_port_of_loading(self):
        if self.port_of_loading and self.port_of_loading.name:
            if isinstance(self.port_of_loading.name, str):
                if self.port_of_loading.country_id:
                    self.place_of_receipt = self.port_of_loading.name.upper() + ', ' + self.port_of_loading.country_id.name.upper()
                else:
                    self.place_of_receipt = self.port_of_loading.name.upper()
            else:
                self.place_of_receipt = str(self.port_of_loading.name)
        else:
            self.place_of_receipt = False

    @api.onchange('port_of_discharge')
    def _onchange_port_of_discharge(self):
        if self.port_of_discharge and self.port_of_discharge.name:
            if isinstance(self.port_of_discharge.name, str):
                if self.port_of_discharge.country_id:
                    self.place_of_delivery = self.port_of_discharge.name.upper() + ', ' + self.port_of_discharge.country_id.name.upper()
                else:
                    self.place_of_delivery = self.port_of_discharge.name.upper()
            else:
                self.place_of_delivery = str(self.port_of_discharge.name)
        else:
            self.place_of_delivery = False


    # ////////////////////////////////////////////////////////////////
    twb_count = fields.Integer(string='TWB Count', compute='_compute_twb_count')

    def _compute_twb_count(self):
        for booking in self:
            twbs = self.env['freight.bol'].search([
                ('booking_ref', '=', booking.id),
                ('service_type', '=', 'land')
            ])
            booking.twb_count = len(twbs)

    def action_create_twb(self):
        _logger.info('Creating TWB...')
        sequence = self.env['ir.sequence'].sudo().next_by_code('truck.waybill.sequence')

        _logger.info('Got sequence: %s', sequence)

        if not sequence:
            # If sequence not found, try creating it
            _logger.warning('Sequence not found, creating...')
            self.env['ir.sequence'].sudo().create({
                'name': 'Truck Way Bill Sequence',
                'code': 'truck.waybill.sequence',
                'prefix': 'TWB-%(y)s%(month)s%(day)s-',
                'padding': 2,
            })
            sequence = self.env['ir.sequence'].sudo().next_by_code('truck.waybill.sequence')
            _logger.info('Created sequence: %s', sequence)

        if not sequence:
            raise UserError(_('Could not generate TWB number. Please check sequence configuration.'))

        bol_obj = self.env['freight.bol']

        # Get values from booking for TWB creation
        bol_val = {
            'display_name': sequence,
            'sn_no':sequence,
            'bol_no': sequence,
            'date_of_issue': fields.Date.today(),  # Set issue date
            'date_laden_on_board': self.booking_date_time,  # Set border transfer date
            'port_of_loading_input': self.pickup_from_address_input or '',
            'port_of_discharge_input': self.delivery_to_address_input or '',
            # BL Information
            'company_id': self.company_id.id,
            'service_type': self.service_type,
            'direction': self.direction,
            'cargo_type': self.cargo_type,
            'type_of_movement': self.type_of_movement,
            'booking_ref': self.id,
            # 'booking_date': self.booking_date_time,
            'carrier_booking_no': self.carrier_booking_no,
            'no_of_original_bl': '0',  # Default for TWB
            'invoice_status': self.invoice_status,
            'invoice_paid_status': self.invoice_paid_status,
            'bl_status': self.bl_status,
            'freight_type': self.freight_type,
            'term': self.payment_term.id if self.payment_term else False,

            # Customer Information
            'customer_name': self.customer_name.id,
            'contact_name': self.contact_name.id,
            'notify_party': self.notify_party.id,
            'carrier_c': self.carrier.id,
            'oversea_agent': self.oversea_agent.id,
            'shipper_id': self.shipper.id,
            'shipper': self.shipper_address_input,
            'consignee_id': self.consignee.id,
            'consignee': self.consignee_address_input,

            # Pickup/Delivery Information
            'place_of_receipt': self.pickup_from_address_input,
            'place_of_delivery': self.delivery_to_address_input,

            # Additional Fields
            'sales_person': self.sales_person.id,
            'analytic_account_id': self.analytic_account_id.id,
            'note': self.note,
        }

        # Create BOL record
        bol = bol_obj.create(bol_val)

        # Copy manifest lines (cargo_line_ids)
        operation_lines = self.operation_line_ids2 if self.cargo_type == 'lcl' else self.operation_line_ids
        for line in operation_lines:
            if line.container_product_name or line.container_no or line.exp_vol > 0:
                bol_line_obj = self.env['freight.bol.cargo']
                vals = {
                    'cargo_line': bol.id,
                    'marks': line.remark or '',
                    'container_no': line.container_no or '',
                    'seal_no': line.seal_no or '',
                    'container_product_id': line.container_product_id.id if line.container_product_id else False,
                    'container_product_name': line.container_product_name or '',
                    'packages_no': str(line.packages_no) + ' ' + str(
                        line.packages_no_uom.name) if line.packages_no and line.packages_no_uom else '',
                    'packages_no_value': line.packages_no or 0.0,
                    'packages_no_uom': line.packages_no_uom.id if line.packages_no_uom else False,
                    'exp_gross_weight': line.exp_gross_weight or 0.0,
                    'exp_net_weight': line.exp_net_weight or 0.0,
                    'exp_vol': line.exp_vol or 0.0,
                }
                bol_line = bol_line_obj.create(vals)
                bol.write({'cargo_line_ids': [(4, bol_line.id)]})

        # Copy cost & profit lines
        for line in self.cost_profit_ids:
            vals = {
                'bol_id': bol.id,
                'product_id': line.product_id.id,
                'product_name': line.product_name,
                'uom_id': line.uom_id.id if line.uom_id else False,
                'cost_price': line.cost_price,
                'cost_qty': line.cost_qty,
                'cost_currency': line.cost_currency.id if line.cost_currency else False,
                'cost_currency_rate': line.cost_currency_rate,
                'cost_amount': line.cost_amount,
                'vendor_id': line.vendor_id.id if line.vendor_id else False,
            }
            self.env['freight.bol.cost.profit'].create(vals)

        return {
            'name': 'Trucking Way Bill',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.bol',
            'res_id': bol.id,
            'type': 'ir.actions.act_window',
        }


    def action_view_twb(self):
        self.ensure_one()
        twbs = self.env['freight.bol'].search([
            ('booking_ref', '=', self.id),
            ('service_type', '=', 'land')
        ])
        action = {
            'name': 'Truck Way Bills',
            'view_mode': 'tree,form',
            'res_model': 'freight.bol',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', twbs.ids)]
        }
        if len(twbs) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': twbs.id
            })
        return action


    # ////////////////////////////////////////////////////////////////
    awb_count = fields.Integer(string="AWB Count", compute="_get_awb_count", copy=False)

    def _get_awb_count(self):
        for operation in self:
            bol = self.env["freight.bol"].search([("booking_ref", "=", operation.id), ])

        self.update(
            {"awb_count": len(bol), }
        )

    @api.multi
    def operation_awb(self):
        for operation in self:
            bol = self.env["freight.bol"].search([("booking_ref", "=", operation.id)])

        if len(bol) > 1:
            views = [
                (self.env.ref("sci_goexcel_freight.view_tree_bol").id, "tree"),
                (self.env.ref("sci_goexcel_freight.view_form_bol").id, "form"),
            ]
            return {
                "name": "Bill Of Lading",
                "view_type": "form",
                "view_mode": "tree,form",
                "view_id": False,
                "res_model": "freight.bol",
                "views": views,
                "domain": [("id", "in", bol.ids)],
                "type": "ir.actions.act_window",
            }
        elif len(bol) == 1:
            return {
                "view_type": "form",
                "view_mode": "form",
                "res_model": "freight.bol",
                "res_id": bol.id or False,
                "type": "ir.actions.act_window",
                "target": "popup",  # readonly mode
            }
        else:
            action = {"type": "ir.actions.act_window_close"}
            return action

    def action_create_awb(self):
        if self.service_type == 'air':
            # _logger.warning('export and ocean')
            # _logger.warning('si id=' + str(si.id))
            if self.cargo_type :
                oversea_agent_adr = ''
                if self.oversea_agent:
                    oversea_agent_adr += self.oversea_agent.name + "\n"
                    if self.oversea_agent.street:
                        oversea_agent_adr += self.oversea_agent.street
                    if self.oversea_agent.street2:
                        oversea_agent_adr += ' ' + self.oversea_agent.street2
                    if self.oversea_agent.zip:
                        oversea_agent_adr += ' ' + self.oversea_agent.zip
                    if self.oversea_agent.city:
                        oversea_agent_adr += ' ' + self.oversea_agent.city
                    if self.oversea_agent.state_id:
                        oversea_agent_adr += ', ' + self.oversea_agent.state_id.name
                    if self.oversea_agent.country_id:
                        oversea_agent_adr += ', ' + self.oversea_agent.country_id.name + "\n"
                    if not self.oversea_agent.country_id:
                        oversea_agent_adr += "\n"
                    if self.oversea_agent.phone:
                        oversea_agent_adr += 'Phone: ' + self.oversea_agent.phone
                    elif self.oversea_agent.email:
                        oversea_agent_adr += '. Email: ' + self.oversea_agent.email

                bol_obj = self.env['freight.bol']
                bol_val = {
                    'bol_status': self.bol_status or '01',
                    'no_of_original_bl': self.no_of_original_bl or '0',
                    'direction': self.direction or False,
                    'cargo_type': self.cargo_type or False,
                    'service_type': self.service_type or False,
                    'booking_date': self.booking_date_time,
                    # 'customer_name': self.customer_name.id or False,
                    # 'contact_name': self.contact_name.id or False,
                    # 'shipper': self.shipper_address_input,
                    # 'consignee': self.consignee_address_input,
                    # 'notify_party': self.notify_party_address_input,
                    'booking_ref': self.id,
                    'carrier_booking_no': self.carrier_booking_no,
                    'voyage_no': self.voyage_no,
                    'vessel': self.vessel_name.name,
                    'feeder_voyage_no': self.feeder_voyage_no,
                    'pre_carriage_by': self.feeder_vessel_name,
                    'port_of_loading_input': self.port_of_loading.name,
                    'port_of_discharge_input': self.port_of_discharge.name,
                    'port_of_discharge_eta': self.port_of_discharge_eta,
                    'place_of_delivery': self.place_of_delivery,
                    'term': self.payment_term.name,
                    'analytic_account_id': self.analytic_account_id.id or False,
                    'sales_person': self.sales_person.id or False,
                    'shipping_agent_code': self.shipping_agent_code or False,
                    'oversea_agent': self.oversea_agent.id or False,
                    'routing_instruction': oversea_agent_adr,
                    # 'consignee_c': self.consignee.id or False,
                    # 'notify_party_c': self.notify_party.id or False,
                    'carrier_c': self.carrier.id or False,
                    'commodity1': self.commodity1.id or False,
                    'port_of_tranship_input': self.port_of_tranship.name,
                    'port_of_tranship_eta': self.port_of_tranship_eta,
                    'shipment_close_date_time': self.shipment_close_date_time,
                    'carrier': self.carrier.id,
                    'air_agent': self.air_agent.id,
                    'airport_departure': self.airport_departure.id,
                    'airport_destination': self.airport_destination.id,
                    'first_carrier_to': self.first_carrier_to.id,
                    'first_carrier_flight_no': self.first_carrier_flight_no.id,
                    'first_carrier_etd': self.first_carrier_etd,
                    'first_carrier_eta': self.first_carrier_eta,
                    'second_carrier_to': self.second_carrier_to.id,
                    'second_carrier_flight_no': self.second_carrier_flight_no.id,
                    'second_carrier_etd': self.second_carrier_etd,
                    'second_carrier_eta': self.second_carrier_eta,
                    'third_carrier_to': self.third_carrier_to.id,
                    'third_carrier_flight_no': self.third_carrier_flight_no.id,
                    'third_carrier_etd': self.third_carrier_etd,
                    'third_carrier_eta': self.third_carrier_eta,
                    'note': self.note

                }
                if not self.lcl_consolidation and self.direction != 'import':
                    bol_val['customer_name'] = self.customer_name.id
                    bol_val['contact_name'] = self.contact_name.id
                    bol_val['shipper'] = self.shipper_address_input
                    bol_val['consignee'] = self.consignee_address_input
                    bol_val['notify_party'] = self.notify_party_address_input
                    bol_val['shipper_id'] = self.shipper.id
                    bol_val['consignee_id'] = self.consignee.id
                bol = bol_obj.create(bol_val)
                container_line = self.operation_line_ids2
                for line in container_line:
                    if line.container_product_name or line.container_no or line.exp_vol > 0:
                        bol_line_obj = self.env['freight.bol.cargo']
                        # print('>>>>>> BOL container=', line.container_no)
                        bol_line = bol_line_obj.create({
                            'marks': line.remark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            'container_product_id': line.container_product_id.id or False,
                            'seal_no': line.seal_no or '',
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'packages_no_value': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id or '',
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            "exp_net_weight": str(line.chargeable_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,
                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        # line.created_bl = True
            else:
                # print('>>>>>>>>>> action_create_bl lcl operation_line_ids2')
                container_line = self.operation_line_ids2
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    # if line.container_product_name and not line.created_bl:
                    bol_obj = self.env['freight.bol']
                    bol_val = {
                        'bol_status': self.bol_status or '01',
                        'no_of_original_bl': self.no_of_original_bl or '0',
                        'direction': self.direction or False,
                        'cargo_type': self.cargo_type or False,
                        'service_type': self.service_type or False,
                        'booking_date': self.booking_date_time,
                        # 'customer_name': self.customer_name.id or False,
                        # 'contact_name': self.contact_name.id or False,
                        # 'shipper': self.shipper_address_input,
                        # 'consignee': self.consignee_address_input,
                        # 'notify_party': self.notify_party_address_input,
                        'booking_ref': self.id,
                        'carrier_booking_no': self.carrier_booking_no,
                        'voyage_no': self.voyage_no,
                        'vessel': self.vessel_name.name,
                        'port_of_loading_input': self.port_of_loading.name,
                        'port_of_discharge_input': self.port_of_discharge.name,
                        'place_of_delivery': self.place_of_delivery,
                        'term': self.payment_term.name,
                        'analytic_account_id': self.analytic_account_id.id or False,
                        'sales_person': self.sales_person.id or False,
                        'shipping_agent_code': self.shipping_agent_code or False,
                        # 'shipper_c': self.shipper.id or False,
                        # 'consignee_c': self.consignee.id or False,
                        # 'notify_party_c': self.notify_party.id or False,
                        'carrier_c': self.carrier.id or False,
                        'commodity1': self.commodity1.id or False,
                        'port_of_tranship_input': self.port_of_tranship.name,
                        'port_of_tranship_eta': self.port_of_tranship_eta,
                        'shipment_close_date_time': self.shipment_close_date_time,
                        'carrier': self.carrier.id,
                        'air_agent': self.air_agent.id,
                        'airport_departure': self.airport_departure.id,
                        'airport_destination': self.airport_destination.id,
                        'first_carrier_to': self.first_carrier_to.id,
                        'first_carrier_flight_no': self.first_carrier_flight_no.id,
                        'first_carrier_etd': self.first_carrier_etd,
                        'first_carrier_eta': self.first_carrier_eta,
                        'second_carrier_to': self.second_carrier_to.id,
                        'second_carrier_flight_no': self.second_carrier_flight_no.id,
                        'second_carrier_etd': self.second_carrier_etd,
                        'second_carrier_eta': self.second_carrier_eta,
                        'third_carrier_to': self.third_carrier_to.id,
                        'third_carrier_flight_no': self.third_carrier_flight_no.id,
                        'third_carrier_etd': self.third_carrier_etd,
                        'third_carrier_eta': self.third_carrier_eta,
                        'note': self.note,
                    }
                    if self.direction != 'import' and not self.lcl_consolidation:
                        # print('>>>>>>>> booking_inherit action_create_bl lcl not lcl_consolidation')
                        bol_val['customer_name'] = self.customer_name.id
                        bol_val['contact_name'] = self.contact_name.id
                        bol_val['shipper'] = self.shipper_address_input
                        bol_val['consignee'] = self.consignee_address_input
                        bol_val['notify_party'] = self.notify_party_address_input
                        bol_val['shipper_id'] = self.shipper.id
                        bol_val['consignee_id'] = self.consignee.id
                        # bol_val['notify_party_id'] = self.notify_party.id
                    bol = bol_obj.create(bol_val)
                    # print(bol)
                    bol_line = bol_line_obj.create({
                        'marks': line.shipping_mark or '',
                        'container_product_name': line.container_product_name or False,
                        'cargo_line': bol.id or '',
                        'container_no': line.container_no or '',
                        # 'seal_no': line.seal_no or '',
                        # 'container_product_name': line.freight_currency.id,
                        'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                        'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                        'exp_vol': str(line.exp_vol) or 0.0,
                        "packages_no_value": str(line.packages_no),
                        "exp_net_weight": str(line.chargeable_weight) or 0.0
                        # 'remark_line': line.remark or '',
                    })
                    bol.write({'cargo_line_ids': bol_line or False})
                    # line.created_bl = True

        else:
            raise exceptions.ValidationError('AWB Creation is only for Air Freight Booking Job!!!')

        # ////////////////////////////////////////////
        # action = self.env.ref('sci_goexcel_freight_2.action_awb').read()[0]
        # return action

    # ////////////////////////////////////////////////////////////////

    @api.onchange('status_transhipment')
    def onchange_status_transhipment(self):
        self.shipment_booking_status = self.status_transhipment

    @api.multi
    @api.onchange("customer_name")
    def onchange_customer_name(self):
        res = super().onchange_customer_name()
        # kashif 16nov23: upgate salesperson when selecting customer
        values = {
            'sales_person': self.customer_name.user_id.id or False
        }
        self.update(values)


    # @api.one
    # @api.depends('container_qty', 'container_product_id')
    # def _compute_teus(self):
    #     if self.container_qty > 0:
    #         container = ''
    #         if self.container_product_id:
    #             container = self.container_product_id.name
    #             if '20' in container:
    #                 self.teus = self.container_qty * 1
    #             elif '40' in container:
    #                 self.teus = self.container_qty * 2
    # @api.one
    # @api.depends('container_qty', 'container_product_id')
    # def _compute_teus(self):
    #     if self.container_qty > 0:
    #         container = ''
    #         if self.container_product_id:
    #             container = self.container_product_id.name
    #             if '20' in container:
    #                 self.teus = self.container_qty * 1
    #             elif '40' in container:
    #                 self.teus = self.container_qty * 2

    @api.one
    @api.depends('operation_line_ids.container_product_id')
    def _compute_teus(self):
        teus = 0
        count = 0
        total_container = ''
        for operation_line in self.operation_line_ids:
            if operation_line.container_product_id:
                container = operation_line.container_product_id.name
                if '20' in container:
                    teus = teus + 1
                elif '40' in container:
                    teus = teus + 2
                count += 1
                if not total_container:
                    total_container = container
                else:
                    total_container = ', ' + container
        self.teus = teus
        self.container_qty = count
        self.container_no = total_container


    @api.model
    def _get_default_term(self):
        comment = self.env.user.company_id.invoice_note
        return comment

    invoice_term = fields.Text('Term', default=_get_default_term)

    @api.onchange('operation_line_ids')
    def _onchange_operation_line_ids(self):
        count = 0
        for operation_line in self.operation_line_ids:
            count += 1
            if not operation_line.container_product_id:
                if self.container_product_id:
                    operation_line.container_product_id = self.container_product_id.id
                    # operation_line.write({'container_product_id': self.container_product_id.id, })
            else:
                if not self.container_product_id:
                    self.container_product_id = operation_line.container_product_id.id
            if self.cargo_type == 'fcl':
                # self.write({'container_qty': count,})
                self.container_qty = count

    # #Added for lcl consolidation
    # @api.onchange('cost_profit_ids')
    # def _onchange_cost_profit_ids(self):
    #     #for cost_profit_ids in self.cost_profit_ids:
    #     if self.lcl_consolidation:
    #         bols = self.env['freight.bol'].search([('booking_ref', '=', self._origin.id),])
    #         booking = self.env['freight.booking'].search([('id', '=', self._origin.id),])
    #         #print('booking id=', booking.id)
    #         total_volume = 0.00
    #         total_freight_rate = 0.00
    #         cost_currency_rate = 1.00
    #         cost_currency = False
    #         chargeable_vol = 0.0
    #         #print('>>>>> _onchange_cost_price id=', self._origin.id)
    #         #Get the total volume from all the HBL
    #         for bol in bols:
    #             for cargo_line in bol.cargo_line_ids:
    #                 if cargo_line:
    #                     exp_gross_weight_tonne = float_round(cargo_line.exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
    #                     if exp_gross_weight_tonne > cargo_line.exp_vol:
    #                         chargeable_vol = exp_gross_weight_tonne
    #                     else:
    #                         chargeable_vol = cargo_line.exp_vol
    #                 else:
    #                     chargeable_vol = cargo_line.exp_vol
    #                 total_volume += chargeable_vol
    #                 #print('>>>>> _onchange_cost_profit_ids chargeable_vol=', chargeable_vol)
    #         #print('>>>>> _onchange_cost_profit_ids total_volume=', total_volume)
    #         #Update the cost for each of the HBL
    #         if self.cost_profit_ids:
    #             #print('>>>>> after self.cost_profit_ids 1')
    #             for master_cost_profit_id in self.cost_profit_ids:
    #                 #print('>>>>> after self.cost_profit_ids 2')
    #                 if master_cost_profit_id.cost_price > 0:
    #                     #print('>>>>> after self.cost_profit_ids 3')
    #                     total_freight_rate = master_cost_profit_id.cost_total
    #                     cost_currency_rate = master_cost_profit_id.cost_currency_rate
    #                     cost_currency = master_cost_profit_id.cost_currency.id
    #                 for bol in bols:
    #                     #print('>>>>> bol=', bol.bol_no)
    #                     cost_price = 0.00
    #                     converted_cost_price = 0.00
    #                     is_matched = False
    #                     for cost_profit_id in bol.cost_profit_ids:
    #                         #print('>>>>> after self.cost_profit_ids 5')
    #                         #total_freight_rate = cost_profit_id.cost_total
    #                         #cost_currency_rate = cost_profit_id.cost_currency_rate
    #                         #cost_currency = cost_profit_id.cost_currency.id
    #                         cost_price = 0.00
    #                         #converted_cost_price = 0.00
    #                         #cost_currency = False
    #                         #for bol in bols:
    #                         exp_gross_weight_tonne = 0.00
    #                         chargeable_vol = 0.00
    #                         #print('>>>>> after self.cost_profit_ids 6')
    #                         if total_volume > 0 and (bol.cargo_line_ids[0].exp_vol or bol.cargo_line_ids[0].exp_gross_weight):
    #                             #print('>>>>> after self.cost_profit_ids 6-1')
    #                             if bol.cargo_line_ids[0].exp_gross_weight > 0:
    #                                 exp_gross_weight_tonne = float_round(bol.cargo_line_ids[0].exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
    #                                 #print('>>>>> after self.cost_profit_ids 6-1-1')
    #                                 if exp_gross_weight_tonne > bol.cargo_line_ids[0].exp_vol:
    #                                     chargeable_vol = exp_gross_weight_tonne
    #                                     #print('>>>>> after self.cost_profit_ids 6-1-2')
    #                                 else:
    #                                     chargeable_vol = cargo_line.exp_vol
    #                                     #print('>>>>> after self.cost_profit_ids 6-1-3')
    #                                 #print('>>>>> after self.cost_profit_ids 6-2')
    #                             else:
    #                                 chargeable_vol = bol.cargo_line_ids[0].exp_vol
    #                             #print('>>>>>>>> _onchange_product_id total_volume 2=', total_volume, ' , chargeable_vol=', chargeable_vol)
    #                             #print('>>>>>>>>> total_freight_rate= ', total_freight_rate)
    #                             converted_cost_price = total_freight_rate / total_volume
    #                             #print('>>>>>>>>>> converted_cost_price=', converted_cost_price)
    #                             #if cost_currency_rate
    #                             cost_price = float_round(converted_cost_price / cost_currency_rate, 2,
    #                                                      rounding_method='HALF-UP')
    #                             #print('>>>>> after self.cost_profit_ids 6-2-1')
    #                         #print('>>>>> after self.cost_profit_ids 6-3')
    #                         if cost_profit_id and cost_profit_id.product_id:
    #                             #print('>>>>>>>> cost_profit_id product=', cost_profit_id.product_id.name)
    #                             #print('>>>>>>>> _onchange_product_id cost_price=', cost_price, ' , converted_cost_price=', converted_cost_price)
    #                             if master_cost_profit_id.product_id.id == cost_profit_id.product_id.id:
    #                                 #print('>>>>>>>> bol_cost_profit_id=', cost_profit_id.product_id.name, ' , rate=', cost_currency_rate)
    #                                 is_matched = True
    #                                 cost_profit_id.write({
    #                                     'cost_price': cost_price or 0.0,
    #                                     'cost_qty': chargeable_vol,
    #                                     #'cost_currency': cost_currency,
    #                                     'cost_amount': float_round(cost_price * chargeable_vol, 2,
    #                                                                rounding_method='HALF-UP'),
    #                                     'cost_currency_rate': cost_currency_rate,
    #                                 })
    #                                 if cost_currency:
    #                                     cost_profit_id.write({
    #                                         'cost_currency': cost_currency,
    #                                     })
    #                                 break
    #                     if not is_matched:
    #                         if master_cost_profit_id and master_cost_profit_id.product_id:
    #                             #print('>>>>>>>> cost_profit_id=', cost_profit_id.product_id.name)
    #                             cost_profit = self.env['freight.bol.cost.profit']
    #                             cost_line = cost_profit.create({
    #                                 'bol_id': bol.id,
    #                                 'product_id': master_cost_profit_id.product_id.id,
    #                                 'product_name': master_cost_profit_id.product_id.name,
    #                                 'cost_price': cost_price or 0.0,
    #                                 'cost_qty': chargeable_vol or 0.0,
    #                                 'cost_currency': cost_currency or self.env.user.company_id.currency_id.id,
    #                                 'cost_amount': float_round(cost_price * chargeable_vol, 2,
    #                                                            rounding_method='HALF-UP'),
    #                                 'cost_currency_rate': cost_currency_rate,
    #
    #                             })
    @api.onchange('cost_profit_ids')
    def _onchange_cost_profit_ids(self):
        if self.lcl_consolidation:
            # Delete any cost_profit records without product_id
            for bol in self.env['freight.bol'].search([('booking_ref', '=', self._origin.id)]):
                bol.cost_profit_ids.filtered(lambda r: not r.product_id).unlink()

        if self.lcl_consolidation:

            # gather all House B/Ls for this booking
            bols = self.env['freight.bol'].search([
                ('booking_ref', '=', self._origin.id),
            ])
            total_volume = 0.0

            # 1) Sum each HBL’s chargeable volume (max of weight, vol, or 1 CBM)
            for bol in bols:
                for cargo in bol.cargo_line_ids:
                    wt_t = float_round(cargo.exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
                    if cargo.exp_vol > 1.0:
                        vol = cargo.exp_vol
                    else:
                        vol = 1
                    chargeable = max(wt_t, vol)
                    total_volume += chargeable

                    cargo.write({'chargeable_weight': chargeable})

            _logger.info("BOOKING.ONCHANGE, Total Volume Charge: %s")

            # 2) Distribute each master cost line proportionally
            if total_volume > 0:
                for master in self.cost_profit_ids:
                    total_rate = master.cost_total
                    rate = master.cost_currency_rate or 1.0
                    currency = master.cost_currency.id

                    for bol in bols:
                        # recalc this BOL’s own chargeable volume
                        cargo0 = bol.cargo_line_ids and bol.cargo_line_ids[0] #todo: why using 1st cargo line?
                        if not cargo0:
                            continue
                        wt0 = float_round(cargo0.exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
                        cbm = max(wt0, cargo0.exp_vol, 1.0)

                        unit_cost = float_round((total_rate / total_volume) / rate, 2, rounding_method='HALF-UP')
                        amount = float_round(unit_cost * cbm, 2, rounding_method='HALF-UP')

                        # update existing or create new cost line on HBL
                        existing = bol.cost_profit_ids.filtered(lambda ln: ln.product_id and ln.product_id == master.product_id)
                        vals = {
                            'cost_price': unit_cost,
                            'cost_qty': cbm,
                            'cost_amount': amount,
                            'cost_currency_rate': rate,
                            'cost_currency': currency,
                            'profit_qty': cbm
                        }
                        if existing:
                            existing.write(vals)
                        else:
                            self.env['freight.bol.cost.profit'].create({
                                'bol_id': bol.id,
                                'product_id': master.product_id.id,
                                'product_name': master.product_id.name,
                                **vals
                            })





    @api.onchange('lcl_pcs')
    def onchange_lcl_pcs(self):
        if self.lcl_pcs:
            if self.lcl_volume > 0.0 and self.lcl_weight > 0.0:
                operation_line_obj = self.env['freight.operations.line2']
                op_line = operation_line_obj.create({
                    'packages_no': self.lcl_pcs or '',
                    'exp_vol': self.lcl_volume or '',
                    'exp_gross_weight': self.lcl_weight or '',
                    'container_commodity_id': self.commodity.id or False,
                    'container_product_name': self.commodity.name or '',
                    'operation_id2': self._origin.id,
                })
                self.operation_line_ids2 = op_line

    @api.onchange('obl_no')
    def onchange_obl_no(self):
        if self.obl_no and self.direction == 'import':
            self.carrier_booking_no = self.obl_no


    @api.onchange('pivot_sale_total', 'pivot_cost_total')
    def _onchange_cost_profit(self):
        self.action_reupdate_booking_invoice_one()

    @api.multi
    def action_reupdate_booking_invoice(self):
        date = datetime.now() + timedelta(days=-90)
        # date = datetime.now()
        bookings = self.env['freight.booking'].search([
            ('booking_date_time', '>=', date),
        ])
        print('>>>>>>>>>>>>> action_reupdate_booking_invoice bookings=', len(bookings), ' greater than date=', date)
        # if bookings and len(bookings) > 0:
        #    for operation in self:
        sorted_recordset = bookings.sorted(key=lambda r: r.id, reverse=True)
        for booking in sorted_recordset:
            print('>>>>>>>>> booking id=', booking.id, ' ,booking no=', booking.booking_no)
            # if booking.id == 201:
            # Get the invoices
            # print('>>>>>>action_reupdate_booking_invoice booking=511')
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', booking.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])
            # vendor_invoice_lines = self.env['booking.invoice.line'].search([
            #     ('booking_id', '=', booking.id),
            # ])
            # print('>>>>>>action_reupdate_booking_invoice before delete vendor_invoice_lines=', len(vendor_invoice_lines))
            self.env['booking.invoice.line'].search([
                ('booking_id', '=', booking.id),
            ]).unlink()

            # print('>>>>>>>> _compute_invoices_numbers invoices')
            if invoices:
                for invoice in invoices:
                    self.action_create_invoice_line(invoice, booking)
            vendor_bill_list = []
            # Get the vendor bills
            for cost_profit_line in booking.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)

            vbs = self.env['account.invoice'].search([
                ('freight_booking', '=', booking.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            # print('>>>>>>>>>>> _compute_invoices_numbers vendor bills')
            invoice_name_list = []
            for x in vbs:
                invoice_name_list.append(x.id)

            unique_list = []

            for y in unique_vendor_bill_list:
                # inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                        # self.action_create_invoice_line(inv, operation)
                else:
                    unique_list.append(y)
                    # self.action_create_invoice_line(inv, operation)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)
            for k in unique_list:
                inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                if inv:
                    # print('>>>>>>>>>> Write create vendor bills')
                    self.action_create_invoice_line(inv, booking)

            booking_invoice_lines = self.env['booking.invoice.line'].search([('booking_id', '=', booking.id)])
            inv_sales = 0
            inv_cost = 0
            # print('>>>>>>>>>> len(booking_invoice_lines)=', len(booking_invoice_lines))
            for booking_invoice_line in booking_invoice_lines:
                if booking_invoice_line.type in ['out_invoice', 'out_refund']:
                    inv_sales += booking_invoice_line.invoice_amount

                if booking_invoice_line.type in ['in_invoice', 'in_refund']:
                    inv_cost += booking_invoice_line.invoice_amount
            print('>>>>>>>> inv_sales=', inv_sales, ' inv_cost=', inv_cost)
            # ======= CODE OPTIMIZATION: by RAJEEL
            booking_id = booking.id
            select_query = f"""
                                                SELECT pivot_cost_total, pivot_sale_total FROM freight_booking WHERE id={booking_id} LIMIT 1
                                                """
            self._cr.execute(select_query)

            pivot_cost_total, pivot_sale_total = self._cr.fetchone()
            if pivot_cost_total:
                diff_amount = float_round(inv_sales - pivot_sale_total, 2, rounding_method='HALF-UP')
            else:
                diff_amount = inv_sales

            if pivot_sale_total:
                diff_cost_amount = float_round(inv_cost - pivot_cost_total, 2, rounding_method='HALF-UP')
            else:
                diff_cost_amount = inv_cost

            has_difference = diff_amount > 0 or diff_cost_amount > 0

            if not inv_sales and not inv_cost:
                inv_profit = 0
            elif inv_sales and inv_cost:
                inv_profit = float_round(inv_sales - inv_cost, 2, rounding_method='HALF-UP')
            elif not inv_sales and inv_cost:
                inv_profit = -inv_cost
            else:
                inv_profit = inv_sales

            update_query = f"""
                        UPDATE freight_booking 
                        SET 
                            inv_sales = {inv_sales} , 
                            inv_cost = {inv_cost} , 
                            diff_amount = {diff_amount} , 
                            diff_cost_amount = {diff_cost_amount} , 
                            has_difference = {has_difference} , 
                            inv_profit = {inv_profit}
                        WHERE id = {booking_id}
                        """
            self._cr.execute(update_query)
            self._cr.commit()
            # ======= CODE OPTIMIZATION: END

    @api.multi
    def action_reupdate_booking_invoice_one(self):
        #print('>>>>>>action_reupdate_booking_invoice_one')
        for operation in self:
            if operation.id:
                bookings = self.env['freight.booking'].search([
                    ('id', '=', operation.id),
                ])
                for booking in bookings:
                    # Get the invoices
                    invoices = self.env['account.invoice'].search([
                        ('freight_booking', '=', booking.id),
                        ('type', 'in', ['out_invoice', 'out_refund']),
                        ('state', '!=', 'cancel'),
                    ])
                    self.env['booking.invoice.line'].search([
                        ('booking_id', '=', booking.id),
                    ]).unlink()
                    #print('>>>>>>>> _compute_invoices_numbers invoices')
                    if invoices:
                        for invoice in invoices:
                            self.action_create_invoice_line(invoice, booking)
                    vendor_bill_list = []
                    # Get the vendor bills
                    for cost_profit_line in booking.cost_profit_ids:
                        for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                            if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                                vendor_bill_list.append(vendor_bill_line.id)
                    #print('>>>>>>> vendor_bill_list len=', len(vendor_bill_list))
                    unique_vendor_bill_list = []
                    for i in vendor_bill_list:
                        if i not in unique_vendor_bill_list:
                            unique_vendor_bill_list.append(i)
                    #print('>>>>>>> unique_vendor_bill_list len=', len(unique_vendor_bill_list))
                    vbs = self.env['account.invoice'].search([
                        ('freight_booking', '=', booking.id),
                        ('type', 'in', ['in_invoice', 'in_refund']),
                        ('state', '!=', 'cancel'),
                    ])
                    #print('>>>>>>>>>>> _compute_invoices_numbers vendor bills')
                    invoice_name_list = []
                    for x in vbs:
                        invoice_name_list.append(x.id)
                    unique_list = []
                    for y in unique_vendor_bill_list:
                        # inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
                        if invoice_name_list and len(invoice_name_list) > 0:
                            if y not in invoice_name_list:
                                unique_list.append(y)
                                # self.action_create_invoice_line(inv, operation)
                        else:
                            unique_list.append(y)
                            # self.action_create_invoice_line(inv, operation)
                    for z in invoice_name_list:
                        # if z not in vendor_bill_list:
                        unique_list.append(z)
                    for k in unique_list:
                        inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                        if inv:
                            #print('>>>>>>>>>> Write create vendor bills')
                            self.action_create_invoice_line(inv, booking)

                    # TODO purchase receipt
                    pr_lines = self.env['account.voucher.line'].search([
                        ('freight_booking', '=', booking.id),
                    ])
                    #pr_list = []
                    amt = 0.00
                    reference = ''
                    invoice_no = ''
                    for pr_line in pr_lines:
                        if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                            #pr_list.append(pr_line.voucher_id.id)
                            job_no = ''
                            if pr_line.freight_booking:
                                job_no = pr_line.freight_booking.booking_no
                            elif pr_line.freight_hbl:
                                job_no = pr_line.freight_hbl.bol_no
                            amt += pr_line.price_subtotal
                            invoice_no = pr_line.voucher_id.number
                            reference = pr_line.voucher_id.reference

                    if amt > 0 or amt < 0:
                        # print('>>>>> create vb invoice_line')
                        invoice_line = self.env['booking.invoice.line']
                        invoice_line_1 = invoice_line.create({
                            'invoice_no': invoice_no or '',
                            'reference': reference or '',
                            'invoice_amount': amt or 0,
                            'type': 'purchase_receipt',
                            'booking_id': booking.id or False,
                            'job_no': job_no or '',
                        })

                    booking_invoice_lines = self.env['booking.invoice.line'].search([('booking_id', '=', booking.id)])
                    inv_sales = 0
                    inv_cost = 0
                    for booking_invoice_line in booking_invoice_lines:
                        if booking_invoice_line.type in ['out_invoice', 'out_refund']:
                            inv_sales += booking_invoice_line.invoice_amount

                        if booking_invoice_line.type in ['in_invoice', 'in_refund', 'purchase_receipt']:
                            inv_cost += booking_invoice_line.invoice_amount
                    #print('>>>>>>>> inv_sales=', inv_sales, ' inv_cost=', inv_cost)
                    booking.write({'inv_sales': inv_sales,
                                   'inv_cost': inv_cost})
                    booking.diff_amount = float_round(booking.inv_sales - booking.pivot_sale_total, 2,
                                                      rounding_method='HALF-UP')
                    booking.has_difference = False
                    if booking.diff_amount > 0:
                        booking.has_difference = True
                    booking.diff_cost_amount = float_round(booking.inv_cost - booking.pivot_cost_total, 2,
                                                           rounding_method='HALF-UP')
                    if booking.diff_cost_amount > 0:
                        booking.has_difference = True
                    profit = inv_sales - inv_cost
                    # booking.inv_profit = float_round(profit, 2, rounding_method='HALF-UP')
                    booking.write({'inv_profit': float_round(profit, 2, rounding_method='HALF-UP'), })

    @api.one
    @api.depends('inv_sales')
    def _compute_pivot_sale_total_new(self):
        # _logger.warning('onchange_pivot_sale_total')
        if self.env.user.has_group('account.group_account_invoice'):
            self.pivot_sale_total = self.inv_sales

    @api.one
    @api.depends('inv_cost')
    def _compute_pivot_cost_total_new(self):
        if self.env.user.has_group('account.group_account_invoice'):
            self.pivot_cost_total = self.inv_cost

    @api.one
    @api.depends('inv_profit')
    def _compute_pivot_profit_total_new(self):
        if self.env.user.has_group('account.group_account_invoice'):
            self.pivot_profit_total = self.inv_profit

    @api.one
    @api.depends('pivot_profit_total')
    def _compute_pivot_margin_total_new(self):
        for service in self:
            if service.pivot_sale_total > 0:
                service.pivot_margin_total = (service.pivot_profit_total / service.pivot_sale_total) * 100

    @api.multi
    def action_create_invoice_line(self, invoice, booking):
        invoice_amount = 0.00
        if invoice.amount_total_signed > 0 or invoice.amount_total_signed < 0:
            if invoice.company_id.currency_id != invoice.currency_id:
                if invoice.exchange_rate_inverse:
                    invoice_amount = float_round(invoice.amount_total_signed * invoice.exchange_rate_inverse,
                                                 2, rounding_method='HALF-UP')
            else:
                invoice_amount = invoice.amount_total_signed
        if invoice.type in ['out_invoice', 'out_refund']:
            # print('>>>>>write action_create_invoice_line signed total=', invoice.amount_total_signed)
            # print('>>>>>write action_create_invoice_line total=', invoice.amount_total)
            # if booking_inv_lines:
            #     for booking_inv_line in booking_inv_lines:
            #         booking_inv_line.unlink()

            invoice_line = self.env['booking.invoice.line']
            invoice_line_1 = invoice_line.create({
                'invoice_no': invoice.number or '',
                'reference': invoice.number or '',
                'invoice_amount': invoice_amount,
                'type': invoice.type,
                'booking_id': booking.id or False,
            })
            # print('>>>>>write invoice successful')
        elif invoice.type in ['in_invoice', 'in_refund']:
            #print('>>>>>write action_create_invoice_line vendor bill')
            booking_id = False
            if invoice.freight_booking:
                # print('>>>>>write vendor bill booking amount:', invoice.amount_total_signed)
                invoice_line = self.env['booking.invoice.line']
                invoice_line_1 = invoice_line.create({
                    'invoice_no': invoice.number or '',
                    'reference': invoice.reference or '',
                    'invoice_amount': invoice_amount or 0,
                    'type': invoice.type,
                    'booking_id': booking.id or False,
                })
                # print('>>>>>write vendor bill successful')
            else:
                filtered_inv_lines = invoice.invoice_line_ids.filtered(lambda r: r.freight_booking.id == booking.id)
                # print('VB No=', invoice.number, ' filtered_inv_lines len=', len(filtered_inv_lines))
                if filtered_inv_lines:
                    sorted_recordset = filtered_inv_lines.sorted(key=lambda r: r.freight_booking)
                    amt = 0
                    count = 0
                    booking_id = False
                    # print('>>>>>>sorted len=', len(sorted_recordset))
                    for line in sorted_recordset:
                        if line.freight_booking:
                            count += 1
                            # print('>>>>>>line MLO Split booking no=', line.carrier_booking_no)
                            # for inv_line in line.freight_booking.invoice_line_ids:
                            if not booking_id or line.freight_booking.id == booking_id:
                                amt += line.price_subtotal
                                booking_id = line.freight_booking.id
                                # print('>>>>> amt=', amt)
                            elif line.freight_booking.id != booking_id:
                                # print('>>>>> line.freight_booking.id != booking_id')
                                if line.invoice_id.company_id.currency_id != line.invoice_id.currency_id:
                                    if line.invoice_id.exchange_rate_inverse:
                                        amt = amt * line.invoice_id.exchange_rate_inverse
                                        # print('>>>>> amt with exc rate=', amt)
                                invoice_line = self.env['booking.invoice.line']
                                if line.invoice_type in ['in_refund', 'out_refund']:
                                    amt = -(amt)
                                if amt > 0 or amt < 0:
                                    # print('>>>>> create vb invoice_line')
                                    invoice_line_1 = invoice_line.create({
                                        'invoice_no': line.invoice_id.number or '',
                                        'reference': line.invoice_id.reference or '',
                                        'invoice_amount': amt or 0,
                                        'type': line.invoice_id.type,
                                        'booking_id': booking_id or False,
                                    })
                                    amt = 0
                                    booking_id = False
                            if len(sorted_recordset) == count:
                                if amt > 0 or amt < 0:
                                    # print('>>>>> create vb invoice_line2 count=', count)
                                    if line.invoice_type in ['in_refund', 'out_refund']:
                                        amt = -(amt)
                                    invoice_line = self.env['booking.invoice.line']
                                    invoice_line_1 = invoice_line.create({
                                        'invoice_no': line.invoice_id.number or '',
                                        'reference': line.invoice_id.reference or '',
                                        'invoice_amount': amt or 0,
                                        'type': line.invoice_id.type,
                                        'booking_id': line.freight_booking.id or False,
                                    })
                                    amt = 0
                                    booking_id = False

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        # print('vendor_po=' + str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.customer_name.id,
                'name': '%s' % self.booking_no,
                # 'partner_id': self.customer_name.id,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            # print(line.vendor_bill_id)
            # print('line.vendor_id=' + line.vendor_id.name)
            if line.vendor_id != vendor_id and not line.invoiced:
                # print('not same partner')
                vb = self.env['account.invoice']
                # vb_line_obj = self.env['account.invoice.line']
                # if line.vendor_id:
                vendor_count = True
                vendor_id = line.vendor_id
                # print('vendor_id=' + vendor_id.name)
                # combine multiple cost lines from same vendor
                value = []
                vendor_bill_created = []
                filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                for vb_line in filtered_vb_lines:
                    # print('combine lines')
                    if not vb_line.invoiced:
                        account_id = False
                        # price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        price_after_converted = float_round(vb_line.cost_price * vb_line.cost_currency_rate, 6,
                                                            rounding_method='HALF-UP')
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        if not account_id:
                            raise exceptions.ValidationError(_("No Expense in Product %s Expense Account")% vb_line.product_id.name)
                        uom_id = False
                        if vb_line.uom_id:
                            uom_id = vb_line.uom_id.id
                        else:
                            uom_id = vb_line.product_id.uom_id.id
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': uom_id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'freight_booking': self.id,
                            'booking_line_id': vb_line.id,
                            'freight_currency': vb_line.cost_currency.id or False,
                            'freight_foreign_price': vb_line.cost_price or 0.0,
                            'freight_currency_rate': float_round(vb_line.cost_currency_rate, 6,
                                                                 rounding_method='HALF-UP') or 1.000000,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.invoiced = True

                vendor_bill_list = []
                if value:
                    vendor_bill_id = vb.with_context(create_from_job=True).create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        #  'default_purchase_id': self.booking_no,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.booking_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'freight_booking': self.id,
                    })
                    vendor_bill_list.append(vendor_bill_id.id)

                for vb_line in filtered_vb_lines:
                    if vb_line.invoiced:
                        vendor_bill_ids_list = []
                        if vendor_bill_list:
                            vendor_bill_ids_list.append(vendor_bill_list[0])
                            vb_line.write({
                                # 'vendor_id_ids': [(6, 0, vendor_ids_list)],
                                'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })

        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def get_vendor_bill_ids(self):
        vendor_bill_list = []
        # vendor_bill_list_temp = []
        for cost_profit_line in self.cost_profit_ids:
            for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                if vendor_bill_line.type in ['in_invoice', 'in_refund'] and vendor_bill_line.id not in vendor_bill_list:
                    vendor_bill_list.append(vendor_bill_line.id)
            if cost_profit_line.vendor_bill_id and cost_profit_line.vendor_bill_id.id not in vendor_bill_list:
                vendor_bill_list.append(cost_profit_line.vendor_bill_id.id)
        return vendor_bill_list

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = operation.get_vendor_bill_ids()
                        # vendor_bill_list_temp.append(vendor_bill_line.id)
            # print('vendor_bill_list: ',  len(vendor_bill_list))
            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            # print('unique_vendor_bill_list: ', len(unique_vendor_bill_list))
            # Get the vendor list (Create the vendor from the job)
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            # print('vendor bills:', len(invoices))
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)
            unique_list = []
            # for x in invoices:
            #     invoice_name_list.append(x.vendor_bill_id.id)
            # unique_list = []
            for y in unique_vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })
        if self._context.get('is_copy', False):
            self.update({
                'vendor_bill_count': 0,
            })
        #     self.update({
        #         'vendor_bill_count': len(unique_list),
        #     })


    @api.multi
    def operation_bill(self):
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = operation.get_vendor_bill_ids()

            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)

            unique_list = []
            for y in vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)

        if len(unique_list) > 1:
            views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                     (self.env.ref('account.invoice_supplier_form').id, 'form')]
            return {
                'name': 'Vendor bills',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.invoice',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', unique_list)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(unique_list) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }

    @api.multi
    def operation_invoices(self):
        """Show Invoice for specific Freight Operation smart Button."""
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _get_invoiced_count(self):
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])

        self.update({
            'invoice_count': len(invoices),
            'invoice_ids': invoices,
        })

    def action_create_bl(self):
        #print('>>>>>>>> booking_inherit action_create_bl')
        if self.service_type == 'ocean':
            # _logger.warning('export and ocean')
            # _logger.warning('si id=' + str(si.id))
            if self.cargo_type == 'fcl':
                oversea_agent_adr = ''
                if self.oversea_agent:
                    oversea_agent_adr += self.oversea_agent.name + "\n"
                    if self.oversea_agent.street:
                        oversea_agent_adr += self.oversea_agent.street
                    if self.oversea_agent.street2:
                        oversea_agent_adr += ' ' + self.oversea_agent.street2
                    if self.oversea_agent.zip:
                        oversea_agent_adr += ' ' + self.oversea_agent.zip
                    if self.oversea_agent.city:
                        oversea_agent_adr += ' ' + self.oversea_agent.city
                    if self.oversea_agent.state_id:
                        oversea_agent_adr += ', ' + self.oversea_agent.state_id.name
                    if self.oversea_agent.country_id:
                        oversea_agent_adr += ', ' + self.oversea_agent.country_id.name + "\n"
                    if not self.oversea_agent.country_id:
                        oversea_agent_adr += "\n"
                    if self.oversea_agent.phone:
                        oversea_agent_adr += 'Phone: ' + self.oversea_agent.phone
                    elif self.oversea_agent.email:
                        oversea_agent_adr += '. Email: ' + self.oversea_agent.email

                bol_obj = self.env['freight.bol']
                bol_val = {
                    'bol_status': self.bol_status or '01',
                    'no_of_original_bl': self.no_of_original_bl or '0',
                    'direction': self.direction or False,
                    'cargo_type': self.cargo_type or False,
                    'service_type': self.service_type or False,
                    'booking_date': self.booking_date_time,
                    #'customer_name': self.customer_name.id or False,
                    #'contact_name': self.contact_name.id or False,
                    #'shipper': self.shipper_address_input,
                    #'consignee': self.consignee_address_input,
                    #'notify_party': self.notify_party_address_input,
                    'booking_ref': self.id,
                    'carrier_booking_no': self.carrier_booking_no,
                    'voyage_no': self.voyage_no,
                    'vessel': self.vessel_name.name,
                    'feeder_voyage_no': self.feeder_voyage_no,
                    'pre_carriage_by': self.feeder_vessel_name,
                    'port_of_loading_input': self.port_of_loading.name,
                    'port_of_discharge_input': self.port_of_discharge.name,
                    'port_of_discharge_eta': self.port_of_discharge_eta,
                    'place_of_delivery': self.place_of_delivery,
                    'term': self.payment_term.name,
                    'analytic_account_id': self.analytic_account_id.id or False,
                    'sales_person': self.sales_person.id or False,
                    'shipping_agent_code': self.shipping_agent_code or False,
                    'oversea_agent': self.oversea_agent.id or False,
                    'routing_instruction': oversea_agent_adr,
                    #'consignee_c': self.consignee.id or False,
                    #'notify_party_c': self.notify_party.id or False,
                    'carrier_c': self.carrier.id or False,
                    'commodity1': self.commodity1.id or False,
                    'port_of_tranship_input': self.port_of_tranship.name,
                    'port_of_tranship_eta': self.port_of_tranship_eta,
                    'shipment_close_date_time': self.shipment_close_date_time,
                    'terminal': self.terminal.name or False,
                    'vessel_id': self.vessel_id or False
                }
                if not self.lcl_consolidation and self.direction != 'import':
                    bol_val['customer_name'] = self.customer_name.id
                    bol_val['contact_name'] = self.contact_name.id
                    bol_val['shipper'] = self.shipper_address_input
                    bol_val['consignee'] = self.consignee_address_input
                    bol_val['notify_party'] = self.notify_party_address_input
                    bol_val['shipper_id'] = self.shipper.id
                    bol_val['consignee_id'] = self.consignee.id
                bol = bol_obj.create(bol_val)
                container_line = self.operation_line_ids
                for line in container_line:
                    if line.container_product_name or line.container_no or line.exp_vol>0:
                        bol_line_obj = self.env['freight.bol.cargo']
                        additional_marks = 'CONTAINER / SEAL NO: ' \
                                           + '\n' + (line.container_no or '') + ' / ' + (line.seal_no or '')
                        marks = line.shipping_mark or ''
                        if 'CONTAINER' not in marks:
                            if marks:
                                marks += '\n\n'
                            marks += additional_marks
                        #print('>>>>>> BOL container=', line.container_no)
                        bol_line = bol_line_obj.create({
                            'marks': marks or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            'container_product_id': line.container_product_id.id or False,
                            'seal_no': line.seal_no or '',
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'packages_no_value': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id or '',
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,
                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        #line.created_bl = True
            else:
                #print('>>>>>>>>>> action_create_bl lcl operation_line_ids2')
                container_line = self.operation_line_ids2
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    #if line.container_product_name and not line.created_bl:
                    bol_obj = self.env['freight.bol']
                    bol_val = {
                        'bol_status': self.bol_status or '01',
                        'no_of_original_bl': self.no_of_original_bl or '0',
                        'direction': self.direction or False,
                        'cargo_type': self.cargo_type or False,
                        'service_type': self.service_type or False,
                        'booking_date': self.booking_date_time,
                        #'customer_name': self.customer_name.id or False,
                        #'contact_name': self.contact_name.id or False,
                        #'shipper': self.shipper_address_input,
                        #'consignee': self.consignee_address_input,
                        #'notify_party': self.notify_party_address_input,
                        'booking_ref': self.id,
                        'carrier_booking_no': self.carrier_booking_no,
                        'voyage_no': self.voyage_no,
                        'vessel': self.vessel_name.name,
                        'port_of_loading_input': self.port_of_loading.name,
                        'port_of_discharge_input': self.port_of_discharge.name,
                        'place_of_delivery': self.place_of_delivery,
                        'term': self.payment_term.name,
                        'analytic_account_id': self.analytic_account_id.id or False,
                        'sales_person': self.sales_person.id or False,
                        'shipping_agent_code': self.shipping_agent_code or False,
                        # 'shipper_c': self.shipper.id or False,
                        # 'consignee_c': self.consignee.id or False,
                        # 'notify_party_c': self.notify_party.id or False,
                        'carrier_c': self.carrier.id or False,
                        'commodity1': self.commodity1.id or False,
                        'port_of_tranship_input': self.port_of_tranship.name,
                        'port_of_tranship_eta': self.port_of_tranship_eta,
                        'shipment_close_date_time': self.shipment_close_date_time,
                    }
                    if self.direction != 'import' and not self.lcl_consolidation:
                        #print('>>>>>>>> booking_inherit action_create_bl lcl not lcl_consolidation')
                        bol_val['customer_name'] = self.customer_name.id
                        bol_val['contact_name'] = self.contact_name.id
                        bol_val['shipper'] = self.shipper_address_input
                        bol_val['consignee'] = self.consignee_address_input
                        bol_val['notify_party'] = self.notify_party_address_input
                        bol_val['shipper_id'] = self.shipper.id
                        bol_val['consignee_id'] = self.consignee.id
                        #bol_val['notify_party_id'] = self.notify_party.id
                    bol = bol_obj.create(bol_val)
                    #print(bol)
                    additional_marks = 'CONTAINER / SEAL NO: ' \
                                       + '\n' + (line.container_no or '') + ' / ' + (line.seal_no or '')
                    marks = line.shipping_mark or ''
                    if 'CONTAINER' not in marks:
                        if marks:
                            marks += '\n\n'
                        marks += additional_marks

                    bol_line = bol_line_obj.create({
                        'marks': marks,
                        'container_product_name': line.container_product_name or False,
                        'cargo_line': bol.id or '',
                        'container_no': line.container_no or '',
                        'seal_no': line.seal_no or '',
                        # 'container_product_name': line.freight_currency.id,
                        'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                        'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                        'exp_vol': str(line.exp_vol) or 0.0,
                        # 'remark_line': line.remark or '',
                    })
                    bol.write({'cargo_line_ids': bol_line or False})
                        #line.created_bl = True

        else:
            raise exceptions.ValidationError('BL Creation is only for Ocean Export Freight Booking Job!!!')

    purchase_receipt_count = fields.Integer(string='Purchase Receipt Count', compute='_get_pr_count', copy=False)

    def _get_pr_count(self):
        # get purchase receipt (Account Voucher) on the lines
        for operation in self:
            # Get PR list
            pr_lines = self.env['account.voucher.line'].search([
                ('freight_booking', '=', operation.id),
            ])
            pr_list = []
            for pr_line in pr_lines:
                if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                    pr_list.append(pr_line.voucher_id.id)
            # pr_name_list = []
            # for x in pr_list:
            #     pr_name_list.append(x.id)
            unique_list = []
            for i in pr_list:
                if i not in unique_list:
                    unique_list.append(i)

            if len(unique_list) > 0:
                self.update({
                    'purchase_receipt_count': len(unique_list),
                })

    @api.multi
    def operation_pr(self):
        for operation in self:
            for operation in self:
                # Get PR list
                pr_lines = self.env['account.voucher.line'].search([
                    ('freight_booking', '=', operation.id),
                ])
                pr_list = []
                for pr_line in pr_lines:
                    if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                        pr_list.append(pr_line.voucher_id.id)
                # pr_name_list = []
                # for x in pr_list:
                #     pr_name_list.append(x.id)
                unique_list = []
                for i in pr_list:
                    if i not in unique_list:
                        unique_list.append(i)

        if len(unique_list) > 1:
            views = [(self.env.ref('account_voucher.view_voucher_tree').id, 'tree'),
                     (self.env.ref('account_voucher.view_purchase_receipt_form').id, 'form')]
            return {
                'name': 'Purchase Receipt',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.voucher',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', unique_list)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(unique_list) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.voucher',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


    #move from the sci_goexcel_ocean_freight_rate
    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)])

            self.billing_address = sq.partner_id.id or False,
            self.sales_person = sq.user_id.id,
            self.incoterm = sq.incoterm.id or False,
            self.port_of_loading = sq.POL.id or False,
            self.port_of_discharge = sq.POD.id or False,
            self.commodity = sq.commodity.id or False,
            self.payment_term = sq.payment_term_id.id or False,
            if sq.carrier_booking_no:
                self.carrier_booking_no = sq.carrier_booking_no
            self.contact_name = sq.contact_name.id or False,
            self.forwarding_agent_code = sq.forwarding_agent_code.id or False,
            self.hs_code = sq.hs_code.id or False,
            if sq.coo:
                self.coo = True
            else:
                self.coo = False
            if sq.fumigation:
                self.fumigation = True
            else:
                self.fumigation = False
            if sq.insurance:
                self.insurance = True
            else:
                self.insurance = False
            if sq.cpc:
                self.cpc = True
            else:
                self.cpc = False
            self.warehouse_hours = sq.warehouse_hours.id or False,
            self.airport_departure = sq.airport_departure.id or False,
            self.airport_destination = sq.airport_destination.id or False,
            self.transporter_company = sq.transporter_company.id or False,
            shipper_adr = ''
            consignee_adr = ''
            notify_party_adr = ''
            if sq.shipper:
                shipper_adr += sq.shipper.name + "\n"
                if sq.shipper.street:
                    shipper_adr += sq.shipper.street
                if sq.shipper.street2:
                    shipper_adr += ' ' + sq.shipper.street2
                if sq.shipper.zip:
                    shipper_adr += ' ' + sq.shipper.zip
                if sq.shipper.city:
                    shipper_adr += ' ' + sq.shipper.city
                if sq.shipper.state_id:
                    shipper_adr += ', ' + sq.shipper.state_id.name
                if sq.shipper.country_id:
                    shipper_adr += ', ' + sq.shipper.country_id.name + "\n"
                if not sq.shipper.country_id:
                    shipper_adr += "\n"
                if sq.shipper.phone:
                    shipper_adr += 'Phone: ' + sq.shipper.phone
                elif sq.shipper.mobile:
                    shipper_adr += '. Mobile: ' + sq.shipper.mobile
            if sq.consignee:
                consignee_adr += sq.consignee.name + "\n"
                if sq.consignee.street:
                    consignee_adr += sq.consignee.street
                if sq.consignee.street2:
                    consignee_adr += ' ' + sq.consignee.street2
                if sq.consignee.zip:
                    consignee_adr += ' ' + sq.consignee.zip
                if sq.consignee.city:
                    consignee_adr += ' ' + sq.consignee.city
                if sq.consignee.state_id:
                    consignee_adr += ', ' + sq.consignee.state_id.name
                if sq.consignee.country_id:
                    consignee_adr += ', ' + sq.consignee.country_id.name + "\n"
                if not sq.consignee.country_id:
                    consignee_adr += "\n"
                if sq.consignee.phone:
                    consignee_adr += 'Phone: ' + sq.consignee.phone
                elif sq.consignee.mobile:
                    consignee_adr += '. Mobile: ' + sq.consignee.mobile
            if sq.partner_id:
                notify_party_adr = sq.partner_id.name + "\n"
                if sq.partner_id.street:
                    notify_party_adr += sq.partner_id.street
                if sq.partner_id.street2:
                    notify_party_adr += ' ' + sq.partner_id.street2
                if sq.partner_id.zip:
                    notify_party_adr += ' ' + sq.partner_id.zip
                if sq.partner_id.city:
                    notify_party_adr += ' ' + sq.partner_id.city
                if sq.partner_id.state_id:
                    notify_party_adr += ', ' + sq.partner_id.state_id.name
                if sq.partner_id.country_id:
                    notify_party_adr += ', ' + sq.partner_id.country_id.name + "\n"
                if not sq.partner_id.country_id:
                    notify_party_adr += "\n"
                if sq.partner_id.phone:
                    notify_party_adr += 'Phone: ' + sq.partner_id.phone
                elif sq.partner_id.mobile:
                    notify_party_adr += '. Mobile: ' + sq.partner_id.mobile
            booking.write({'direction': sq.mode or False,
                           'customer_name': sq.partner_id.id or False,
                           'cargo_type': sq.type or False,
                           'service_type': sq.service_type,
                           'shipper': sq.shipper.id or False,
                           'consignee': sq.consignee.id or False,
                           'notify_party': sq.partner_id.id or False,
                           'notify_party_address_input': notify_party_adr,
                           'consignee_address_input': consignee_adr,
                           'shipper_address_input': shipper_adr,
                           })
            for line in booking.cost_profit_ids:
                line.unlink()
            cost_profit_obj = self.env['freight.cost_profit']
            ocean_freight_rate_product = self.env['product.product'].sudo().search(
                [('id', '=', self.env['ir.config_parameter'].sudo().get_param(
                    'sci_goexcel_ocean_freight_rate.product_ocean_freight_rate'))]
                , limit=1)
            current_date = datetime.today()
            for line in sq.order_line:
                if line.product_id:
                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    elif line.product_id == ocean_freight_rate_product:
                        #print(ocean_freight_rate_product)
                        price_unit = 0
                        ocean_freight_rate_ids = self.env['freight.ocean.freight.rate.line'].search(
                            [('valid_from', '<=', current_date), ('valid_to', '>=', current_date),
                             ('customer', '=', sq.partner_id.id)])
                        port_pair_ids = self.env['freight.port.pair'].search(
                            [('port_of_loading', '=', sq.POL.id),
                             ('port_of_discharge', '=', sq.POD.id)], limit=1)
                        if ocean_freight_rate_ids:
                            for i in ocean_freight_rate_ids:
                                if port_pair_ids in i.ocean_freight_rate_id.port_pair:
                                    if sq.carrier == i.ocean_freight_rate_id.carrier:
                                        if sq.container_product_id == i.ocean_freight_rate_id.container_product_id:
                                            if i.ocean_freight_rate_id.state == 'active':
                                                price_unit = line.price_unit
                    else:
                        price_unit = line.price_unit
                    #print(price_unit)
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'uom_id': line.product_uom.id or False,
                        'product_name': line.name or False,
                        'booking_id': booking.id or '',
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                        'cost_price': line.cost_price or 0.0,
                        'cost_currency': line.cost_currency.id or False,
                        'cost_currency_rate': line.cost_exc_rate or 1.0,
                    })
                    booking.write({'cost_profit_ids': cost_profit_line or False})



    @api.multi
    def action_send_booking_confirmation_si(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        if self.carrier_booking_no:
            #print('action_send_booking_confirmation_si carrier booking no')
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_edi_booking_confirmation')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            excel_template_id = self.env.ref('sci_goexcel_freight_2.action_si_report_xlsx').render_xlsx(self.ids,[])
            #print('action_send_booking_confirmation_si carrier excel_template_id=', excel_template_id)
            data_record = base64.b64encode(excel_template_id[0])
            file_name = 'SI ' + self.booking_no + '.xlsx'
            ir_values = {
                'name': "Shipping Instruction",
                'type': 'binary',
                'datas': data_record,
                'datas_fname': file_name,
                'store_fname': 'Shipping Instruction',
                'mimetype': 'application/xlsx',
            }
            excel_attachment = self.env['ir.attachment'].create(ir_values)
            template = self.env['mail.template'].browse(template_id)
            template.attachment_ids = False
            template.attachment_ids = [(4, excel_attachment.id)]
            ctx = {
                'default_model': 'freight.booking',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_light",
                # 'proforma': self.env.context.get('proforma', False),
                'force_email': True
            }
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
            self.shipment_booking_status = '02'
        else:
            raise exceptions.ValidationError('Carrier Booking No must not be empty!!!')


    #  For Carrier Booking Number
    @api.onchange('carrier_booking_no')
    def _onchange_carrier_booking_no(self):

        if self.carrier_booking_no:
            #res = super(FreightBooking2, self).onchange_carrier_booking_no()
            carrier_booking_check = self.env['freight.booking'].search(
                [('carrier_booking_no', '=', self.carrier_booking_no)],
                limit=1)
            if carrier_booking_check:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': 'Carrier Booking Number Already Existed!'
                    }
                }


    #For ETD Date
    @api.onchange('shipment_booking_status')
    def _onchange_shipment_booking_status(self):
        res = super(FreightBooking2, self).onchange_shipment_booking_status()
        if self.shipment_booking_status == '02':
            if not self.booking_date_time:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': 'Please Enter ETA/ETD Date!'}
                }


    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'sq'),('default', '=', True),
                                                                ('company_id', '=', self.company_id.id)], limit=1)
            if template:
                return template.template

    @api.model
    def create(self, vals):
        company = vals.get('company_id')
        template = self.env['sale.letter.template'].search([('doc_type', '=', 'bc'), ('default', '=', True),
                                                            ('company_id', '=', company)], limit=1)
        vals['bc_sale_term'] = template.template
        vals['template_id'] = template.id
        if self._context.get('is_copy', False):
            vals['vendor_bill_count'] = 0
        res = super(FreightBooking2, self).create(vals)
        return res

    template_id = fields.Many2one('sale.letter.template', 'Template')
    bc_sale_term = fields.Html('T&C', default=_get_default_term)


    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.bc_sale_term = self.template_id.template

    sq_reference = fields.Many2many(
        "sale.order", "sq_booking_rel", "sq_id", "booking_id", "SQ Reference", copy=False
    )

    @api.multi
    def action_multi_quotation(self):
        self.ensure_one()
        view = self.env.ref("sci_goexcel_freight_2.multi_quotation_view_form")
        customer_id = self.customer_name.id
        return {
            "name": "Create",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "context": {"booking_id": self.id, "customer": customer_id},
            "res_model": "multi.quotation.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
        }

class FreightOperationLine2(models.Model):
    """Freight Operation Line Model."""
    _inherit = 'freight.operations.line2'

    exp_vol = fields.Float(string="Measurement Vol", digits=(12, 4),
                           help="Expected Volume in M3 or CM3 Measure")
    dim_length_uom = fields.Many2one('uom.uom', string='L.UoM', help="Length UoM", track_visibility='onchange')
    dim_width_uom = fields.Many2one('uom.uom', string='W.UoM', help="Width UoM", track_visibility='onchange')
    dim_height_uom = fields.Many2one('uom.uom', string='H.UoM', help="Height UoM", track_visibility='onchange')


    # haulage_charge_product = self.env['product.product'].sudo().search(
    #     [(
    #         'id', '=', self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_haulage_charge.haulage_product'))]
    #     , limit=1)

    @api.depends('dim_length', 'dim_width', 'dim_height', 'packages_no')
    def _compute_vol_weight(self):
        for line in self:
            cm_uom = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_freight_2.cbm_uom')
            inc_uom = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_freight_2.inc_uom')
            if int(line.dim_length_uom.id) == int(cm_uom):
                if line.dim_length or line.dim_width or line.dim_height or line.packages_no:
                    # get the KG
                    line.volumetric_weight = (
                                                     line.packages_no * line.dim_length * line.dim_width * line.dim_height) / 6000
            elif int(line.dim_length_uom.id) == int(inc_uom):
                if line.dim_length or line.dim_width or line.dim_height or line.packages_no:
                    # get the KG
                    line.volumetric_weight = (
                                                     line.packages_no * line.dim_length * line.dim_width * line.dim_height) / 366
                    #get the pounds
                    #line.volumetric_weight = (line.packages_no * line.dim_length * line.dim_width * line.dim_height) / 366

class FreightOperationLine3(models.Model):
    _inherit = 'freight.operations.line2'
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)

    @api.model
    def create(self, vals):
        temp = []
        booking_id = False

        if 'container_no' in vals and 'container_product_id' in vals:
            booking_id = self.env['freight.booking'].search([('id', '=', vals['operation_id2'])], limit=1)
            try:
                for i in range(0, int(vals['container_no'])):
                    temp.append((0, 0, {'container_product_id': vals['container_product_id']}))
                booking_id.operation_line_ids = temp
            except ValueError:
                raise UserError(
                    _("Please enter only integer, eg, 1, 2, 3, 4, etc to indicate the number of Containers for this booking job. System will create lines in the Manifest")
                )
        else:
            booking_id = self.env['freight.booking'].search([('id', '=', vals['operation_id2'])], limit=1)

        obj = super(FreightOperationLine3, self).create(vals)

        if booking_id.service_type == 'air':
            air_freight_product = self.env['product.product'].search([('is_air_freight_product', '=', True)], limit=1)
            if air_freight_product:
                cost_profit_obj = self.env['freight.cost_profit']
                cost_profit_line = cost_profit_obj.create({
                    'product_id': air_freight_product.id or False,
                    'uom_id' : air_freight_product.uom_id.id or False,
                    'product_name': air_freight_product.name or False,
                    'booking_id': booking_id.id or '',
                    'profit_qty': obj.chargeable_weight or 0,
                    # 'profit_currency': line.freight_currency.id,
                    # 'cost_currency': line.cost_currency.id or False,
                })
                booking_id.write({'cost_profit_ids': cost_profit_line or False})

        return obj

class CostProfit(models.Model):
    _inherit = 'freight.cost_profit'

    # def copy(self, default=None):
    #     default = dict(default or {})
    #     default.update({
    #         'vendor_bill_id': False,
    #         'vendor_bill_ids': [(6, 0, [])],  # clear all linked vendor bills
    #         'invoiced': False  # reset invoiced flag
    #     })
    #     return super(CostProfit, self).copy(default)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'uom_id': []}}

        vals = {}
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
            vals['uom_id'] = self.product_id.uom_id
            vals['product_name'] = self.product_id.name

        self.update(vals)
        if self.product_id:
            #update the air freight selling price based on the chargeable weight
            selling_qty = 1.00
            profit_qty_set = 0.0
            #booking = self.env['freight.booking'].search([('id', '=', self._origin.id)], limit=1)
            booking = self.env['freight.booking'].search([('id', '=', self.env.context.get('active_id'))], limit=1)
            #print('>>>>>>>> _onchange_product_id booking=', booking.booking_no)
            if booking.service_type == 'air':
                #print('>>>>>>>> _onchange_product_id air booking')
                air_freight_rate = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_freight_2.air_freight_rate_product')
                #print('>>>>>>>> _onchange_product_id air_freight_rate=', air_freight_rate)
                #print('>>>>>>>> _onchange_product_id product=', self.product_id.id)
                manifest_line = self.env['freight.operations.line2'].search([('operation_id2', '=', self.env.context.get('active_id'))], limit=1)
                #print('>>>>>>>> _onchange_product_id manifest_line=', manifest_line)
                #print('>>>>>>>> _onchange_product_id chargeable_weight=', manifest_line.chargeable_weight)
                #print('>>>>>>>> _onchange_product_id container_product_name=', manifest_line.container_product_name)
                #print('>>>>>>>> _onchange_product_id volumetric_weight=', manifest_line.volumetric_weight)
                #print('>>>>>>>> _onchange_product_id packages no=', manifest_line.packages_no)
                #print('>>>>>>>> _onchange_product_id exp_gross_weight=', manifest_line.exp_gross_weight)
                if air_freight_rate and self.product_id.id == int(air_freight_rate):
                    cm_uom = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_freight_2.cbm_uom')
                    inc_uom = self.env['ir.config_parameter'].sudo().get_param('sci_goexcel_freight_2.inc_uom')
                    volumetric_weight = 0

                    if manifest_line.dim_length or manifest_line.dim_width or manifest_line.dim_height or manifest_line.packages_no:
                        if int(manifest_line.dim_length_uom.id) == int(cm_uom):
                            volumetric_weight = (manifest_line.packages_no * manifest_line.dim_length * manifest_line.dim_width * manifest_line.dim_height) / 6000
                        elif int(manifest_line.dim_length_uom.id) == int(inc_uom):
                            volumetric_weight = (manifest_line.packages_no * manifest_line.dim_length * manifest_line.dim_width * manifest_line.dim_height) / 366

                    a = int(volumetric_weight)
                    b = int(manifest_line.exp_gross_weight)

                    if b > a:
                        chargeable_weight = manifest_line.exp_gross_weight
                    else:
                        chargeable_weight = volumetric_weight
                    if chargeable_weight > 0:
                        selling_qty = chargeable_weight

                if self.product_id.is_air_freight_product:
                    profit_qty_set = manifest_line.chargeable_weight or 0.0
                    self.update({
                        'profit_qty':manifest_line.chargeable_weight or 0.0

                    })

            if self.product_id.is_air_freight_product:

                self.update({
                    'profit_qty': profit_qty_set

                })
            else:
                self.update({
                    'list_price': self.product_id.list_price or 0.0,
                    'cost_price': self.product_id.standard_price or 0.0,
                    'profit_qty': selling_qty,
                })

    cost_price = fields.Float(
        string="Unit Price", track_visibility="onchange"
    )

    account_invoice_line = fields.Many2one('account.invoice.line')

    @api.onchange("cost_qty", "profit_qty")
    def _compare_qty(self):
        for rec in self:
            if rec.cost_qty > rec.profit_qty:
                raise UserError("Selling quantity must be greater than Cost Quantity!")

    # Ahmad Zaman - 19/4/24 - Added Fiscal Position (B2B Exemption) Support
    @api.onchange('product_id')
    def set_tax_value(self):
        for rec in self:
            if rec.product_id:
                partner_fiscal_position = rec.booking_id.shipper.property_account_position_id
                if partner_fiscal_position:
                    partner_source_tax = partner_fiscal_position.tax_ids.filtered(
                        lambda x: x.tax_src_id.id == rec.product_id.taxes_id.id).tax_src_id
                    partner_replacement_tax = partner_fiscal_position.tax_ids.filtered(
                        lambda x: x.tax_src_id.id == rec.product_id.taxes_id.id).tax_dest_id
                else:
                    partner_source_tax = ''
                    partner_replacement_tax = ''
                product = rec.product_id
                product_tax = rec.product_id.taxes_id
                if partner_fiscal_position:
                    if product and product_tax and product_tax.id == partner_source_tax.id:
                        rec.tax_id = [(6, 0, [partner_replacement_tax.id])]
                elif product and product_tax:
                    rec.tax_id = [(6, 0, [product_tax.id])]
                else:
                    return