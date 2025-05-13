# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    soa_note = fields.Text(related="company_id.soa_note", string="Additional Notes for Customer SOA", readonly=False)
    soa_type = fields.Selection(related="company_id.soa_type", readonly=False, string='SOA Type')
    soa_invoice_date_type = fields.Selection(related="company_id.soa_invoice_date_type", readonly=False, string='Invoice Date')
    show_payment_term = fields.Boolean(related="company_id.show_payment_term", readonly=False, string='Show Payment Term')
    aging_group = fields.Selection(related="company_id.aging_group", readonly=False, string='Ageing Group')
