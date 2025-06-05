from odoo import api, fields, models,exceptions, _
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)
import base64

class BillOfLading(models.Model):
    _inherit = "freight.bol"

    hbl_no = fields.Char(string='OBL No', copy=False, readonly=False)
    bl_status = fields.Selection([('original', 'Original'),
                                  ('seaway', 'Seaway'),
                                  ('telex', 'Telex')],
                                 string="BL Status", track_visibility='onchange')
    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')],
                                    string='Freight Type', track_visibility='onchange')

    sn_no = fields.Char(string='BL No', copy=False, index=True)
    unstuff_date = fields.Date(string='Unstuff Date', track_visibility='onchange')
    port_of_tranship_input = fields.Text(string='Port of Tranship', track_visibility='onchange')
    port_of_tranship_eta = fields.Date(string='Tranship ETA', track_visibility='onchange', copy=False)
    # place_of_delivery = fields.Char(string='Place of Delivery', track_visibility='onchange')
    shipment_close_date_time = fields.Datetime(string='Closing Date Time', track_visibility='onchange', copy=False)
    shipper_id = fields.Many2one('res.partner', string='Shipper', help="The Party who shipped the freight, eg Exporter",
                              track_visibility='onchange')
    consignee_id = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight",
                                track_visibility='onchange')
    sq_reference = fields.Many2one('sale.order', string='S.Q Reference', track_visibility='onchange', copy=False,
                                   index=True)
    oversea_agent = fields.Many2one('res.partner', string='Oversea Agent',
                                    help="The Party who will be help to ship cargo from oversea",
                                    track_visibility='onchange')
    type_of_movement = fields.Selection(selection_add=[('cy-ramp', 'CY-RAMP'),('cy-sd', 'CY-SD')])

    invoice_no = fields.Char(string='Invoice No')
    # /////////////////////////////////////////////////////////////////////////////

    awb_no = fields.Char(string='AWB No', compute='_compute_awb_no', store=True, readonly=False, index=True)
    agen_iata_code = fields.Char("IATA Code")
    account_number = ('Account Number')
    request_flight_date = fields.Date("Request Flight Date")
    reference_number = fields.Char("Reference Number")
    optional_shipping_information = fields.Char("Optional Shipping Inforamtion")
    Currency = fields.Char("Currency" ,default="MYR")
    chgs_code = fields.Char("CHGS Code")
    wt_ppd = fields.Char("WT/VAL PPD")
    wt_coll = fields.Char("WT/VAL COLL" , default="PP")
    other_ppd = fields.Char("Other PPD")
    other_coll = fields.Char("Other COLL", default="PP")
    declared_value_for_carriage = fields.Char('Declared Value For Carriage', default="NVD")
    declared_value_for_custom = fields.Char('Declared Value For Custom', default="NCV")
    account_of_insurance = fields.Char("Account Of Insurance")
    sci = fields.Char("SCI")

    consignee_account_number = fields.Char("Consignee Account Number")
    air_agent = fields.Many2one(
        "res.partner",
        string="Air Agent",
        help="The Party who will be help to ship import cargo",
        track_visibility="onchange",
    )

    air_agent_address = fields.Text(
        string="Air Agent Address", track_visibility="onchange"
    )

    carrier = fields.Many2one("res.partner", string="Carrier", track_visibility="onchange")


    airport_departure = fields.Many2one(
        "freight.airport", string="Airport Departure", track_visibility="onchange"
    )
    airport_destination = fields.Many2one(
        "freight.airport", string="Airport Destination", track_visibility="onchange"
    )
    first_carrier_to = fields.Many2one(
        "freight.airport", string="First Carrier To", track_visibility="onchange"
    )
    first_carrier_flight_no = fields.Many2one(
        "airline.flight", string="1st Flight No", track_visibility="onchange"
    )
    first_carrier_etd = fields.Datetime(
        string="F. Carrier ETD", track_visibility="onchange", copy=False
    )
    first_carrier_eta = fields.Datetime(
        string="F. Carrier ETA", track_visibility="onchange", copy=False
    )
    second_carrier_to = fields.Many2one(
        "freight.airport", string="Second Carrier To", track_visibility="onchange"
    )
    second_carrier_flight_no = fields.Many2one(
        "airline.flight", string="2nd Flight No", track_visibility="onchange"
    )
    second_carrier_etd = fields.Datetime(
        string="S.Carrier ETD", track_visibility="onchange", copy=False
    )
    second_carrier_eta = fields.Datetime(
        string="S. Carrier ETA", track_visibility="onchange", copy=False
    )
    third_carrier_to = fields.Many2one(
        "freight.airport", string="Third Carrier To", track_visibility="onchange"
    )
    third_carrier_flight_no = fields.Many2one(
        "airline.flight", string="3rd Flight No", track_visibility="onchange"
    )
    third_carrier_etd = fields.Datetime(
        string="T. Carrier ETD", track_visibility="onchange", copy=False
    )
    third_carrier_eta = fields.Datetime(
        string="T. Carrier ETA", track_visibility="onchange", copy=False
    )

    # Josh 18042025, add smart buttons to BOL for invoice and vendor bill
    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_invoice_vendorbill_count", copy=False)
    vendor_bill_count = fields.Integer(string="Vendor Bill Count", compute="_compute_invoice_vendorbill_count", copy=False)

    #Josh 24042025, add terminal and vessel id where values are from bookings
    terminal = fields.Char("Terminal")
    vessel_id = fields.Char("Vessel ID")

    #Josh 16052025, add lcl consolidation boolean field, based on booking
    lcl_consolidation = fields.Boolean(string='LCL Consolidation', compute="_booking_is_lcl")

    @api.depends('booking_ref.lcl_consolidation')
    def _booking_is_lcl(self):
        for record in self:
            record.lcl_consolidation = record.booking_ref.lcl_consolidation if record.booking_ref else False

    def _compute_invoice_vendorbill_count(self):
        for rec in self:
            booking = rec.booking_ref
            if booking:
                rec.invoice_count = self.env['account.invoice'].search_count([
                    ('freight_booking', '=', booking.id),
                    ('type', '=', 'out_invoice')
                ])
                rec.vendor_bill_count = self.env['account.invoice'].search_count([
                    ('freight_booking', '=', booking.id),
                    ('type', '=', 'in_invoice')
                ])
            else:
                rec.invoice_count = 0
                rec.vendor_bill_count = 0

    def operation_invoices(self):
        self.ensure_one()
        return {
            'name': 'Customer Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'tree,form',
            'domain': [('freight_booking', '=', self.booking_ref.id), ('type', '=', 'out_invoice')],
            'context': {'default_freight_booking': self.booking_ref.id}
        }

    def operation_bill(self):
        self.ensure_one()
        return {
            'name': 'Vendor Bills',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'tree,form',
            'domain': [('freight_booking', '=', self.booking_ref.id), ('type', '=', 'in_invoice')],
            'context': {'default_freight_booking': self.booking_ref.id}
        }

    # def action_view_bol_invoices(self):
    #     self.ensure_one()
    #     return {
    #         'name': 'Customer Invoices',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.invoice',
    #         'domain': [('freight_booking', '=', self.booking_ref.id), ('type', '=', 'out_invoice')],
    #         'context': {'default_freight_booking': self.booking_ref.id}
    #     }
    #
    # def action_view_bol_vendor_bills(self):
    #     self.ensure_one()
    #     return {
    #         'name': 'Vendor Bills',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.invoice',
    #         'domain': [('freight_booking', '=', self.booking_ref.id), ('type', '=', 'in_invoice')],
    #         'context': {'default_freight_booking': self.booking_ref.id}
    #     }
    # ///////////////////////////////////////////////////////////////////////////////

    @api.depends('bol_no', 'service_type')
    def _compute_awb_no(self):
        for record in self:
            if record.service_type == 'air':
                record.awb_no = record.bol_no
            else:
                record.awb_no = False
    @api.onchange('air_agent')
    def onchange_air_agent(self):
        adr = ''
        if self.air_agent:
            # if self.consignee_address_input is False or '':
            adr += self.air_agent.name + "\n"
            if self.air_agent.street:
                adr += self.air_agent.street
            if self.air_agent.street2:
                adr += ' ' + self.air_agent.street2
            if self.air_agent.zip:
                adr += ' ' + self.air_agent.zip
            if self.air_agent.city:
                adr += ' ' + self.air_agent.city
            if self.air_agent.state_id:
                adr += ', ' + self.air_agent.state_id.name
            if self.air_agent.country_id:
                adr += ', ' + self.air_agent.country_id.name + "\n"
            if not self.air_agent.country_id:
                adr += "\n"
            if self.air_agent.phone:
                adr += 'Phone: ' + self.air_agent.phone
            elif self.air_agent.mobile:
                adr += '. Mobile: ' + self.air_agent.mobile
            self.air_agent_address = adr


    @api.model
    def create(self, vals):
        # if vals.get('service_type') == 'land':
        #     if not vals.get('bol_no'):
        #         sequence = self.env['ir.sequence'].sudo().next_by_code('truck.waybill.sequence')
        #         if not sequence:
        #             raise exceptions.ValidationError(_('Please configure Truck Way Bill sequence'))
        #         vals['bol_no'] = sequence
        #         vals['sn_no'] = sequence
        #         vals['display_name'] = sequence
        # else:
        #     vals['sn_no'] = self.env['ir.sequence'].next_by_code('sn')
        #
        # return super(BillOfLading, self).create(vals)
        vals['sn_no'] = self.env['ir.sequence'].next_by_code('sn')
        res = super(BillOfLading, self).create(vals)
        return res


    def write(self, value):
        if self.direction == 'export' and self.bol_no:
            if not self.hbl_no:
                value['hbl_no'] = self.bol_no

        # if 'bol_no' in value and self.service_type == 'land':
        #     raise exceptions.ValidationError(_('You cannot modify the TWB number'))

        return super(BillOfLading, self).write(value)

    @api.multi
    def action_send_booking_confirmation(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight_2', 'email_template_edi_bl_booking_confirmation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.bol',
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




    @api.multi
    def action_send_booking_confirmation_si(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        #if self.carrier_booking_no:
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight_2', 'email_template_edi_bl_booking_confirmation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        excel_template_id = self.env.ref('sci_goexcel_freight_2.action_si_bol_report_xlsx').render_xlsx(self.ids,[])
        data_record = base64.b64encode(excel_template_id[0])
        file_name = 'SI ' + self.bol_no + '.xlsx'
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
            'default_model': 'freight.bol',
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
        #else:
        #    raise exceptions.ValidationError('Carrier Booking No must not be empty!!!')


    @api.multi
    def action_send_bl_xls(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        #if self.carrier_booking_no:
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('sci_goexcel_freight_2', 'email_template_bol')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        excel_template_id = self.env.ref('sci_goexcel_freight_2.action_bol_report_xls').render_xlsx(self.ids,[])
        data_record = base64.b64encode(excel_template_id[0])
        file_name = 'SI ' + self.bol_no + '.xlsx'
        ir_values = {
            'name': "Bill of Lading",
            'type': 'binary',
            'datas': data_record,
            'datas_fname': file_name,
            'store_fname': 'Bill of Lading',
            'mimetype': 'application/xlsx',
        }
        excel_attachment = self.env['ir.attachment'].create(ir_values)
        template = self.env['mail.template'].browse(template_id)
        template.attachment_ids = False
        template.attachment_ids = [(4, excel_attachment.id)]
        ctx = {
            'default_model': 'freight.bol',
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
        #self.shipment_booking_status = '02'
        #else:
        #    raise exceptions.ValidationError('Carrier Booking No must not be empty!!!')

    @api.onchange('shipper_id')
    def onchange_shipper_id(self):
        adr = ''
        if self.shipper_id:
            # if self.shipper_id_address_input is False or '':
            adr += self.shipper_id.name + "\n"
            if self.shipper_id.street:
                adr += self.shipper_id.street
            if self.shipper_id.street2:
                adr += ' ' + self.shipper_id.street2
            if self.shipper_id.zip:
                adr += ' ' + self.shipper_id.zip
            if self.shipper_id.city:
                adr += ' ' + self.shipper_id.city
            if self.shipper_id.state_id:
                adr += ', ' + self.shipper_id.state_id.name
            if self.shipper_id.country_id:
                adr += ', ' + self.shipper_id.country_id.name + "\n"
            if not self.shipper_id.country_id:
                adr += "\n"
            if self.shipper_id.phone:
                adr += 'Phone: ' + self.shipper_id.phone
            elif self.shipper_id.mobile:
                adr += '. Mobile: ' + self.shipper_id.mobile
            # if self.shipper_id.country_id:
            #     adr += ', ' + self.shipper_id.country_id.name
            # _logger.warning("adr" + adr)
            self.shipper = adr

    @api.onchange('consignee_id')
    def onchange_consignee_id(self):
        adr = ''
        if self.consignee_id:
            # if self.consignee_address_input is False or '':
            adr += self.consignee_id.name + "\n"
            if self.consignee_id.street:
                adr += self.consignee_id.street
            if self.consignee_id.street2:
                adr += ' ' + self.consignee_id.street2
            if self.consignee_id.zip:
                adr += ' ' + self.consignee_id.zip
            if self.consignee_id.city:
                adr += ' ' + self.consignee_id.city
            if self.consignee_id.state_id:
                adr += ', ' + self.consignee_id.state_id.name
            if self.consignee_id.country_id:
                adr += ', ' + self.consignee_id.country_id.name + "\n"
            if not self.consignee_id.country_id:
                adr += "\n"
            if self.consignee_id.phone:
                adr += 'Phone: ' + self.consignee_id.phone
            elif self.consignee_id.mobile:
                adr += '. Mobile: ' + self.consignee_id.mobile
            self.consignee = adr


    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
            bol = self.env['freight.bol'].search([('bol_no', '=', self.bol_no)])
            cost_profit_obj = self.env['freight.bol.cost.profit']
            if sq and self.direction == 'export':
                self.shipper_id = sq.partner_id.id
            elif sq and self.direction == 'export':
                self.consignee_id = sq.partner_id.id
            for line in sq.order_line:
                if line.product_id:
                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    else:
                        price_unit = line.price_unit
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'product_name': line.name or False,
                        'bol_id': bol.id or '',
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                    })
                    bol.write({'cost_profit_ids': cost_profit_line or False})

    @api.onchange('oversea_agent')
    def onchange_oversea_agent(self):
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
            self.routing_instruction = oversea_agent_adr

class CostProfit(models.Model):
    _inherit = 'freight.bol.cost.profit'

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     if not self.product_id:
    #         return {'domain': {'uom_id': []}}
    #
    #     vals = {}
    #     domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
    #     if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
    #         vals['uom_id'] = self.product_id.uom_id
    #         vals['product_name'] = self.product_id.name
    #
    #     self.update(vals)
    #
    #     if self.bol_id.booking_ref.lcl_consolidation:
    #         if self.product_id:
    #             if self.bol_id.booking_ref:
    #                 total_freight_rate = 0.00
    #                 total_volume = 0.00
    #                 cost_currency_rate = 1.00
    #                 cost_currency = False
    #                 #get the freight price from the master booking
    #                 for cost_profit_id in self.bol_id.booking_ref.cost_profit_ids:
    #                     if cost_profit_id.product_id.id == self.product_id.id:
    #                         total_freight_rate = cost_profit_id.cost_total
    #                         cost_currency_rate = cost_profit_id.cost_currency_rate
    #                         cost_currency = cost_profit_id.cost_currency.id
    #                         break
    #                 #print('>>>>>> _onchange_product_id total freight rate=', total_freight_rate, ' , cost_currency_rate=',
    #                       #cost_currency_rate, ' cost_currency=', cost_currency)
    #                 #get all the HBL for the booking job
    #                 bols = self.env['freight.bol'].search([('booking_ref', '=', self.bol_id.booking_ref.id),])
    #                 #print('>>>>>>>> _onchange_product_id freight rate=', freight_rate)
    #                 #print('>>>>>>>> _onchange_product_id len bol=', len(bols))
    #                 for bol in bols:
    #                     #print('>>>>>>>> _onchange_product_id bol no=', bol.bol_no)
    #                     #print('>>>>>>>> _onchange_product_id exp_gross_weight=', bol.cargo_line_ids[0].exp_gross_weight,
    #                     #      ' , exp_vol=', bol.cargo_line_ids[0].exp_vol)
    #                     if bol.cargo_line_ids:
    #                         #print('>>>>>>>> _onchange_product_id exp_gross_weight=', bol.cargo_line_ids[0].exp_gross_weight,
    #                         #      ' , exp_vol=', bol.cargo_line_ids[0].exp_vol)
    #                         exp_gross_weight_tonne = 0.00
    #                         chargeable_vol = 0.00
    #                         if bol.cargo_line_ids[0].exp_gross_weight > 0:
    #                             exp_gross_weight_tonne = float_round(bol.cargo_line_ids[0].exp_gross_weight / 1000, 2,
    #                                                                  rounding_method='HALF-UP')
    #                             if exp_gross_weight_tonne > bol.cargo_line_ids[0].exp_vol:
    #                                 chargeable_vol = exp_gross_weight_tonne
    #                             else:
    #                                 chargeable_vol = bol.cargo_line_ids[0].exp_vol
    #                         else:
    #                             chargeable_vol = bol.cargo_line_ids[0].exp_vol
    #                         total_volume += chargeable_vol
    #
    #                         #print('>>>>>>>> _onchange_product_id total_volume 1=', total_volume, ' , chargeable_vol 1=', chargeable_vol)
    #                 #print('>>>>>>>> _onchange_product_id total_volume=', total_volume)
    #                 #print('>>>>>>>> _onchange_product_id total_volume 1=', total_volume)
    #                 #for current BOL, populate the chargeable weight
    #                 if self.bol_id.cargo_line_ids:
    #                     if self.bol_id.cargo_line_ids[0].exp_vol or self.bol_id.cargo_line_ids[0].exp_gross_weight:
    #                         exp_gross_weight_tonne = 0.00
    #                         chargeable_vol = 0.00
    #                         if self.bol_id.cargo_line_ids[0].exp_gross_weight > 0:
    #                             #print('>>>>>>>> _onchange_product_id exp_gross_weight=', self.bol_id.cargo_line_ids[0].exp_gross_weight)
    #                             exp_gross_weight_tonne = float_round(self.bol_id.cargo_line_ids[0].exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
    #                             #print('>>>>>>>> _onchange_product_id exp_gross_weight tonne=', exp_gross_weight_tonne)
    #                             if exp_gross_weight_tonne > self.bol_id.cargo_line_ids[0].exp_vol:
    #                                 chargeable_vol = exp_gross_weight_tonne
    #                             else:
    #                                 chargeable_vol = self.bol_id.cargo_line_ids[0].exp_vol
    #                         else:
    #                             chargeable_vol = self.bol_id.cargo_line_ids[0].exp_vol
    #                         total_volume += chargeable_vol  #cannot get the volume from the above loop
    #                         #print('>>>>>>>> _onchange_product_id total_volume 2=', total_volume, ' , chargeable_vol=', chargeable_vol)
    #                         converted_cost_price = total_freight_rate / total_volume
    #                         cost_price = float_round(converted_cost_price / cost_currency_rate, 2,
    #                                                  rounding_method='HALF-UP')
    #
    #                         #print('>>>>>>>> _onchange_product_id cost_price=', cost_price, ' , converted_cost_price=', converted_cost_price)
    #                         self.update({
    #                             'cost_price': cost_price or 0.0,
    #                             'cost_qty': chargeable_vol,
    #                             'cost_currency': cost_currency,
    #                             'cost_amount': float_round(cost_price * chargeable_vol, 2,
    #                                                        rounding_method='HALF-UP'),
    #                             'cost_currency_rate': cost_currency_rate,
    #                         })

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'uom_id': []}}

        # sync UoM and name
        if self.uom_id != self.product_id.uom_id:
            self.uom_id = self.product_id.uom_id
            self.product_name = self.product_id.name

        # only for consolidated House B/Ls
        booking = self.bol_id.booking_ref
        if booking.lcl_consolidation:
            # fetch master cost
            master = booking.cost_profit_ids.filtered(lambda m: m.product_id == self.product_id)
            if not master:
                return
            total_rate = master.cost_total
            rate = master.cost_currency_rate or 1.0
            currency = master.cost_currency.id

            # sum volumes of all HBLs (floor 1 CBM)
            total_volume = 0.0
            for bol in booking.bol_ids:
                cargo = bol.cargo_line_ids and bol.cargo_line_ids[0]
                if not cargo:
                    continue
                wt = float_round(cargo.exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
                total_volume += max(wt, cargo.exp_vol, 1.0)

            if total_volume <= 0:
                return

            # this BOL’s share
            cargo0 = self.bol_id.cargo_line_ids and self.bol_id.cargo_line_ids[0]
            if cargo0:
                wt0 = float_round(cargo0.exp_gross_weight / 1000, 2, rounding_method='HALF-UP')
                cbm = max(wt0, cargo0.exp_vol, 1.0)
            else:
                cbm = 0.0

            unit_cost = float_round((total_rate / total_volume) / rate, 2, rounding_method='HALF-UP')
            amount = float_round(unit_cost * cbm, 2, rounding_method='HALF-UP')

            self.cost_price = unit_cost
            self.cost_qty = cbm
            self.cost_amount = amount
            self.cost_currency = currency
            self.cost_currency_rate = rate


class CargoLine(models.Model):
    _inherit = 'freight.bol.cargo'

    chargeable_weight = fields.Float(string='Chargeable Weight', default=0.0, help="This field is only visible for LCL consolidation")

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(CargoLine, self).write(vals)
        #TODO update to the Freight booking manifest
        # if 'packages_no' in vals:
        #     for bl in self.env['freight.bol'].search([('booking_ref', '=', self.operation_id2.id),]):
        #         if bl.cargo_line_ids:
        #             bl.cargo_line_ids[0].write({'packages_no_value' : vals['packages_no']})