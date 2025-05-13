from odoo import api, fields, models
from datetime import date
from odoo.tools import float_round


class MultiQuotationWizard(models.TransientModel):
    _name = "multi.quotation.wizard"

    multi_quotation_lines = fields.One2many(
        "multi.quotation.wizard.line",
        "multi_quotation_id",
        string="Multi Quotation Lines",
    )

    # quotation_line_ids = fields.One2many('sale.order.line', 'order_id', string="Quotation Lines")
    quotation_line_ids = fields.One2many(
        "wizard.quotation.line",
        "wizard_quotation_id",
        string="Quotation Lines"
    )

    @api.model
    def default_get(self, fields):
        customer = self.env.context.get("customer")
        quotation_array = []
        booking_id = self.env.context.get("booking_id")
        booking = self.env["freight.booking"].search([("id", "=", booking_id), ])
        today = date.today()
        # TS 1/3/2023 - not based on today, but the booking ETA/ETD
        if booking.booking_date_time:
            today = booking.booking_date_time

        # Yulia 15042025 fetch all so based by state status
        # approved = Approved
        # sent = Quotation Sent
        # sale = Sale order
        # draft = quotation
        # confirm = Confirm
        quotations = self.env["sale.order"].search(
            [
                ("partner_id.id", "=", customer),
                ("validity_date", ">=", today),
                ("state", "in", ('approved', 'sent', 'draft','sent','sale','confirm')),
            ]
        )
        res = super(MultiQuotationWizard, self).default_get(fields)
        quotations_line_ids = []
        for quotation in quotations:
            total_amount = 0
            quotation_array.append(
                (
                    0,
                    0,
                    {
                        "quotation": quotation.id,
                        "date_order": quotation.date_order,
                        "validity_date": quotation.validity_date,
                        "sq_description": quotation.sq_description,
                        "total_amount": quotation.amount_total,
                        "add_to_line": False,
                        "customer": quotation.partner_id.id,
                    },
                )
            )

        res.update({"multi_quotation_lines": quotation_array})
        return res

    def check_order_line(self, obj):
        filtered_lines = self.quotation_line_ids.filtered(lambda line: line.sale_order_id_int == obj.id)
        if filtered_lines.add_to_line:
            return True

    @api.multi
    def action_copy(self):
        # print('>>>>>>>>>>>>>>>>action_copy 1 >>>>>>>>>>>len=', len(self.multi_quotation_lines))
        booking_id = self.env.context.get("booking_id")
        cost_profit_array = []
        sq_reference_array = []
        booking = self.env["freight.booking"].search([("id", "=", booking_id), ])
        # print('>>>>>>>>>>>>>>>>action_copy 2 booking >>>>>>>>>>>', str(booking))
        for quotation_line in self.multi_quotation_lines:
            if quotation_line.add_to_line:
                if not booking.sales_person and quotation_line.quotation.user_id:
                    booking.sales_person = quotation_line.quotation.user_id.id
                if not booking.incoterm and quotation_line.quotation.incoterm:
                    booking.incoterm = quotation_line.quotation.incoterm.id
                if not booking.port_of_loading and quotation_line.quotation.POL:
                    booking.port_of_loading = quotation_line.quotation.POL.id or False
                if not booking.port_of_discharge and quotation_line.quotation.POD:
                    booking.port_of_discharge = quotation_line.quotation.POD.id or False
                if not booking.commodity and quotation_line.quotation.commodity:
                    booking.commodity = quotation_line.quotation.commodity.id or False
                if not booking.payment_term and quotation_line.quotation.payment_term_id:
                    booking.payment_term = quotation_line.quotation.payment_term_id.id or False
                if not booking.place_of_delivery and quotation_line.quotation.place_of_delivery:
                    booking.place_of_delivery = quotation_line.quotation.place_of_delivery or False
                if not booking.type_of_movement and quotation_line.quotation.type_of_movement:
                    booking.type_of_movement = quotation_line.quotation.type_of_movement or False
                # print('>>>>>>>>>>>>>>>>action_copy 3 quotation >>>>>>>>>>> ', quotation_line.quotation.name)
                for obj in quotation_line.quotation.order_line:
                    # TS 29/12/2022 -  total sales not updated
                    # TS 17/01/2023 -  shld copy from freight foreign price
                    sale_total = 0.00
                    amount = 0.00
                    price_unit = 0.00
                    exc_rate = 1.000000
                    if obj.freight_foreign_price > 1.0:
                        price_unit = obj.freight_foreign_price
                        amount = price_unit * obj.product_uom_qty * obj.freight_currency_rate
                        sale_total = (float_round(amount, 2, rounding_method="HALF-UP") or 0.0)
                        exc_rate = obj.freight_foreign_price
                    else:
                        price_unit = obj.price_unit
                        amount = price_unit * obj.product_uom_qty
                        sale_total = (float_round(amount, 2, rounding_method="HALF-UP") or 0.0)
                    uom_id = False
                    if obj.product_uom:
                        uom_id = obj.product_uom.id
                    else:
                        uom_id = obj.product_id.uom_id.id

                    # Ahmad Zaman - 21/8/24 - Added Fiscal Position (B2B Exemption) Support
                    fiscal_position = obj.order_id.partner_id.property_account_position_id
                    fp_tax = False
                    if fiscal_position and (obj.tax_id or obj.product_id.taxes_id):
                        if obj.tax_id:
                            tax_mapping = fiscal_position.tax_ids.filtered(lambda x: x.tax_src_id.id == obj.tax_id.id)
                        else:
                            tax_mapping = fiscal_position.tax_ids.filtered(
                                lambda x: x.tax_src_id.id == obj.product_id.taxes_id.id)
                        if tax_mapping:
                            fp_tax = tax_mapping[0].tax_dest_id

                    # TS 28/03/2023 -  different way to insert the records to cost&profit
                    if obj.product_id:
                        check_item_order_line = self.check_order_line(obj, )
                        if check_item_order_line:
                            booking.cost_profit_ids = [(0, 0, {
                                "product_id": obj.product_id.id or False,
                                "product_name": obj.name or "",
                                "profit_qty": obj.product_uom_qty or 0.0,
                                "list_price": price_unit or 0.0,
                                "profit_currency":obj.freight_currency.id or obj.currency_id.id,
                                "profit_currency_rate": obj.freight_currency_rate or 1.0,
                                'sale_total': sale_total,
                                "cost_qty": obj.product_uom_qty or 0.0,
                                "cost_price": obj.cost_price or 0.0,
                                "cost_currency": obj.cost_currency.id or False,
                                "vendor_id": obj.vendor.id or False,
                                'booking_id': booking.id,
                                'uom_id': uom_id or False,
                                'tax_id': fp_tax or obj.tax_id or obj.product_id.taxes_id or False,
                            })]

                    sq_reference_array.append(quotation_line.quotation.id)
        # 28/3/2023 TS - reinsert all the sq that have been copied from
        if sq_reference_array and len(sq_reference_array) > 0:
            for sq in booking.sq_reference:
                sq_reference_array.append(sq.id)
            booking.sq_reference = [(6, 0, sq_reference_array)]
        # TS 1/3/2023 - Do Not Merge the Cost & Profit line and allow multiple select
        # if len(cost_profit_array) > 0:
        #     for cost_profit_line in booking.cost_profit_ids:
        #         cost_profit_line.sudo().unlink()
        #     booking.cost_profit_ids = cost_profit_array
        #     booking.sq_reference = [(6, 0, sq_reference_array)]
        # Merge - Canon
        # record_set = booking.cost_profit_ids.sorted(key=lambda r: r.product_id.id)
        # cur_product_id = False
        # cur_product_name = False
        # previous_line = False
        # to_be_remove_cost_profit = []
        # for line in record_set:
        #     latest_profit_qty = 0
        #     latest_list_price = 0
        #     latest_cost_qty = 0
        #     latest_cost_price = 0
        #     if cur_product_id:
        #         if line.product_id.id == cur_product_id:
        #             if line.product_name == cur_product_name:
        #                 detail = {
        #                     'operation_id': previous_line.id,
        #                     'partner_id': line.vendor_id.id,
        #                     'product_id': line.product_id.id,
        #                     'qty': line.cost_qty,
        #                     'price_unit': line.cost_price,
        #                 }
        #                 vendor_detail = self.env['freight.cost.profit.vendor.detail'].create(detail)
        #                 latest_profit_qty = previous_line.profit_qty + line.profit_qty
        #                 latest_list_price = previous_line.list_price + line.list_price
        #                 previous_line.profit_qty = latest_profit_qty
        #                 previous_line.list_price = latest_list_price / 2
        #
        #                 latest_cost_qty = previous_line.cost_qty + line.cost_qty
        #                 latest_cost_price = previous_line.cost_price + line.cost_price
        #                 previous_line.cost_qty = latest_cost_qty
        #                 previous_line.cost_price = latest_cost_price / 2
        #                 previous_line.vendor_id = False
        #                 to_be_remove_cost_profit.append(line)
        #
        #             else:
        #                 detail = {
        #                     'operation_id': line.id,
        #                     'partner_id': line.vendor_id.id,
        #                     'product_id': line.product_id.id,
        #                     'qty': line.cost_qty,
        #                     'price_unit': line.cost_price,
        #                 }
        #                 vendor_detail = self.env['freight.cost.profit.vendor.detail'].create(detail)
        #                 previous_line = line
        #         else:
        #             detail = {
        #                 'operation_id': line.id,
        #                 'partner_id': line.vendor_id.id,
        #                 'product_id': line.product_id.id,
        #                 'qty': line.cost_qty,
        #                 'price_unit': line.cost_price,
        #             }
        #             vendor_detail = self.env['freight.cost.profit.vendor.detail'].create(detail)
        #             previous_line = line
        #
        #         cur_product_id = line.product_id.id
        #         cur_product_name = line.product_name
        #
        #     else:
        #         detail = {
        #             'operation_id': line.id,
        #             'partner_id': line.vendor_id.id,
        #             'product_id': line.product_id.id,
        #             'qty': line.cost_qty,
        #             'price_unit': line.cost_price,
        #         }
        #         vendor_detail = self.env['freight.cost.profit.vendor.detail'].create(detail)
        #         cur_product_id = line.product_id.id
        #         cur_product_name = line.product_name
        #         previous_line = line

        # for i in to_be_remove_cost_profit:
        #     i.unlink()

    #

    @api.onchange('multi_quotation_lines')
    def _onchange_multi_quotation_lines(self):
        # Create a dictionary to store the current state of add_to_line for each sale_order_line_id
        existing_selections = {}
        for line in self.quotation_line_ids:
            if line.sale_order_line_id:
                existing_selections[line.sale_order_line_id.id] = line.add_to_line

        # Clear the existing lines
        self.quotation_line_ids = [(5, 0, 0)]

        # Build the new list of quotation lines
        quotation_lines = []
        for line in self.multi_quotation_lines:
            if line.add_to_line:
                for detail_line in line.quotation.order_line:
                    if detail_line.product_id:
                        add_to_line = existing_selections.get(detail_line.id, True)

                        quotation_lines.append((0, 0, {
                            'product_id': detail_line.product_id.id,
                            'name': detail_line.name,
                            'product_uom_qty': detail_line.product_uom_qty,
                            'price_subtotal': detail_line.price_subtotal,
                            'add_to_line': add_to_line,  # Use preserved value
                            'sale_order_line_id': detail_line.id,
                            'sale_order_id_int': detail_line.id,
                            'profit_currency': detail_line.freight_currency.id,
                            'freight_foreign_price': detail_line.freight_foreign_price,
                            'freight_currency': detail_line.freight_currency.id,
                            'freight_currency_rate': detail_line.freight_currency_rate,
                            'cost_price': detail_line.cost_price,
                            'vendor': detail_line.vendor.id
                        }))

        self.quotation_line_ids = quotation_lines


