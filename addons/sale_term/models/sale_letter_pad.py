# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

states = [('draft', 'Draft'), ('approved', 'Approved')]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.multi
    # def _get_default_term(self):
    #     for rec in self:
    #         print(' _get_default_term')
    #         template = self.env['sale.letter.template'].search([('doc_type', '=', 'sq'),('default', '=', True),
    #                                                             ('company_id', '=', self.company_id.id)], limit=1)
    #         if template:
    #             print(' _get_default_term template')
    #             return template.template

    @api.model
    def create(self, vals):
        company = vals.get('company_id')
        template = self.env['sale.letter.template'].search([('doc_type', '=', 'sq'), ('default', '=', True),
                                                            ('company_id', '=', company)], limit=1)
        vals['template_id'] = template.id
        res = super(SaleOrder, self).create(vals)
        return res

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]})
    sale_term = fields.Html(related='template_id.template', string='Template', states={'draft': [('readonly', False)]})
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    # @api.onchange('template_id')
    # def onchange_template_id(self):
    #     if self.template_id:
    #         self.sale_term = self.template_id.template


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            if rec.company_id.currency_id != rec.currency_id:
                template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'),
                                                                    ('currency_id', '!=', rec.currency_id.id),
                                                                    ('company_id', '=', rec.company_id.id)], limit=1)
            else:
                template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                                    ('company_id', '=', rec.company_id.id)], limit=1)

            if template:
                return template.template

    @api.model
    def create(self, vals):
        company = vals.get('company_id')
        template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                            ('company_id', '=', company)], limit=1)
        vals['template_id'] = template.id
        res = super(AccountInvoice, self).create(vals)
        return res


    @api.multi
    def write(self, vals):
        #print('>>>>>>>>>>>sale_term write')
        for inv in self:
            currency_id = False
            if vals.get("currency_id") or inv.currency_id:
                if vals.get("currency_id"):
                    currency_id = vals.get("currency_id")
                    #print('>>>>>>>>>>>currency_id=', currency_id)
                elif inv.currency_id:
                    currency_id = inv.currency_id.id
                if inv.company_id.currency_id.id != currency_id:
                    template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'),
                                                                        ('currency_id', '=', currency_id),
                                                                        ('company_id', '=', inv.company_id.id)], limit=1)
                else:
                    template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                                        ('company_id', '=', inv.company_id.id)], limit=1)
                if template:
                    vals['template_id'] = template.id
                    #print('template=', template.template)
        res = super(AccountInvoice, self).write(vals)
        return res


    # @api.onchange('date_invoice', 'currency_id')
    # def onchange_date_invoice(self):
    #     # if not self.comment:
    #     #     self.comment = self.env.user.company_id.invoice_note
    #     if self.company_id.currency_id != self.currency_id:
    #         template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'),
    #                                                             ('currency_id', '!=', self.currency_id.id),
    #                                                             ('company_id', '=', self.company_id.id)], limit=1)
    #     else:
    #         template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
    #                                                             ('company_id', '=', self.company_id.id)], limit=1)
    #     if template:
    #         self.sale_term = template.template



    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]},
                                  default=_get_default_term)
    sale_term = fields.Html(related='template_id.template',string='Template', states={'draft': [('readonly', False)]})
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    # @api.onchange('template_id')
    # def onchange_template_id(self):
    #     if self.template_id:
    #         self.sale_term = self.template_id.template


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'po'), ('default', '=', True),
                                                                ('company_id', '=', self.company_id.id)], limit=1)
            if template:
                return template.template

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]}, )
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]},
                            default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template


class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'do'), ('default', '=', True),
                                                                ('company_id', '=', self.company_id.id)], limit=1)
            if template:
                return template.template

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]}, )
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]},
                            default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template




class AccountLetterTemplate(models.Model):
    _name = 'sale.letter.template'
    _description = 'Terms and Condition'

    name = fields.Char('Name', required=True)
    template = fields.Html('Template')
    active = fields.Boolean('Active', default=True)
    default = fields.Boolean('Default', default=True)
    doc_type = fields.Selection([('sq', 'Sale Quotation'), ('invoice', 'Invoice'), ('do', 'Delivery Order'),
                                 ('po', 'Purchase Order')], string="Document Type", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Invoice Currency')