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

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'dot'), ('default', '=', True),
                                                                ('company_id', '=', self.company_id.id)], limit=1)
            if template:
                return template.template

    @api.model
    def create(self, vals):
        company = vals.get('company_id')
        template = self.env['sale.letter.template'].search([('doc_type', '=', 'dot'), ('default', '=', True),
                                                            ('company_id', '=', company)], limit=1)
        vals['dot_sale_term'] = template.template
        res = super(TransportRFT, self).create(vals)
        return res

    template_id = fields.Many2one('sale.letter.template', 'Template')
    dot_sale_term = fields.Html('T&C', default=_get_default_term)



    # @api.onchange('pivot_sale_total', 'pivot_cost_total')
    # def _onchange_cost_profit(self):
    #     self.action_reupdate_rft_invoice_one()


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