class MultiQuotationWizardLine(models.TransientModel):
    _name = "multi.quotation.wizard.line"

    multi_quotation_id = fields.Many2one(
        "multi.quotation.wizard", string="Multi Quotation ID"
    )

    quotation = fields.Many2one("sale.order", string="Quotation")
    total_amount = fields.Float(string="Total Amount")
    date_order = fields.Date(string="Order Date")
    validity_date = fields.Date(string="Validity Date")
    add_to_line = fields.Boolean(string="Add to Line")
    sq_description = fields.Char("SQ Description")
    customer = fields.Many2one("res.partner", string="Customer")

    @api.onchange("quotation")
    def _onchange_quotation(self):
        booking_id = self.env.context

        if self.quotation:
            if self.quotation.date_order:
                self.date_order = self.quotation.date_order.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if self.quotation.validity_date:
                self.validity_date = self.quotation.validity_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            self.sq_description = self.sq_description or False


class WizardQuotationLine(models.TransientModel):
    _name = 'wizard.quotation.line'

    wizard_quotation_id = fields.Many2one('multi.quotation.wizard', string='Wizard')
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale order Line Id")
    sale_order_id_int = fields.Integer()
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description')
    product_uom_qty = fields.Float(string='Ordered Qty')
    price_subtotal = fields.Float(string='Subtotal')
    add_to_line = fields.Boolean(string="Add to Line")
    profit_currency = fields.Many2one('res.currency', 'Currency',
                                      default=lambda self: self.env.user.company_id.currency_id.id,
                                      )
    profit_currency_rate = fields.Float(string='Rate', default="1.000000", digits=(12, 6), track_visibility='onchange')

#     Yulia 03032025 add new fields
    freight_foreign_price = fields.Float(string='Unit Price(FC)', track_visibility='onchange')
    freight_currency = fields.Many2one("res.currency",string="Currency",track_visibility="onchange")
    freight_currency_rate = fields.Float(string='Exc. Rate', track_visibility='onchange',
                                         digits=(12, 6))
    cost_price = fields.Float(string="Cost Price", track_visibility="onchange")
    vendor = fields.Many2one(
        "res.partner", string="Vendor", domain=[("supplier", "=", True)]
    )
