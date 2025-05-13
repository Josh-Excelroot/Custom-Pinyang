# -*- coding: utf-8 -*-
# Copyright (C) Laxicon Solution.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_approval = fields.Boolean("Enable Approval work Flow")
    restrict_for_close_period = fields.Boolean("Restrict record creation for Closed Fiscal Period or Closed Fiscal Year")
    period_type = fields.Selection([('1', '1 Month'), ('3', '3 Month'), ('6', '6 Month'), ('12', '12 Month')], string="Period Type")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    period_type = fields.Selection(related="company_id.period_type", string="Period Type", readonly=False)

    enable_approval = fields.Boolean(string="Enable Approval work Flow", related='company_id.enable_approval', readonly=False)
    restrict_for_close_period = fields.Boolean(
        string="Restrict record creation for Closed Fiscal Period or Closed Fiscal Year", related='company_id.restrict_for_close_period', readonly=False)

    def update_old_records(self):
        for rec in self.env['account.move'].sudo().search(['|', ('period_id', '=', False), ('fiscal_year', '=', False)] + [('company_id', '=', self.company_id.id)]):
            #print('>>>>>>>>>>>>update_old_records  record name=', rec.name, ' , date=', rec.date)
            if rec.date:
                period = self.env['account.period.part'].sudo().search([('date_from', '<=', rec.date), ('date_to', '>=', rec.date), ('company_id', '=', rec.company_id.id)], limit=1)
                #print('>>>>>>>>>>>>update_old_records period=', period, ' , date=', rec.date)
                if period:
                    rec.period_id = period.id

        for rec in self.env['account.invoice'].sudo().search(['|', ('period_id', '=', False), ('fiscal_year', '=', False)] + [('company_id', '=', self.company_id.id)]):
            if rec.date:
                period = self.env['account.period.part'].sudo().search([('date_from', '<=', rec.date_invoice), ('date_to', '>=', rec.date_invoice), ('company_id', '=', rec.company_id.id)], limit=1)
                if period:
                    rec.period_id = period.id
