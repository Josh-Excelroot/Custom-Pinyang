from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class InvoiceWizard(models.TransientModel):
    _name = 'rft.invoice.wizard'

    customer_name = fields.Many2one('res.partner', string='Customer Name')
    rft_no = fields.Char(string='RFT No', index=True)
    cost_profit_ids = fields.One2many('rft.invoice.wizard.line', 'rft_id', string="Cost & Profit")

    select_add = fields.Selection([('all', 'Select All'), ('deselect', 'DeSelect All')],
                                  string='Select/DeSelect All to Add to Invoice'
                                  , default='all')
    container_product_name = fields.Text(string='Description of Goods')

    @api.onchange('select_add')
    def onchange_select_add(self):
        if self.select_add == 'all':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = True

        elif self.select_add == 'deselect':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = False


    def _saleorder_create_analytic_account_prepare_values(self):
        """
         Prepare values to create analytic account
        :return: list of values
        """
        return {
            'name': '%s' % self.rft_no,
            'partner_id': self.customer_name.id,
            'company_id': self.company_id.id,
        }

    @api.model
    def default_get(self, fields):
        result = super(InvoiceWizard, self).default_get(fields)
        rft_id = self.env.context.get('rft_id')
        if rft_id:
            rft = self.env['transport.rft'].browse(rft_id)
            if not rft.analytic_account_id:
                values = {
                    'partner_id': rft.billing_address.id,
                    'name': '%s' % rft.rft_no,
                    'code': rft.rft_no,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                rft.write({'analytic_account_id': analytic_account.id,
                               })
            # for rec in self:
            result.update({'customer_name': rft.billing_address.id,
                           'rft_no': rft.rft_no,
                           })
            rft_list = []
            for rft_line in rft.cost_profit_ids_rft:
                if not rft_line.added_to_invoice:
                    rft_list.append({
                        'rft_line_id': rft_line.id,
                        'product_id': rft_line.product_id,
                        #'product_id': rft_line.product_name,
                        'list_price': rft_line.unit_price,
                        'profit_qty': rft_line.sales_qty,
                        'sale_total': rft_line.sales_amount,
                        'cost_profit_line' : rft_line,
                        'analytic_account_id': rft.analytic_account_id,
                    })

            # if rft.cargo_type == 'fcl':
            #     if rft.operation_line_ids:
            #         result.update({'container_product_name': rft.operation_line_ids[0].container_product_name})

            # if rft.cargo_type == 'lcl':
            #     if rft.operation_line_ids2:
            #         result.update({'container_product_name': rft.operation_line_ids2[0].container_product_name})

            result['cost_profit_ids'] = rft_list
            result = self._convert_to_write(result)


        #print(result)
        return result


    @api.multi
    def action_create_invoice(self):
        if self.rft_no:
            rft = self.env['transport.rft'].search([('rft_no', '=', self.rft_no)])
            create_invoice = False
            for rft_line in self.cost_profit_ids:
                if rft_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the transport."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                # if rft.service_type == "land":
                #     invoice_type = "lorry"
                # else:
                #     invoice_type = "without_lorry"
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': rft.billing_address.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': rft.rft_no,
                    'rft_id': rft.id,
                    'account_id': rft.billing_address.property_account_receivable_id.id or False,
                    'company_id': rft.company_id.id,
                    'user_id': rft.sales_person.id,
                    #'invoice_type': invoice_type,
                    #'invoice_description': self.container_product_name,
                }
                invoice = inv_obj.create(inv_val)
                for rft_line in self.cost_profit_ids:
                    if rft_line.add_to_invoice:
                        line_item = rft_line.cost_profit_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.unit_price * line_item.sale_currency_rate
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        #print(rft.rft_no)
                        if account_id:
                            if sale_unit_price_converted > 0:
                                inv_line = inv_line_obj.create({
                                    'rft_line_id': line_item.id or False,
                                    'invoice_id': invoice.id or False,
                                    'account_id': account_id.id or False,
                                    'name': line_item.product_name or '',
                                    'product_id': line_item.product_id.id or False,
                                    'quantity': line_item.sales_qty or 0.0,
                                    'uom_id': line_item.product_id.uom_id.id or False,
                                    'price_unit': sale_unit_price_converted or 0.0,
                                    'account_analytic_id': rft.analytic_account_id.id or False,
                                    'invoice_line_tax_ids': [(6, 0, line_item.tax_id.ids)],
                                    'origin': rft.rft_no,
                                })
                                line_item.write({'invoice_id': invoice.id or False,
                                            'inv_line_id': inv_line.id or False})
                        else:
                            raise ValidationError(_('Please Check Your Product Income/Expense Account!'))
                invoice.compute_taxes()
            for check_line in rft.cost_profit_ids_rft:
                if check_line.added_to_invoice:
                    rft.invoice_status = '03'
                else:
                    rft.invoice_status = '02'



    @api.multi
    def action_select_all(self):
        for rft_line in self.cost_profit_ids:
            rft_line.write({'add_to_invoice': True})


    @api.multi
    def action_deselect_all(self):
        for rft_line in self.cost_profit_ids:
            rft_line.add_to_invoice = False


class InvoiceWizardLine(models.TransientModel):
    _name = "rft.invoice.wizard.line"

    rft_id = fields.Many2one('rft.invoice.wizard', string='rft Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    cost_profit_line = fields.Many2one('rft.cost.profit', string='rft Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    product_id = fields.Many2one('product.product', string="Product")
    add_to_invoice = fields.Boolean(string='Add to Invoice')
    list_price = fields.Float(string="Unit Price")
    #profit_qty = fields.Integer(string='Qty')
    profit_qty = fields.Float(string='Qty', digits=(12, 2))
    sale_total = fields.Float(string="Total Sales")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always')
    rft_line_id = fields.Many2one('rft.cost.profit')

