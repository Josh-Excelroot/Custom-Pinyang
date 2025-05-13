# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_followup_report_id = fields.Many2one(related="company_id.payment_followup_report_id", string="Payment Folloup Report", domain="[('model', '=', 'account.invoice')]", readonly=False)
    go_live_date = fields.Date(related="company_id.go_live_date", readonly=False, string="Go Live Date")
    # statement_duration = fields.Selection(related="company_id.statement_duration", readonly=False, string="Statement Duration")
    invoice_include_type = fields.Selection(related="company_id.invoice_include_type", string="Include Invoice?", readonly=False)


class ResCompany(models.Model):
    _inherit = "res.company"

    payment_followup_report_id = fields.Many2one('ir.actions.report', string="Payment Followup Report", domain="[('model', '=', 'account.invoice')]", readonly=False)
    go_live_date = fields.Date(string="Go Live Date")
    # statement_duration = fields.Selection([('3', '3 Months'), ('6', '6 Months'), ('9', '9 Months'), ('1', '1 Year')], string="Statement Duration")
    invoice_include_type = fields.Selection([('open', 'Open'), ('overdue', 'Overdue')], string="Include Invoice?")
