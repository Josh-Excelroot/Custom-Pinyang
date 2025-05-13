from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
import logging
from odoo.tools import float_round
_logger = logging.getLogger(__name__)


class TransportRFT(models.Model):
    _name = 'transport.rft'
    _description = 'Transport RFT'
    _order = 'required_date_time desc, write_date desc'
    color = fields.Integer('Color Index', default=0, store=False)
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ##General
    rft_status = fields.Selection([('01', 'RFT Draft'),
                                   ('02', 'RFT Confirmed'),
                                   ('03', 'Dispatched'),
                                   ('04', 'In Transit'),
                                   ('05', 'Done'), ('06', 'Cancelled')], string="RFT Status", default="01", copy=False,
                                  track_visibility='onchange', store=True)
    delivery_rft_status = fields.Selection(related='rft_status', copy=False)

    origin = fields.Char(string='Source Document',
                         help="Reference of the document that linked to RFT.")
    rft_no = fields.Char(string='RFT No', copy=False, readonly=True, index=True)
    consignment_note_no = fields.Char(string='Consignment Note No',
                                      default=lambda self: self.env['ir.sequence'].next_by_code('cn'),
                                      copy=False, readonly=True, index=True)

    booking_no = fields.Char(string='Booking/BL No', track_visibility='onchange', copy=False)
    direction = fields.Selection([('import', 'Import'), ('export', 'Export'), ('point', 'Point to Point')], string='Direction',
                                 track_visibility='onchange')
    required_date_time = fields.Datetime(string='Required Date Time', track_visibility='onchange', copy=False,
                                         index=True)
    elapsed_day = fields.Char(string='Elapsed Days', copy=False, store=True, track_visibility='onchange', )
    sq_reference = fields.Many2one('sale.order', string='S.Q Reference', track_visibility='onchange', copy=False)
    booking_reference = fields.Many2one('freight.booking', string='Booking Job Reference', track_visibility='onchange',
                                        copy=False,
                                        index=True)
    driver_id = fields.Many2one('res.partner', string="Driver ID")
    truck_type = fields.Many2one('freight.truck', string="Truck type")


    # invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced_count', readonly=True)
    # vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_get_bill_count', readonly=True)
    # po_count = fields.Integer(string='Purchase Order Count', compute='_get_po_count', readonly=True)
    ##Party
    pickup_from = fields.Many2one('res.partner', string='Pick-Up From', track_visibility='onchange')
    pickup_from_address_input = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    pickup_from_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')

    delivery_to = fields.Many2one('res.partner', string='Delivery To', track_visibility='onchange')
    delivery_to_address_input = fields.Text(string='Delivery To Address', track_visibility='onchange')
    delivery_to_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')

    billing_address = fields.Many2one('res.partner', string='Customer', track_visibility='onchange')
    #    payment_term = fields.Many2one('account.payment.term', string='Payment Term', track_visibility='onchange')
    #    incoterm = fields.Many2one('freight.incoterm', string='Incoterm', track_visibility='onchange')

    shipper = fields.Many2one('res.partner', string='Shipper', help="The Party who shipped the freight, eg Exporter",
                              track_visibility='onchange')
    # shipper_address = fields.Char(string='Shipper Address')
    consignee = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight",
                                track_visibility='onchange')
    forwarding_agent = fields.Many2one('res.partner', string='Forwarding Agent',
                                       help="The third party to facilitate the freight forwarding",
                                       track_visibility='onchange')
    requested_by = fields.Many2one('res.partner', string='Requested By', track_visibility='onchange')
    # requested_by_1 = fields.Many2one('res.users', string='Requested By', track_visibility='onchange',
    #                                default=lambda self: self.env.user.id,)
    requested_by_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')

    customer_seal = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Customer Seal', copy=False,
                                     track_visibility='onchange')
    delivery_type = fields.Selection([('direct', 'Direct Delivery'), ('normal', 'Normal Delivery')],
                                     string='Delivery Type',
                                     track_visibility='onchange')
    direct_loading = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Direct Loading',
                                      track_visibility='onchange')
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')

    commodity = fields.Many2one('product.product', track_visibility='onchange')
    commodity1 = fields.Many2one('freight.commodity1', string='Commodity', track_visibility='onchange')
    commodity_type = fields.Selection([('dg', 'Dangerous Goods'), ('gg', 'General Goods')], string='Commodity Type',
                                      track_visibility='onchange')
    commodity_type1 = fields.Many2one('freight.commodity', string="Commodity Type",
                                      help="Dangerous Goods or General Goods", track_visibility='onchange')
    seal_no = fields.Char(string='Custom Seal No', track_visibility='onchange')
    accept_hour = fields.Many2one('transport.accept.hour', string="Accept Hour",
                                  help="Customer Working Hours",
                                  track_visibility='onchange')

    rft_note = fields.Text(string='Remarks', track_visibility='onchange', copy=False)
    trip_count = fields.Integer(compute='_compute_trip_count')
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced_count', readonly=True)
    ##Shipment Info (Ocean Freight)
    #
    empty_container_dropoff = fields.Many2one('transport.depot', string="Depot (Laden/Empty Container)",
                                              help="Depot or Port for Laden/Empty Container drop off/picku-p",
                                              track_visibility='onchange')
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', track_visibility='onchange')
    voyage_no = fields.Char(string='Voyage No', track_visibility='onchange')
    vessel_code = fields.Char(string='Vessel Code', track_visibility='onchange')
    port = fields.Many2one('freight.ports', string='Port of Loading/Discharge', track_visibility='onchange')
    vessel_eta_etd = fields.Date(string='Vessel ETA', track_visibility='onchange')
    vessel_etd = fields.Date(string='Vessel ETD', track_visibility='onchange')
    loading_eta = fields.Date(string='Loading ETA', track_visibility='onchange')
    container_operator = fields.Many2one('res.partner', string='Container Operator', track_visibility='onchange')

    # terminal = fields.Char(string='Terminal', track_visibility='onchange')
    # income_acc_id = fields.Many2one("account.account",
    #                                 string="Income Account", track_visibility='onchange')
    # expence_acc_id = fields.Many2one("account.account",
    #                                  string="Expense Account", track_visibility='onchange')
    container_line_ids = fields.One2many('rft.container.line', 'container_line_id', string="Container", copy=True,
                                         auto_join=True, track_visibility='always')
    cost_profit_ids_rft = fields.One2many('rft.cost.profit', 'rft_transport_id', string="Cost & Profit",
                                          copy=True, auto_join=True, track_visibility='always')
    packaging_line_ids = fields.One2many('rft.packaging.line', 'packaging_line_id', string="Container", copy=True,
                                         auto_join=True, track_visibility='always')
    equipment_line_ids = fields.One2many('rft.equipment.line', 'equipment_line_id', string="Equipment", copy=True,
                                         auto_join=True, track_visibility='always')
    manpower_line_ids = fields.One2many('rft.manpower.line', 'manpower_line_id', string="Manpower", copy=True,
                                        auto_join=True, track_visibility='always')

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", track_visibility='always', copy=False)
    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id,
                            track_visibility='onchange')
    sales_person = fields.Many2one('res.users', string="Salesperson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    use_packaging = fields.Boolean(string='use packaging', compute="_get_use_packaging",
                                   default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                       "sci_goexcel_transport.use_packaging"))
    use_manpower = fields.Boolean(string='use manpower', compute="_get_use_manpower",
                                  default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                      "sci_goexcel_transport.use_manpower"))
    use_equipment = fields.Boolean(string='use equipment', compute="_get_use_equipment",
                                   default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                       "sci_goexcel_transport.use_equipment"))

    shipping_agent = fields.Many2one('res.partner', string='Shipping Agent', track_visibility='onchange')

    # Dennis - 24/3/2022 12.0.1.0.1 - added for invoice amount and cost amount
    haulage = fields.Many2one('res.partner', string='Transporter', track_visibility='onchange')
    invoice_amount = fields.Float(string="Inv Amount", store=True, track_visibility='onchange')
    cost_amount = fields.Float(string="Cost Amt", store=True, track_visibility='onchange')
    invoice_no = fields.Char(string='Invoices No', store=True)

    invoice_status = fields.Selection([('01', 'New'),
                                       ('02', 'Partially Invoiced'),
                                       ('03', 'Fully Invoiced')],
                                      string="Invoice Status", default="01", copy=False,
                                      track_visibility='onchange')
    invoice_paid_status = fields.Selection([('01', 'New'),
                                            ('02', 'Partially Paid'),
                                            ('03', 'Fully Paid')],
                                           string="Invoice Paid Status", default="01", copy=False,
                                           track_visibility='onchange')
    billing_status = fields.Selection([('01', 'New'),
                                       ('02', 'Partially Invoiced'),
                                       ('03', 'Fully Invoiced')],
                                      string="Billing Status", default="01", copy=False,
                                      track_visibility='onchange')
    billing_paid_status = fields.Selection([('01', 'New'),
                                            ('02', 'Partially Paid'),
                                            ('03', 'Fully Paid')],
                                           string="Billing Paid Status", default="01", copy=False,
                                           track_visibility='onchange')
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_get_bill_count', copy=False)

    do_to_receive_date = fields.Date(string='DO To Receive Date', track_visibility='onchange', copy=False)
    do_file_name = fields.Char(string="DO File name", track_visibility='onchange', copy=False)
    do_attachment = fields.Binary(string="DO Attachment", track_visibility='onchange', copy=False)
    do_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)
    #do_no = fields.Char(string="DO No")
    #has_attachment = fields.Boolean(string="Has Attachment")

    pl_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    pl_file_name = fields.Char(string="File name", track_visibility='onchange', copy=False)
    pl_attachment = fields.Binary(string="CI/PL Documents", track_visibility='onchange', copy=False)
    pl_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)

    si_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    si_file_name = fields.Char(string="File name", track_visibility='onchange', copy=False)
    si_attachment = fields.Binary(string="NOA Documents", track_visibility='onchange', copy=False)
    si_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)

    ci_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    ci_file_name = fields.Char(string="File name", track_visibility='onchange')
    ci_attachment = fields.Binary(string="Permit Documents", track_visibility='onchange', copy=False)
    ci_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)

    # obl = fields.Boolean(track_visibility='onchange')
    # obl_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    # obl_file_name = fields.Char(string="OBL File name", track_visibility='onchange', copy=False)
    # obl_attachment = fields.Binary(string="Others Documents", track_visibility='onchange', copy=False)
    # obl_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)

    # cc = fields.Boolean(track_visibility='onchange')
    # cc_to_receive_date = fields.Date(string='Custom Docs To Receive Date', track_visibility='onchange', copy=False)
    # cc_file_name = fields.Char(string="CC File name", track_visibility='onchange', copy=False)
    # cc_attachment = fields.Binary(string="Custom Docs Attachment", track_visibility='onchange', copy=False)
    # cc_remark = fields.Text(string="Remark", track_visibility='onchange', copy=False)

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            #vendor_bill_list_temp = []
            for cost_profit_line in operation.cost_profit_ids_rft:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            invoices = self.env['account.invoice'].search([
                ('rft_id', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            #print('vendor bills:', len(invoices))
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)
            unique_list = []

            for y in unique_vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                #if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })


    @api.multi
    def operation_bill(self):
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            for cost_profit_line in operation.cost_profit_ids_rft:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            invoices = self.env['account.invoice'].search([
                ('rft_id', '=', operation.id),
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


    # @api.one
    # @api.depends('cost_profit_ids_rft.sales_total')
    # def _compute_invoices_no(self):
    #     for operation in self:
    #         # Get the invoices
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', 'in', ['out_invoice', 'out_refund']),
    #             ('state', '!=', 'cancel'),
    #         ])
    #         print('>>>>>>>> _compute_invoice_no invoices')
    #         if invoices:
    #             operation.invoices_no = ''
    #             for invoice in invoices:
    #                 if operation.invoices_no and len(operation.invoices_no) > 1:
    #                     if invoice.number:
    #                         operation.invoices_no = operation.invoices_no + ' ' + str(invoice.number)
    #                 else:
    #                     if invoice.number:
    #                         operation.invoices_no = str(invoice.number)

    # @api.one
    # @api.depends('cost_profit_ids_rft.sales_total')
    # def _compute_invoice_amount(self):
    #     for invoice in self.cost_profit_ids_rft:
    #         if invoice.amount_id:
    #             self.invoice_amount = invoice.amount_total + self.invoice_amount

    # @api.one
    # @api.depends('cost_profit_ids.sales_total')
    # def _compute_sale_total(self):
    #     # _logger.warning('onchange_sales_total')
    #     for service in self.cost_profit_ids:
    #         if service.product_id:
    #             self.sales_total = service.sale_total + self.sales_total


    @api.multi
    def _get_default_commodity_category(self):
        # print('_get_default_commodity_category')
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        # print('commodity_lines len=' + str(len(commodity_lines)))
        for commodity_line in commodity_lines:
            # _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.model
    def _set_department(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        department = employee_rec.department_id
        return department

    sales_team = fields.Many2one('crm.team', string="Sales Team")
    department = fields.Many2one('hr.department', string="Department", default=_set_department)

    @api.model
    def create(self, vals):
        vals['rft_no'] = self.env['ir.sequence'].next_by_code('rft')
        res = super(TransportRFT, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        result = []
        for rft in self:
            name = str(rft.rft_no)
        result.append((rft.id, name))
        return result

    @api.onchange('delivery_rft_status')
    def onchange_delivery_rft_status(self):
        self.rft_status = self.delivery_rft_status

    @api.onchange('delivery_to')
    def onchange_delivery_to(self):
        adr = ''
        if self.delivery_to:
            adr += self.delivery_to.name + "\n"
            if self.delivery_to.street:
                adr += self.delivery_to.street
            if self.delivery_to.street2:
                adr += ' ' + self.delivery_to.street2
            if self.delivery_to.zip:
                adr += ' ' + self.delivery_to.zip
            if self.delivery_to.city:
                adr += ' ' + self.delivery_to.city
            if self.delivery_to.state_id:
                adr += ', ' + self.delivery_to.state_id.name
            if self.delivery_to.country_id:
                adr += ', ' + self.delivery_to.country_id.name + "\n"
            if not self.delivery_to.country_id:
                adr += "\n"
            if self.delivery_to.phone:
                adr += 'Phone: ' + self.delivery_to.phone
            elif self.delivery_to.mobile:
                adr += '. Mobile: ' + self.delivery_to.mobile
            # if self.delivery_to.country_id:
            #     adr += ', ' + self.delivery_to.country_id.name
            # _logger.warning("adr" + adr)
            self.delivery_to_address_input = adr
            self.consignee = self.delivery_to

    @api.onchange('pickup_from')
    def onchange_pickup_from(self):
        adr = ''
        if self.pickup_from:
            adr += self.pickup_from.name + "\n"
            if self.pickup_from.street:
                adr += self.pickup_from.street
            if self.pickup_from.street2:
                adr += ' ' + self.pickup_from.street2
            if self.pickup_from.zip:
                adr += ' ' + self.pickup_from.zip
            if self.pickup_from.city:
                adr += ' ' + self.pickup_from.city
            if self.pickup_from.state_id:
                adr += ', ' + self.pickup_from.state_id.name
            if self.pickup_from.country_id:
                adr += ', ' + self.pickup_from.country_id.name + "\n"
            if not self.pickup_from.country_id:
                adr += "\n"
            if self.pickup_from.phone:
                adr += 'Phone: ' + self.pickup_from.phone
            elif self.pickup_from.mobile:
                adr += '. Mobile: ' + self.pickup_from.mobile
            self.pickup_from_address_input = adr
            self.billing_address = self.pickup_from
            self.shipper = self.pickup_from

    @api.multi
    def action_schedule_reminder(self, context=None):
        summary = context.get('summary')
        action = context.get('action')
        if action == 'do':
            date_deadline = self.do_to_receive_date
        self.env['mail.activity'].create({
            'summary': summary,
            'note': 'Please follow up!',
            'res_id': self.id,
            # 'res_model_id': self.id,
            'res_model_id': self.env.ref('sci_goexcel_transport.model_transport_rft').id,
            'user_id': self.env.user.id,
            'date_deadline': date_deadline,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            # 'activity_type_id': 2,
        })

    @api.onchange('required_date_time')
    def _onchange_required_date_time(self):
        if self.required_date_time:
            # days = self.booking_date_time - datetime.now().date()
            diff = self.required_date_time - datetime.now()
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            # _logger.warning('diff:' + str(diff))
            # total_sec = diff.total_seconds()
            # _logger.warning('total sec:' + str(total_sec))
            # total_min = float(total_sec / 60)
            # _logger.warning('total min:' + str(total_min))
            # total_day = total_min / 60 / 24
            # _logger.warning('total day:' + str(total_day))
            # _logger.warning('elapsed days:' + str(elapsed_days))
            print(total_day)
            self.elapsed_day = total_day
            # self.sudo().write({'elapsed_day': total_day})

    @api.model
    def _cron_elapsed_day(self):
        # yesterday_date = datetime.now().date()
        #  rfts = self.env['transport.rft'].search([
        #      ('required_date_time', '>', datetime.now()),
        #  ])
        rfts = self.env['transport.rft'].search([
            ('elapsed_day', '!=', '0'),
        ])
        # _logger.warning('len rfts=' + str(len(rfts)))
        for rft in rfts:
            if rft.required_date_time:
                diff = rft.required_date_time - datetime.now()
                # _logger.warning('diff:' + str(diff))
                diff_str = str(diff)
                end_pos = diff_str.find('.')
                total_day = diff_str[0:end_pos]
                # total_sec = diff.total_seconds()
                # total_min = float(total_sec / 60)
                # total_day = total_min / 60 / 24
                # _logger.warning('elapsed_days=' + str(elapsed_days))
                rft.elapsed_day = total_day
                # booking.write({'elapsed_day_booking': elapsed_days})

    @api.multi
    def action_cancel_rft(self):
        self.rft_status = '06'

    @api.multi
    def action_dispatch_trip(self):

        trip_obj = self.env['dispatch.trip']
        trip_manifest_obj = self.env['trip.manifest.line']
        # _logger.warning('action_copy_to_booking 1')
        trip_val = {
            'trip_status': '01',
            'load_type': 'ftl',
            'required_date_time': self.required_date_time or False,
            'shipping_instruction': self.rft_note or '',
            'pickup_from': self.pickup_from.id or False,
            'pickup_from_address_input': self.pickup_from_address_input or '',
            'delivery_to': self.delivery_to.id or False,
            'delivery_to_address_input': self.delivery_to_address_input or '',
            'rft_reference': self.id,
            'company_id': self.company_id.id,
            # 'sales_person': self.user_id.id
        }
        trip = trip_obj.create(trip_val)
        for line in self.container_line_ids:
            # _logger.warning('action_copy_to_booking 1')
            if line.container_product_id:
                # _logger.warning('action_copy_to_booking 2')
                trip_manifest_line = trip_manifest_obj.create({
                    'container_no': line.container_no or '',
                    'container_id': line.container_id.id or False,
                    'manifest_product_id': line.container_product_id.id or False,
                    'manifest_product_name': line.container_product_name or False,
                    'manifest_line_id': trip.id,
                    'packages_no': line.packages_no or 0,
                    'exp_gross_weight': line.exp_gross_weight or 0,
                    'exp_vol': line.exp_vol or 0,
                    'required_date_time_line': line.required_date_time_line or False,
                    'container_operator_line': line.container_operator_line.id or False,
                    'accept_hour_line': line.accept_hour_line.id or False,
                    'remark_line': line.remark_line or '',
                })
                trip.write({'manifest_line_ids': trip_manifest_line or False})

        trip_packaging_line_obj = self.env['trip.packaging.line']
        for line in self.packaging_line_ids:
            # _logger.warning('action_copy_to_booking 1')
            #           if line.container_product_id:
            # _logger.warning('action_copy_to_booking 2')
            trip_packaging_line = trip_packaging_line_obj.create({
                'packaging_line_id': trip.id,
                'packaging_product_id': line.packaging_product_id.id or False,
                'packaging_product_name': line.packaging_product_name or '',
                'packages_no': line.packages_no or '',
                'rft_reference': self.id,
                'required_date_time_line': line.required_date_time_line or False,
                'remark_line': line.remark_line or '',
            })
            # trip.write({'manifest_line_ids': trip_manifest_line or False})
            trip.write({'packaging_line_ids': trip_packaging_line or False})
            line.trip_reference = trip.id

        trip_equipment_line_obj = self.env['trip.equipment.line']
        for line in self.equipment_line_ids:
            # _logger.warning('action_copy_to_booking 1')
            #           if line.container_product_id:
            # _logger.warning('action_copy_to_booking 2')
            trip_equipment_line = trip_equipment_line_obj.create({
                'equipment_line_id': trip.id,
                'equipment_id': line.equipment_id.id or False,
                'equipment_name': line.equipment_name or '',
                'qty': line.qty or False,
                'vendor_id': line.vendor_id.id or False,
                'pickup_from_address_input_line': line.pickup_from_address_input_line or '',
                'delivery_to_address_input_line': line.delivery_to_address_input_line or '',
                'rft_reference': self.id,
                'required_date_time_line': line.required_date_time_line or False,
                'remark_line': line.remark_line or '',
            })
            # trip.write({'manifest_line_ids': trip_manifest_line or False})
            trip.write({'equipment_line_ids': trip_equipment_line or False})
            line.trip_reference = trip.id

        trip_manpower_line_obj = self.env['trip.manpower.line']
        for line in self.manpower_line_ids:
            # _logger.warning('action_copy_to_booking 1')
            #           if line.container_product_id:
            # _logger.warning('action_copy_to_booking 2')
            trip_manpower_line = trip_manpower_line_obj.create({
                'manpower_line_id': trip.id,
                'manpower_id': line.manpower_id.id or False,
                'manpower_name': line.manpower_name or '',
                'qty': line.qty or False,
                'vendor_id': line.vendor_id.id or False,
                'rft_reference': self.id,
                'required_date_time_line': line.required_date_time_line or False,
                'remark_line': line.remark_line or '',
            })
            # trip.write({'manifest_line_ids': trip_manifest_line or False})
            trip.write({'manpower_line_ids': trip_manpower_line or False})
            line.trip_reference = trip.id

        self.rft_status = '03'

    @api.multi
    def action_create_invoice(self):
        """Create Invoice for the RFT"""
        self.ensure_one()
        view = self.env.ref('sci_goexcel_transport.rft_invoice_view_form')
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rft.invoice.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(rft_id=self.id),
        }

        # inv_obj = self.env['account.invoice']
        # inv_line_obj = self.env['account.invoice.line']
        # if not self.analytic_account_id:
        #     values = {
        #         'partner_id': self.billing_address.id,
        #         'name': '%s' % self.rft_no,
        #         'company_id': self.company_id.id,
        #     }
        #     analytic_account = self.env['account.analytic.account'].sudo().create(values)
        #     self.write({'analytic_account_id': analytic_account.id,})
        #
        # inv_val = {
        #     'type': 'out_invoice',
        #     #     'transaction_ids': self.ids,
        #     'state': 'draft',
        #     'partner_id': self.billing_address.id or False,
        #     'date_invoice': fields.Date.context_today(self),
        #     'origin': self.rft_no,
        #     'rft_id': self.id,
        #     'account_id': self.billing_address.property_account_receivable_id.id or False,
        #     'company_id': self.company_id.id
        # }
        #
        # invoice = inv_obj.create(inv_val)
        # for line in self.cost_profit_ids_rft:
        #     sale_unit_price_converted = line.unit_price * line.sales_currency_rate
        #     if line.product_id.property_account_income_id:
        #         account_id = line.product_id.property_account_income_id
        #     elif line.product_id.categ_id.property_account_income_categ_id:
        #         account_id = line.product_id.categ_id.property_account_income_categ_id
        #     inv_line = inv_line_obj.create({
        #         'invoice_id': invoice.id or False,
        #         'account_id': account_id.id or False,
        #         'name': line.product_id.name or '',
        #         'product_id': line.product_id.id or False,
        #         'quantity': line.sales_qty or 0.0,
        #         # 'uom_id': line.uom_id.id or False,
        #         'price_unit': sale_unit_price_converted or 0.0,
        #         'account_analytic_id': self.analytic_account_id.id,
        #     })
        #     line.write({'invoice_id': invoice.id or False,
        #                 'inv_line_id': inv_line.id or False})


    @api.multi
    def action_create_vendor_bill(self):
        vendor_po = self.cost_profit_ids_rft.filtered(lambda c: c.vendor_id)
        #print('>>>>>>>> action_create_vendor_bill vendor_po=', str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.billing_address.id,
                'name': '%s' % self.booking_no,
                # 'partner_id': self.customer_name.id,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            #print(line.vendor_bill_id)
            #print('line.vendor_id=', line.vendor_id.name)
            if line.vendor_id != vendor_id:
                #print('not same partner')
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
                    #print('combine lines')
                    if not vb_line.invoiced:
                        account_id = False
                        price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        #print(vb_line)
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            #'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'rft_id': self.id,
                            'booking_line_id': vb_line.id,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.invoiced = True
                        # print('vendor_id=' + vendor_id.name)
                if value:
                    vendor_bill_id = vb.create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        #  'default_purchase_id': self.booking_no,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.booking_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'rft_id': self.id,
                    })
                for new_vendor_bill in vendor_bill_created:
                    new_vendor_bill.vendor_bill_id = vendor_bill_id.id
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')


    @api.multi
    def operation_invoices(self):
        """Show Invoice for smart Button."""
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('partner_id', '=', operation.billing_address.id),
                ('origin', '=', self.rft_no),
                ('type', '=', 'out_invoice'),
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
                ('partner_id', '=', operation.billing_address.id),
                ('origin', '=', operation.rft_no),
                ('type', '=', 'out_invoice'),
            ])

        self.update({
            'invoice_count': len(invoices),
        })

    @api.multi
    def action_dispatch_trip_ltl(self):

        trip_obj = self.env['dispatch.trip']
        trip_manifest_obj = self.env['trip.manifest.line.ltl']
        # _logger.warning('action_copy_to_booking 1')
        trip_val = {
            'trip_status': '01',
            'load_type': 'ltl',
            'required_date_time': self.required_date_time or False,
            # 'shipping_instruction': self.rft_note or '',
            # 'pickup_from': self.pickup_from.id or False,
            'pickup_from_address_input': self.pickup_from_address_input or '',
            # 'delivery_to': self.delivery_to.id or False,
            'delivery_to_address_input': self.delivery_to_address_input or '',
            # 'rft_reference': self.id,
            'company_id': self.company_id.id,
            # 'sales_person': self.user_id.id
        }
        trip = trip_obj.create(trip_val)
        for line in self.container_line_ids:
            # _logger.warning('action_copy_to_booking 1')
            #           if line.container_product_id:
            # _logger.warning('action_copy_to_booking 2')
            trip_manifest_line = trip_manifest_obj.create({
                'rft_reference_line': self.id,
                'manifest_line_id_ltl': trip.id,
                'pickup_from_line': self.pickup_from.id or False,
                'pickup_from_address_input_line': self.pickup_from_address_input or '',
                'delivery_to_line': self.delivery_to.id or False,
                'delivery_to_address_input_line': self.delivery_to_address_input or '',
                'packages_no': line.packages_no or 0,
                'exp_gross_weight': line.exp_gross_weight or 0,
                'required_date_time_line': line.required_date_time_line or False,
                'accept_hour_line': line.accept_hour_line.id or False,
                'remark_line': line.remark_line or '',
            })
            # trip.write({'manifest_line_ids': trip_manifest_line or False})
            trip.write({'manifest_line_ids_ltl': trip_manifest_line or False})
            line.trip_reference = trip.id

        self.rft_status = '03'

    @api.multi
    def _compute_trip_count(self):
        for trip in self:
            trips = self.env['dispatch.trip'].search([
                ('rft_reference', '=', trip.id),
            ])
            trip.trip_count = len(trips)

    @api.multi
    def action_set_status_in_transit(self):
        return self.write({'rft_status': '04'})

    @api.multi
    def _get_use_packaging(self):
        use_packaging = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_packaging")
        for record in self:
            record.use_packaging = use_packaging

    @api.multi
    def _get_use_manpower(self):
        use_manpower = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_manpower")
        # _logger.warning("use_manpower=" + str(use_manpower))
        for record in self:
            record.use_manpower = use_manpower

    @api.multi
    def _get_use_equipment(self):
        use_equipment = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_equipment")
        # _logger.warning("use_equipment=" + str(use_equipment))
        for record in self:
            record.use_equipment = use_equipment

    @api.multi
    def action_send_rft(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        if self.rft_no:
            self.rft_status = '02'
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_transport', 'email_template_rft')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'transport.rft',
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
            self.rft_status = '02'
        else:
            raise exceptions.ValidationError('Carrier Booking No must not be empty!!!')

    @api.multi
    def action_send_do(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        #print(self.pickup_from_address_input)
        self.ensure_one()
        if self.rft_no:
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_transport', 'email_template_edi_do')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'transport.rft',
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

    delivery_instruction = fields.Text(string='Delivery Instruction', track_visibility='onchange')


class RFTContainerLine(models.Model):
    _name = 'rft.container.line'
    _description = 'Container Line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    # rec_name = 'container_line_id'

    sequence = fields.Integer(string="sequence")
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    container_id = fields.Many2one('product.product', string="Container Type", track_visibility='onchange')
    container_line_id = fields.Many2one('transport.rft', string='RFT Container Line', required=True, ondelete='cascade',
                                        index=True, copy=False)
    trip_reference = fields.Many2one('dispatch.trip', string="Trip", track_visibility='onchange', copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')
    container_product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    container_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="No. of Packages", help="Eg, Carton", track_visibility='onchange')
    packages_no_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)",
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_vol = fields.Float(string="Volume",
                           help="Volume/Dimension", track_visibility='onchange')
    container_operator_line = fields.Many2one('res.partner', string="Container Operator")
    accept_hour_line = fields.Many2one('transport.accept.hour', string="Accept Hour",
                                       help="Customer Working Hours",
                                       track_visibility='onchange')
    remark_line = fields.Text(string='Remarks', track_visibility='onchange')
    pickup_from_address = fields.Text(string='Pick-Up From', track_visibility='onchange')
    delivery_to_address = fields.Text(string='Delivery To', track_visibility='onchange')
    lorry_no = fields.Char(string="Lorry No.", track_visibility='onchange')

    # @api.onchange('container_line_id')
    # def _onchange_container_line_id(self):
    #     vals = {}
    #     vals['required_date_time_line'] = self.container_line_id.required_date_time
    #     vals['container_operator_line'] = self.container_line_id.container_operator
    #     vals['accept_hour_line'] = self.container_line_id.accept_hour
    #     vals['remark_line'] = self.container_line_id.remark
    #     self.update(vals)

    @api.onchange('container_product_id')
    def _onchange_container_product_id(self):
        vals = {}
        vals['container_product_name'] = self.container_product_id.name
        self.update(vals)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(RFTContainerLine, self).create(vals)
        print(res)
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_id"):
            content = content + "  \u2022 Container Type: " + str(vals.get("container_id")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("container_product_id"):
            content = content + "  \u2022 Product: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Volume: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("container_operator_line"):
            content = content + "  \u2022 Container Operator: " + str(vals.get("container_operator_line")) + "<br/>"
        if vals.get("accept_hour_line"):
            content = content + "  \u2022 Accept Hour: " + str(vals.get("accept_hour_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.container_line_id.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(RFTContainerLine, self).write(vals)
        print(res)
        # _logger.warning("after super write")
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_id"):
            content = content + "  \u2022 Container Type: " + str(vals.get("container_id")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("container_product_id"):
            content = content + "  \u2022 Product: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Volume: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("container_operator_line"):
            content = content + "  \u2022 Container Operator: " + str(vals.get("container_operator_line")) + "<br/>"
        if vals.get("accept_hour_line"):
            content = content + "  \u2022 Accept Hour: " + str(vals.get("accept_hour_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.container_line_id.message_post(body=content)

        return res


class RFTCostProfit(models.Model):
    _name = 'rft.cost.profit'
    _description = "RFT Cost & Profit"
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    # _order = 'booking_id, sequence, id'

    sequence = fields.Integer(string="sequence")
    rft_transport_id = fields.Many2one('transport.rft', string='RFT Reference', required=True, ondelete='cascade',
                                       index=True,
                                       copy=False)
    product_id = fields.Many2one('product.product', string="Product", track_visibility='onchange')
    product_name = fields.Text(string="Description", track_visibility='onchange')
    sales_qty = fields.Integer(string='Qty', default="1", track_visibility='onchange')
    unit_price = fields.Float(string="Unit Rate", track_visibility='onchange')

    sales_currency = fields.Many2one('res.currency', 'Currency',
                                     default=lambda self: self.env.user.company_id.currency_id.id,
                                     track_visibility='onchange')
    # profit_currency = fields.Many2one('res.currency', string="Curr")
    sales_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    # sale amount
    sales_amount = fields.Float(string="Amt",
                                compute="_compute_sales_amount", store=True, track_visibility='onchange')
    sales_total = fields.Float(string="Total Sales",
                               compute="_compute_sales_total", store=True, track_visibility='onchange')
    cost_qty = fields.Integer(string='Qty', default="1", track_visibility='onchange')
    cost_price = fields.Float(string="Unit Price", track_visibility='onchange')
    # cost_gst = fields.Selection([('zer', 'ZER')], string="Tax", default="zer", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    cost_currency = fields.Many2one('res.currency', string="Curr", required=True,
                                    default=lambda self: self.env.user.company_id.currency_id.id,
                                    track_visibility='onchange')
    cost_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    cost_amount = fields.Float(string="Amt",
                               compute="_compute_cost_amount", store=True, track_visibility='onchange')
    cost_total = fields.Float(string="Total Cost",
                              compute="_compute_cost_total", store=True, track_visibility='onchange')
    profit_total = fields.Float(string="Total Profit",
                                compute="_compute_profit_total", store=True, track_visibility='onchange')

    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    sale_currency_rate = fields.Float(string='Rate', default="1.000000", digit=(12,6))
    cost_currency_rate = fields.Float(string='Rate', default="1.000000", digit=(12,6))
    invoiced = fields.Boolean(string='Billed', copy=False)
    is_billed = fields.Char('Is Biiled?', compute='_compute_is_billed', store=True)
    added_to_invoice = fields.Boolean(string='Invoiced', copy=False)
    invoice_paid = fields.Boolean(string='Invoice Paid', copy=False)
    vendor_bill_ids = fields.Many2many('account.invoice', string="Vendor Bill List", copy=False)
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    is_billed = fields.Char('Is Biiled?', compute='_compute_is_billed', store=True)

    @api.one
    def _set_access_for_invoiced(self):
        if self.env['res.users'].has_group('account.group_account_manager'):
            self.invoiced_readonly = False
        else:
            self.invoiced_readonly = True

    invoiced_readonly = fields.Boolean(compute="_set_access_for_invoiced",
                                       string='Is user able to modify invoiced?')
    paid = fields.Boolean(string='Paid', copy=False)
    is_paid = fields.Char('Is Paid?', compute='_compute_is_paid', store=True)


    @api.multi
    @api.depends('invoiced')
    def _compute_is_billed(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'Y'
                elif not cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'N'

    @api.multi
    @api.depends('paid')
    def _compute_is_paid(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.paid:
                    cost_profit_line.is_paid = 'Y'
                elif not cost_profit_line.paid:
                    cost_profit_line.is_paid = 'N'


    @api.depends('sales_qty', 'unit_price')
    def _compute_sales_amount(self):
        for service in self:
            if service.product_id:
                amount = service.sales_qty * service.unit_price
                service.sales_amount = float_round(amount, 2,
                                                    rounding_method='HALF-UP') or 0.0
                #service.sales_amount = service.sales_qty * service.unit_price or 0.0

    @api.depends('cost_qty', 'cost_price')
    def _compute_cost_amount(self):
        for service in self:
            if service.product_id:

                #service.cost_amount = service.cost_qty * service.cost_price or 0.0
                amount = service.cost_qty * service.cost_price
                service.cost_amount = float_round(amount, 2,
                                                  rounding_method='HALF-UP') or 0.0


    @api.depends('sales_amount', 'sale_currency_rate')
    def _compute_sales_total(self):
        for service in self:
            if service.product_id:
                #service.sales_total = service.sales_amount * service.sales_currency_rate or 0.0
                amount = service.sales_amount * service.sale_currency_rate
                print('>>>>>>>  _compute_sales_total=', amount)
                service.sales_total = float_round(amount, 2, rounding_method='HALF-UP') or 0.0


    @api.depends('cost_amount', 'cost_currency_rate')
    def _compute_cost_total(self):
        for service in self:
            if service.product_id:
                amount = service.cost_amount * service.cost_currency_rate or 0.0
                service.cost_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                service.profit_total = service.sales_total - service.cost_total or 0.0


    @api.depends('cost_total', 'sales_total')
    def _compute_profit_total(self):
        for service in self:
            if service.product_id:
                service.profit_total = service.sales_total - service.cost_total or 0.0


    @api.onchange('sales_currency_rate')
    def _onchange_profit_currency_rate(self):
        for service in self:
            if service.product_id:
                service.sales_total = service.sales_amount * service.sales_currency_rate or 0.0

    @api.onchange('sales_amount')
    def _onchange_sales_amount(self):
        for service in self:
            if service.product_id:
                service.sales_total = service.sales_amount * service.sales_currency_rate or 0.0
                service.profit_total = service.sales_total - service.cost_total or 0.0

    @api.onchange('cost_amount')
    def _onchange_cost_amount(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sales_total - service.cost_total or 0.0

    @api.onchange('cost_currency_rate')
    def _onchange_cost_currency_rate(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sales_total - service.cost_total or 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return

        vals = {}
        # domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        # if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
        #    vals['uom_id'] = self.product_id.uom_id
        vals['product_name'] = self.product_id.name

        self.update(vals)

        if self.product_id:
            self.update({
                'unit_price': self.product_id.list_price or 0.0,
                'cost_price': self.product_id.standard_price or 0.0
            })

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(RFTCostProfit, self).create(vals)
        content = ""
        if vals.get("product_id"):
            content = content + "  \u2022 Product: " + str(vals.get("product_id")) + "<br/>"
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("sales_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("sales_qty")) + "<br/>"
        if vals.get("unit_price"):
            content = content + "  \u2022 Unit Rate: " + str(vals.get("unit_price")) + "<br/>"
        if vals.get("sales_amount"):
            content = content + "  \u2022 Amt: " + str(vals.get("sales_amount")) + "<br/>"
        if vals.get("sales_currency"):
            content = content + "  \u2022 Currency: " + str(vals.get("sales_currency")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("cost_currency"):
            content = content + "  \u2022 Curr: " + str(vals.get("cost_currency")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.rft_transport_id.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(RFTCostProfit, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("product_id"):
            content = content + "  \u2022 Product: " + str(vals.get("product_id")) + "<br/>"
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("sales_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("sales_qty")) + "<br/>"
        if vals.get("unit_price"):
            content = content + "  \u2022 Unit Rate: " + str(vals.get("unit_price")) + "<br/>"
        if vals.get("sales_amount"):
            content = content + "  \u2022 Amt: " + str(vals.get("sales_amount")) + "<br/>"
        if vals.get("sales_currency"):
            content = content + "  \u2022 Currency: " + str(vals.get("sales_currency")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("cost_currency"):
            content = content + "  \u2022 Curr: " + str(vals.get("cost_currency")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.rft_transport_id.message_post(body=content)

        return res


class RFTPackagingLine(models.Model):
    _name = 'rft.packaging.line'
    _description = 'Packaging Line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    # rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    packaging_line_id = fields.Many2one('transport.rft', string='RFT Packaging Line', required=True, ondelete='cascade',
                                        index=True, copy=False)
    packaging_product_id = fields.Many2one('product.product', string='Packaging', track_visibility='onchange')
    packaging_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="Qty", track_visibility='onchange')
    trip_reference = fields.Many2one('dispatch.trip', string="Trip", track_visibility='onchange', copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')

    @api.onchange('packaging_product_id')
    def _onchange_packaging_product_id(self):
        vals = {}
        vals['packaging_product_name'] = self.packaging_product_id.name
        self.update(vals)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(RFTPackagingLine, self).create(vals)
        content = ""
        if vals.get("packaging_product_id"):
            content = content + "  \u2022 Packaging: " + str(vals.get("packaging_product_id")) + "<br/>"
        if vals.get("packaging_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("packaging_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 Qty: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.packaging_line_id.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(RFTPackagingLine, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("packaging_product_id"):
            content = content + "  \u2022 Packaging: " + str(vals.get("packaging_product_id")) + "<br/>"
        if vals.get("packaging_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("packaging_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 Qty: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.packaging_line_id.message_post(body=content)

        return res


class RFTEquipmentLine(models.Model):
    _name = 'rft.equipment.line'
    _description = 'Equipment Line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    # rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    equipment_line_id = fields.Many2one('transport.rft', string='RFT Equipment Line', required=True, ondelete='cascade',
                                        index=True, copy=False)
    equipment_id = fields.Many2one('fleet.vehicle', string='Equipment & Tools', track_visibility='onchange')
    equipment_name = fields.Text(string='Description', track_visibility='onchange')
    qty = fields.Integer(string="Qty", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    trip_reference = fields.Many2one('dispatch.trip', string="Trip", track_visibility='onchange', copy=False)
    pickup_from_address_input_line = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    delivery_to_address_input_line = fields.Text(string='Delivery To Address', track_visibility='onchange')
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        vals = {}
        vals['equipment_name'] = self.equipment_id.name
        self.update(vals)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(RFTEquipmentLine, self).create(vals)
        content = ""
        if vals.get("equipment_id"):
            content = content + "  \u2022 Equipment & Tools: " + str(vals.get("equipment_id")) + "<br/>"
        if vals.get("equipment_name"):
            content = content + "  \u2022 Description: " + str(vals.get("equipment_name")) + "<br/>"
        if vals.get("qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("qty")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("pickup_from_address_input_line"):
            content = content + "  \u2022 Pick-Up Address: " + str(vals.get("pickup_from_address_input_line")) + "<br/>"
        if vals.get("delivery_to_address_input_line"):
            content = content + "  \u2022 Delivery To Address: " + str(
                vals.get("delivery_to_address_input_line")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.equipment_line_id.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(RFTEquipmentLine, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("equipment_id"):
            content = content + "  \u2022 Equipment & Tools: " + str(vals.get("equipment_id")) + "<br/>"
        if vals.get("equipment_name"):
            content = content + "  \u2022 Description: " + str(vals.get("equipment_name")) + "<br/>"
        if vals.get("qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("qty")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("pickup_from_address_input_line"):
            content = content + "  \u2022 Pick-Up Address: " + str(vals.get("pickup_from_address_input_line")) + "<br/>"
        if vals.get("delivery_to_address_input_line"):
            content = content + "  \u2022 Delivery To Address: " + str(
                vals.get("delivery_to_address_input_line")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.equipment_line_id.message_post(body=content)

        return res


class RFTManPowerLine(models.Model):
    _name = 'rft.manpower.line'
    _description = 'Manpower Line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    # rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    manpower_line_id = fields.Many2one('transport.rft', string='RFT Manpower Line', required=True, ondelete='cascade',
                                       index=True, copy=False)
    manpower_id = fields.Many2one('product.product', string='ManPower', track_visibility='onchange')
    manpower_name = fields.Text(string='Description', track_visibility='onchange')
    qty = fields.Integer(string="Qty", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    trip_reference = fields.Many2one('dispatch.trip', string="Trip", track_visibility='onchange', copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')

    @api.onchange('manpower_id')
    def _onchange_manpower_id(self):
        vals = {}
        vals['manpower_name'] = self.manpower_id.name
        self.update(vals)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(RFTManPowerLine, self).create(vals)
        content = ""
        if vals.get("manpower_id"):
            content = content + "  \u2022 ManPower: " + str(vals.get("manpower_id")) + "<br/>"
        if vals.get("manpower_name"):
            content = content + "  \u2022 Description: " + str(vals.get("manpower_name")) + "<br/>"
        if vals.get("qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("qty")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.manpower_line_id.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(RFTManPowerLine, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("manpower_id"):
            content = content + "  \u2022 ManPower: " + str(vals.get("manpower_id")) + "<br/>"
        if vals.get("manpower_name"):
            content = content + "  \u2022 Description: " + str(vals.get("manpower_name")) + "<br/>"
        if vals.get("qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("qty")) + "<br/>"
        if vals.get("trip_reference"):
            content = content + "  \u2022 Trip: " + str(vals.get("trip_reference")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id")) + "<br/>"
        if vals.get("required_date_time_line"):
            content = content + "  \u2022 Required Date Time: " + str(vals.get("required_date_time_line")) + "<br/>"
        if vals.get("remark_line"):
            content = content + "  \u2022 Remarks: " + str(vals.get("remark_line")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.manpower_line_id.message_post(body=content)

        return res
