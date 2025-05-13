def import_invoice1(self):
    account_invoice_obj = self.env['account.invoice']
    invoice_line_obj = self.env['account.invoice.line']

    form_view_ref = False
    ctx = dict(self._context)
    form_view_ref = self.env.ref('account.invoice_supplier_form', False).id

    if self.new_partner:
        partner_rec = self.with_context(ctx).create_partner()
        account_id_header = False
    else:
        partner_rec = self.partner_id
        if self.partner_id.property_account_payable_id:
            account_id_header = self.partner_id.property_account_payable_id[0].id
        else:
            account_id_header = False

    # TS - add the freight booking reference from the BL no by search carrier booking no
    freight_booking = self.env['freight.booking'].search([('carrier_booking_no', 'like', self.bl_no)], limit=1)
    value = []

    for invoice_line in self.invoice_line_ids:
        account_id = False
        if invoice_line.product_id:
            if invoice_line.product_id.property_account_expense_id:
                account_id = invoice_line.product_id.property_account_expense_id
            elif invoice_line.product_id.categ_id.property_account_expense_categ_id:
                account_id = invoice_line.product_id.categ_id.property_account_expense_categ_id
            if account_id:
                group_product_desc_invoice = self.env['ir.config_parameter'].sudo().get_param(
                    'product_description.group_product_desc_invoice')
                if group_product_desc_invoice:
                    name1 = " "
                    product_desc = invoice_line.product_id.name
                else:
                    name1 = invoice_line.product_id.name
                    product_desc = ""
                found_line_product = False
                if self.merge_line_item:
                    for i in value:
                        freight_foreign_price = i[2].get('freight_foreign_price')
                        price_unit = i[2].get('price_unit')
                        if invoice_line.product_id.id == i[2].get('product_id'):
                            found_line_product = True
                            freight_foreign_price = freight_foreign_price + invoice_line.foreign_price
                            price_unit = price_unit + invoice_line.price_unit
                            curr_account_id = i[2].get('account_id')
                            curr_product_id = i[2].get('product_id')
                            curr_name = i[2].get('name')
                            curr_product_desc = i[2].get('product_desc')
                            curr_freight_currency = i[2].get('freight_currency')
                            curr_freight_currency_rate = i[2].get('freight_currency_rate')
                            curr_quantity = i[2].get('quantity')
                            curr_uom_id = i[2].get('uom_id')

                            i[2] = {
                                'account_id': curr_account_id,
                                'product_id': curr_product_id,
                                'name': curr_name,
                                'product_desc': curr_product_desc,
                                'freight_currency': curr_freight_currency,
                                'freight_foreign_price': freight_foreign_price,
                                'freight_currency_rate': curr_freight_currency_rate,
                                'quantity': curr_quantity,
                                'price_unit': price_unit,
                                'uom_id': curr_uom_id,
                            }

                if not found_line_product:
                    value.append([0, 0, {
                        'account_id': account_id.id or False,
                        'product_id': invoice_line.product_id.id or False,
                        'name': name1 or '',
                        'product_desc': product_desc or '',
                        'freight_currency': invoice_line.currency.id,
                        'freight_foreign_price': invoice_line.foreign_price,
                        'freight_currency_rate': invoice_line.currency_rate,
                        'quantity': invoice_line.quantity,
                        'price_unit': invoice_line.price_unit,
                        'uom_id': invoice_line.product_id.uom_id and invoice_line.product_id.uom_id.id or False,
                    }])
            else:
                raise Warning(_("No Account Id in Item."))
    vendor_bill = self.env['account.invoice'].browse(1)

    if freight_booking:

        for invoice_line in vendor_bill.invoice_line_ids:
            cost_price = 0
            if invoice_line.freight_foreign_price > 0:
                cost_price = invoice_line.freight_foreign_price
            else:
                cost_price = invoice_line.price_unit
            check_booking = False
            for cost_profit_line in freight_booking.cost_profit_ids:
                if cost_profit_line.product_id == invoice_line.product_id:
                    booking_line_id = cost_profit_line
                    check_booking = True
                    if invoice_line.price_unit and (
                            invoice_line.price_unit > 0 or invoice_line.price_unit < 0):

                        # Vendor Bill
                        if cost_profit_line.vendor_bill_ids:
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                total_qty = 0
                                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search(
                                        [('invoice_id', '=', vendor_bill_line.id)])
                                    for invoice_line_item in account_invoice_line:
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and (
                                                invoice_line_item.freight_booking.id == freight_booking.id):
                                            total_qty = total_qty + invoice_line_item.quantity
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + invoice_line.quantity
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {
                                            'cost_qty': total_qty or False,
                                            'invoiced': True,
                                            'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                            'vendor_bill_ids': [(4, vendor_bill.id)],
                                        })
                            else:
                                cost_profit_line.write({
                                    'cost_price': cost_price,
                                    'cost_qty': invoice_line.quantity,
                                    'invoiced': True,
                                    'vendor_id': vendor_bill.partner_id.id,
                                    'vendor_bill_id': vendor_bill.id,
                                    'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                    'vendor_bill_ids': [(4, vendor_bill.id)],
                                    'cost_currency': invoice_line.freight_currency.id,
                                    'cost_currency_rate': invoice_line.freight_currency_rate,
                                })

                        else:
                            cost_profit_line.write({
                                'cost_price': cost_price,
                                'cost_qty': invoice_line.quantity,
                                'invoiced': True,
                                'vendor_id': vendor_bill.partner_id.id,
                                'vendor_bill_id': vendor_bill.id,
                                'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                'vendor_bill_ids': [(4, vendor_bill.id)],
                                'cost_currency': invoice_line.freight_currency.id,
                                'cost_currency_rate': invoice_line.freight_currency_rate,
                            })
            # if check_booking:
            # If product did not exist
            if not check_booking:
                values = {
                    'booking_id': freight_booking.id,
                    # Please check
                    'booking_line_id_temp': freight_booking.id,
                    'product_id': invoice_line.product_id.id,
                    'product_name': invoice_line.product_id.name,
                    'cost_price': cost_price,
                    'cost_qty': invoice_line.quantity,
                    'invoiced': True,
                    'vendor_id': vendor_bill.partner_id.id,
                    'vendor_bill_id': vendor_bill.id,
                    'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                    'vendor_bill_ids': [(4, vendor_bill.id)],
                    'cost_currency': invoice_line.freight_currency.id,
                    'cost_currency_rate': invoice_line.freight_currency_rate,
                }
                booking_line_id = self.env['freight.cost_profit'].sudo().create(values)

            invoice_line.write({
                'account_analytic_id': account_analytic_id,
                'booking_line_id': booking_line_id.id,
                'origin': freight_booking.booking_no,
                'freight_booking': freight_booking.id,
                'carrier_booking_no': freight_booking.carrier_booking_no,
            })

    return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'account.invoice',
        'views': [(form_view_ref, 'form')],
        'view_id': form_view_ref,
        'res_id': vendor_bill.id or False,
    }