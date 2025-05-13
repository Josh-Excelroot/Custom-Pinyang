from odoo import api, fields, models, exceptions,_
import logging
from datetime import date
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class FreightInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_description = fields.Char(string='Invoice Description', track_visibility='onchange')
    x_product_category = fields.Many2one('product.category', string='Freight Booking', track_visibility='onchange')

    invoice_note = fields.Text(string='Invoice Additional Note', track_visibility='onchange',
                               compute="_get_use_invoice_note")
    document_attachments_ids = fields.One2many('document.attachments', 'invoice_id', string="Documents")
    folder_id = fields.Char()
    invoice_type = fields.Selection([('lorry', 'Truck'), ('without_lorry', 'Non-Truck')], default='without_lorry',
                                    string='Invoice Type')
    attn = fields.Many2one('res.partner', string='Attn', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('type') == 'in_refund' or vals.get('type') == 'out_refund' or vals.get('type') == 'in_invoice' or \
                (vals.get('type') == 'out_invoice' and vals.get('customer_debit_note')):
            if self.freight_booking:
                vals.update({'freight_booking': self.freight_booking.id})
        if self.company_id.currency_id != self.currency_id:
            vals.update({'comment': self.env.user.company_id.invoice_note_foreign_currency})
        else:
            vals.update({'comment': self.env.user.company_id.invoice_note})
        res = super(FreightInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        currency = self.env['res.currency'].browse(vals.get('currency_id'))
        # TS
        if currency:
            for record in self:
                if record.company_id.currency_id != currency:
                    vals.update({'comment': self.env.user.company_id.invoice_note_foreign_currency})
                else:
                    vals.update({'comment': self.env.user.company_id.invoice_note})
        
        res = super(FreightInvoice, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        #print("Invoice Unlink")
        for inv in self:
            for invoice_line in inv.invoice_line_ids:
                if invoice_line.booking_line_id:
                    cost_profit_line = self.env['freight.cost_profit'].search(
                        [('id', '=', invoice_line.booking_line_id.id)],
                        limit=1)
                    if inv.type == 'in_invoice':  # when delete a vendor bill item
                        # if there are multiple vendor bills assigned to the same job cost
                        if cost_profit_line.vendor_bill_ids and len(cost_profit_line.vendor_bill_ids) > 1:
                            vendor_bill_ids_list = []
                            total_qty = 0
                            for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                account_invoice_line = self.env['account.invoice.line'].search(
                                    [('invoice_id', '=', vendor_bill_id.id)])
                                for invoice_line_item in account_invoice_line:
                                    #if invoice_line_item.product_id == cost_profit_line.product_id:
                                    if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_booking.id == invoice_line.freight_booking.id):
                                        total_qty = total_qty + invoice_line_item.quantity
                                if vendor_bill_id.id != inv.id:  #TODO
                                    vendor_bill_ids_list.append(vendor_bill_id.id)
                            if total_qty > 0:
                                cost_profit_line.write(
                                    {  # assuming cost_price will always be same for all vendor bills for same item
                                        # 'cost_price': round(price_unit, 2) or 0,
                                        'cost_qty': total_qty or False,
                                        # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                        # 'cost_currency': invoice_line.freight_currency.id,
                                        'invoiced': True,
                                        # 'vendor_id': self.invoice_id.partner_id.id,
                                        'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                    })
                            # cost_profit.write({
                            #     'vendor_id_ids': [(3, self.partner_id.id)],
                            #     'vendor_bill_ids': [(3, self.id)],
                            #     'invoiced': False,
                            # })
                        else: #if only 1 vendor bill
                            cost_profit_line.write({
                                'vendor_id': False,
                                'vendor_bill_ids': [(3, self.id)],
                                'invoiced': False,
                                'cost_price': 0,
                                'cost_qty': 0,
                                'cost_currency_rate': 1.000000,
                                'cost_currency': False,
                            })
                # if self.type == 'in_refund':
                    #     cost_profit.write({
                    #         'vendor_bill_ids': [(3, self.id)],
                    #     })
                    #booking = self.env['freight.booking'].search([('id', '=', cost_profit.booking_id.id)], limit=1)
                    #booking.action_calculate_cost()
            return super(FreightInvoice, self).unlink()


    @api.onchange('date_invoice')
    def onchange_date_invoice(self):
        if not self.invoice_note:
            self.invoice_note = self.env.user.company_id.invoice_note


    @api.multi
    def _get_use_invoice_note(self):
        for record in self:
            # TS
            if record.company_id.currency_id != record.currency_id:
                record.invoice_note = self.env.user.company_id.invoice_note_foreign_currency
            else:
                record.invoice_note = self.env.user.company_id.invoice_note

    # TS - bug fix the CN/Invoice not updating the comment
    @api.onchange('currency_id')
    def onchange_currency_id(self):
        if self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.comment = self.env.user.company_id.invoice_note_foreign_currency

    #main purpose is to update the vendor_bill_ids in the cost&profit items
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        
        purchase_ids = self.invoice_line_ids.mapped('purchase_id')
        if purchase_ids:
            self.origin = ', '.join(purchase_ids.mapped('name'))
        # TS - this is important to recalculate the Tax, if there is any change to qty, price, etc
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines

    def action_assign_job_cost(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_invoice.job_cost_wizard_form')
        return {
            'name': 'Assign Job Cost',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'job.cost.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(self.env.context,
                            vendor_bill_id=self.id,
                            partner_id=self.partner_id.id,
                            ),
        }


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    # booking_job_cost = fields.Many2one('freight.cost_profit', string='Job Cost')
    freight_booking = fields.Many2one('freight.booking', string='Booking Job', copy=False)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=False)
    lorry_type = fields.Char('Lorry Type')
    lorry_no = fields.Char('Lorry No')
    location = fields.Char('Pickup From')
    dest_location = fields.Char('Deliver To')
    do_no = fields.Char('DO No')
    check_calculate_cost = fields.Boolean('Check Calculate Cost')

    booking_line_id = fields.Many2one('freight.cost_profit', copy=False)
    bl_line_id = fields.Many2one('freight.bol.cost.profit', copy=False)
    #inv_parent_id = fields.Integer(string='parent_id', copy=False, compute="_compute_inv_parent_id")

    # def _compute_inv_parent_id(self):
    #     print('_compute_inv_parent_id');
    #     for operation in self:
    #         operation.inv_parent_id = self.env.context.get('new_parent_id')

    @api.model
    def create(self, vals):
        #To fix - by default Vendor DN/Vendor CN will copy the line info from the parent
        invoice_line = super(AccountInvoiceLine, self).create(vals)
        if self._context.get('create_from_job'):
            return invoice_line

        # To fix - by default Vendor DN/Vendor CN will copy the line info from the parent
        if invoice_line.invoice_id.type in ['in_refund', 'out_refund'] \
                or (invoice_line.invoice_id.type in ['in_invoice', 'out_invoice'] and invoice_line.invoice_id.debit_invoice_id):
            invoice_line.booking_line_id = False

        # if not invoice_line.product_id:
        #    invoice_line.unlink()
        return invoice_line

    def action_assign_job_cost(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_invoice.view_job_cost_form')
        return {
            'name': 'Add Job Cost',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.booking.job.cost',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(self.env.context,
                            vendor_bill_id=self.invoice_id.id,
                            partner_id=self.partner_id.id,
                            product_id=self.product_id.id,
                            ),
            # 'res_id': self.id,
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner.'),
            }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            self_lang = self
            if part.lang:
                self_lang = self.with_context(lang=part.lang)

            product = self_lang.product_id
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            product_name = self_lang._get_invoice_line_name_from_product()
            if not self.name:
                self.name = self.product_id.name

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}

