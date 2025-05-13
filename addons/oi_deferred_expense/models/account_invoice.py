# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    asset_ids = fields.One2many('account.asset.asset', 'invoice_id')
    asset_count = fields.Integer('Asset Count', compute="get_asset_ids")
    is_asset_category = fields.Boolean(string='Is there Asset Category', compute="get_asset_category")

    @api.depends('invoice_line_ids')
    def get_asset_category(self):
        for rec in self:
            rec.is_asset_category = True if rec.invoice_line_ids.filtered(lambda x: x.asset_category_id) else False

    @api.multi
    @api.depends('asset_ids')
    def get_asset_ids(self):
        for rec in self:
            rec.asset_count = len(rec.asset_ids)

    def action_view_assets(self):
        asset_ids = self.mapped('asset_ids')
        action = self.env.ref(
            'oi_deferred_expense.action_account_asset_asset_deferred_expense').read()[0]
        if len(asset_ids) > 1:
            action['domain'] = [('id', 'in', asset_ids.ids)]
        elif len(asset_ids) == 1:
            form_view = [
                (self.env.ref('oi_deferred_expense.view_deferred_expense_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + \
                    [(state, view)
                     for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = asset_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_date = fields.Date('Asset Date')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        vals = super(AccountInvoiceLine, self)._onchange_product_id()
        if self.product_id and self.invoice_id.type == 'in_invoice':
            self.asset_category_id = self.product_id.product_tmpl_id.deferred_expense_category_id
        return vals

    def _set_additional_fields(self, invoice):
        if not self.asset_category_id:
            if invoice.type == 'out_invoice' and invoice.type == 'in_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.deferred_expense_category_id.id
            self.onchange_asset_category_id()
        super(AccountInvoiceLine, self)._set_additional_fields(invoice)

    @api.one
    def asset_create(self):
        if self.asset_category_id and not self.asset_date:
            raise UserError(_("Please Add Asset Date"))
        if self.asset_category_id:
            for qty in range(0, int(self.quantity)):
                vals = {
                    'name': self.name,
                    'code': self.invoice_id.number or False,
                    'category_id': self.asset_category_id.id,
                    'value': self.price_subtotal_signed,
                    'partner_id': self.invoice_id.partner_id.id,
                    'company_id': self.invoice_id.company_id.id,
                    'currency_id': self.invoice_id.company_currency_id.id,
                    'date': self.asset_date if self.asset_date else self.invoice_id.date_invoice,
                    'invoice_id': self.invoice_id.id,
                }
                changed_vals = self.env['account.asset.asset'].onchange_category_id_values(
                    vals['category_id'])
                vals.update(changed_vals['value'])
                asset = self.env['account.asset.asset'].create(vals)
                # auto confirm(Kinjal)
                # if self.asset_category_id.open_asset:
                asset.validate()
                asset.compute_generated_entries(datetime.today())
        return True
