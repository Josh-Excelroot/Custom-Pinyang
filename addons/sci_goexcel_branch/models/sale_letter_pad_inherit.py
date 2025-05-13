# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging


class AccountLetterTemplateInherit(models.Model):
    _inherit = 'sale.letter.template'

    branch = fields.Many2one("account.analytic.tag", string="Branch", copy='False')
    doc_type = fields.Selection([('sq', 'Sale Quotation'), ('invoice', 'Invoice'), ('do', 'Delivery Order'),
                                 ('po', 'Purchase Order'), ('bc', 'Booking Confirmation')], string="Document Type", track_visibility='onchange')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            if rec.company_id.currency_id != rec.currency_id:
                template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'),
                                                                    ('currency_id', '!=', rec.currency_id.id),
                                                                    ('company_id', '=', rec.company_id.id),
                                                                    ('branch', '=', rec.branch.id)], limit=1)
            else:
                template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                                    ('company_id', '=', rec.company_id.id),
                                                                    ('branch', '=', rec.branch.id)], limit=1)

            if template:
                return template.template

    @api.model
    def create(self, vals):
        company = vals.get('company_id')
        branch = vals.get('branch')
        if not vals.get('template_id') and company and branch:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                                ('company_id', '=', company),
                                                                ('branch', '=', branch),], limit=1)
            if template:
                vals['sale_term'] = template.template
        res = super(AccountInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        #print('>>>>>>>>>>>sale_term write')
        #res = super(AccountInvoice, self).write(vals)
        for inv in self:
            currency_id = False
            if vals.get("currency_id") or inv.currency_id:
                if vals.get("currency_id"):
                    currency_id = vals.get("currency_id")
                    #print('>>>>>>>>>>>currency_id=', currency_id)
                elif inv.currency_id:
                    currency_id = inv.currency_id.id

                if vals.get('template_id') or inv.template_id:
                    template = (vals.get('template_id') and self.env['sale.letter.template'].browse(vals.get('template_id'))) or inv.template_id

                elif inv.company_id.currency_id.id != currency_id:
                    template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'),
                                                                        ('currency_id', '=', currency_id),
                                                                        ('company_id', '=', inv.company_id.id),
                                                                        ('branch', '=', inv.branch.id),], limit=1)
                    vals['template_id'] = template.id
                else:
                    template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True),
                                                                        ('company_id', '=', inv.company_id.id),
                                                                        ], limit=1)
                    vals['template_id'] = template.id
                if template:
                    vals['sale_term'] = template.template

        res = super(AccountInvoice, self).write(vals)
        return res
