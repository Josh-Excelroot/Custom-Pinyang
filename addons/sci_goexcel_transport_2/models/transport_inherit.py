from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class TransportRFT(models.Model):
    _inherit = "transport.rft"

    # job_type = fields.Many2one('transport.job.type', string='Job Type')
    temperature_type = fields.Many2one('temperature.type', string='Temperature Type')
    temperature_set_point = fields.Text(string="Temperature Set Point")
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
    rft_status = fields.Selection([('01', 'New'),
                                   ('02', 'Job Assigned'),
                                   ('03', 'Job Completed'),
                                   ('04', 'Invoicing Completed'),
                                   ('05', 'POD Attached'), ('06', 'Cancel'), ('07', 'On Hold')],
                                  string="RFT Status",
                                  default="01", copy=False,
                                  track_visibility='onchange', store=True)
    cold_reach = fields.Boolean(string="cr boolean")

    man_power = fields.Char(string="Man Power")
    man_power_count = fields.Selection([('0', '0'), ('1', '1'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')],
                                       string="Man Power Count",
                                       default="0")
    trip_type = fields.Many2one("trip.type", string="Trip Type")
    rft_job = fields.Many2one("transport.rft", string="RFT Job")
    vehicle = fields.Many2one("fleet.vehicle", string="Vehicle")
    rft_status_name = fields.Text(string="Status Name", Value='New')
    vehicle = fields.Many2one("fleet.vehicle", string="Vehicle")
    rft_status_name = fields.Text(string="Status Name", Value='New')
    delivery_rft_status = fields.Selection(related='rft_status', copy=False)
    container_line_ids = fields.One2many('rft.container.line', 'container_line_id', string="Trucking Cargo", copy=True,
                                         auto_join=True, track_visibility='always')


    @api.one
    @api.depends('cost_profit_ids_rft.sales_total')
    def _compute_pivot_sale_total_new(self):
        # _logger.warning('onchange_pivot_sale_total')
        for service in self.cost_profit_ids_rft:
            if service.product_id:
                self.pivot_sale_total = service.sales_total + self.pivot_sale_total

    @api.one
    @api.depends('cost_profit_ids_rft.cost_total')
    def _compute_pivot_cost_total_new(self):
        for service in self.cost_profit_ids_rft:
            if service.product_id:
                self.pivot_cost_total = service.cost_total + self.pivot_cost_total

    @api.one
    @api.depends('cost_profit_ids_rft.profit_total')
    def _compute_pivot_profit_total_new(self):
        for service in self.cost_profit_ids_rft:
            if service.product_id:
                self.pivot_profit_total = service.profit_total + self.pivot_profit_total

    @api.one
    @api.depends('pivot_profit_total')
    def _compute_pivot_margin_total_new(self):
        for service in self:
            if service.pivot_sale_total > 0:
                service.pivot_margin_total = (service.pivot_profit_total / service.pivot_sale_total) * 100

    def trip_summary(self):
        view = self.env.ref("sci_goexcel_transport_2.trip_summary_view_form")
        return {
            'name': 'Create',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trip.summary.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'parent_obj': self.id}

        }

    @api.onchange('trip_type')
    def onchange_trip_type(self):

        if self.trip_type.name == 'Cold Reach':
            self.cold_reach = True
        else:
            self.cold_reach = False

    @api.multi
    def name_get(self):
        result = []
        for rft in self:
            name = str(rft.rft_no)
            result.append((rft.id, name))
        return result

    @api.onchange('rft_status')
    def _onchange_rft_status(self):
        if self.rft_status == '01':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status")
        elif self.rft_status == '02':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status_job_assigned")
        elif self.rft_status == '03':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status_job_completed")
        elif self.rft_status == '04':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status_invoicing")
        elif self.rft_status == '05':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status_pod")
        elif self.rft_status == '06':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status_cancel")
        elif self.rft_status == '07':
            res = self.env["transport.rft"].search([('id', '=', self._origin.id)])
            self.send_email(res, "sci_goexcel_transport_2.email_template_rft_status")

    def get_email_ids_of_notification_parties(self):

        user1 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '01')])  # New RFT
        user2 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '02')])  # Job Assigned
        user3 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '03')])  # Job Completed
        user4 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '04')])  # Invoicing Completed
        user5 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '05')])  # POD Attached
        user6 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '06')])  # Cancel
        user7 = self.env["rft.job.status"].search([("rft_status_wizard", "=", '07')])  # On Hold

        if user1:

            notification_recipent = user1.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")


        elif user2:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user2.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

        elif user3:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user3.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

        elif user4:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user4.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

        elif user5:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user5.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

        elif user6:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user6.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

        elif user7:
            # notification_reciepents = user1.notification_parties
            notification_recipent = user7.notification_parties
            if len(notification_recipent) == 1:
                email = str([notification_recipent.email]).replace("[", "").replace("]", "")
            else:
                comma_separated_email = []
                for recipients in notification_recipent:
                    comma_separated_email.append(recipients.email)

                email = ",".join(comma_separated_email)
            return email.replace("'", "")

    def send_email(self, res, template):

        template = self.env.ref(template)
        if res.id:
            template.send_mail(res.id, force_send=True)



    # @api.multi
    # def action_reupdate_rft_invoice_one(self):
    #     #print('>>>>>>action_reupdate_booking_invoice_one')
    #     for operation in self:
    #         if operation.id:
    #             rfts = self.env['transport.rft'].search([
    #                 ('id', '=', operation.id),
    #             ])
    #             for rft in rfts:
    #                 # Get the invoices
    #                 # invoices = self.env['account.invoice'].search([
    #                 #     ('rft_id', '=', rft.id),
    #                 #     ('type', 'in', ['out_invoice', 'out_refund']),
    #                 #     ('state', '!=', 'cancel'),
    #                 # ])
    #                 vendor_bill_list = []
    #                 # Get the vendor bills
    #                 for cost_profit_line in rft.cost_profit_ids_rft:
    #                     for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                         if vendor_bill_line.type in ['in_invoice', 'in_refund']:
    #                             vendor_bill_list.append(vendor_bill_line.id)
    #                 #print('>>>>>>> vendor_bill_list len=', len(vendor_bill_list))
    #                 unique_vendor_bill_list = []
    #                 for i in vendor_bill_list:
    #                     if i not in unique_vendor_bill_list:
    #                         unique_vendor_bill_list.append(i)
    #                 #print('>>>>>>> unique_vendor_bill_list len=', len(unique_vendor_bill_list))
    #                 vbs = self.env['account.invoice'].search([
    #                     ('freight_booking', '=', rft.id),
    #                     ('type', 'in', ['in_invoice', 'in_refund']),
    #                     ('state', '!=', 'cancel'),
    #                 ])
    #                 #print('>>>>>>>>>>> _compute_invoices_numbers vendor bills')
    #                 invoice_name_list = []
    #                 for x in vbs:
    #                     invoice_name_list.append(x.id)
    #                 unique_list = []
    #                 for y in unique_vendor_bill_list:
    #                     # inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
    #                     if invoice_name_list and len(invoice_name_list) > 0:
    #                         if y not in invoice_name_list:
    #                             unique_list.append(y)
    #                             # self.action_create_invoice_line(inv, operation)
    #                     else:
    #                         unique_list.append(y)
    #                         # self.action_create_invoice_line(inv, operation)
    #                 for z in invoice_name_list:
    #                     # if z not in vendor_bill_list:
    #                     unique_list.append(z)
    #                 for k in unique_list:
    #                     inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
    #                     if inv:
    #                         #print('>>>>>>>>>> Write create vendor bills')
    #                         self.action_create_invoice_line(inv, rft)


class RFTCostProfit(models.Model):
    _inherit = 'rft.cost.profit'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        vals = {}
        # domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        # if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
        #    vals['uom_id'] = self.product_id.uom_id
        if self.product_id.name:
            if self.product_id.description_sale:
                vals['product_name'] = self.product_id.name + '\n' + self.product_id.description_sale
            else:
                vals['product_name'] = self.product_id.name

        self.update(vals)

        if self.product_id:
            self.update({
                'unit_price': self.product_id.list_price or 0.0,
                'cost_price': self.product_id.standard_price or 0.0
            })


class DispatchTrip(models.Model):
    _inherit = 'dispatch.trip'

    @api.onchange('vehicle')
    def _onchange_vehicle(self):
        if self.vehicle:
            rfts = self.env['transport.rft'].search([
                ('id', '=', self.rft_reference.id),
            ], limit=1)

            vehicles = self.env['fleet.vehicle'].search([
                ('id', '=', self.vehicle.id),
            ])
            # _logger.warning('vehicle len=' + str(len(vehicles)))
            for vehicle in vehicles:
                self.driver_id = vehicle.driver_id.id
                rfts.driver_id = vehicle.driver_id.display_name



