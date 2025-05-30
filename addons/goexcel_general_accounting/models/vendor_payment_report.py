# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models

class VendorPaymentReport(models.Model):
    _name = "vendor.payment.report"
    _auto = False
    _description = "Vendor Payment Report"
    _order = 'payment_date desc, name asc'

    id = fields.Integer(string="ID", readonly=True)
    name = fields.Char(string="Name", readonly=True)
    payment_date = fields.Date(string='Payment Date', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    account_payment_id = fields.Many2one('account.payment', string="Vendor Payment", readonly=True)
    account_voucher_id = fields.Many2one('account.voucher', string="Sale Receipt", readonly=True)
    journal_id = fields.Many2one('account.journal', string="Payment Journal", readonly=True)
    reference = fields.Char(string="Payment Ref", readonly=True)
    payment_amount = fields.Monetary(string="SubTotal Price", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency ID", readonly=True)
    #cheque_no = fields.Char(string="Cheque No", readonly=True)
    #move_reconciled = fields.Boolean(string="Fully Matched", readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('open', 'Open'), ('sent', 'Sent'),
                              ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled'), ('cancel', 'Cancelled')],
                             string="Status", readonly=True)
    #user_id = fields.Many2one('res.users', string="SalesPerson", readonly=True)
    #company_id = fields.Many2one("res.company", "Company")
    company_id = fields.Many2one('res.company', 'Company', readonly=True)



    #TS -if the field is not exist in another table, use NULL as XXXXX
    #    make sure company_id must be there, if not stored, set the Store=True
    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, 'vendor_payment_report')
        self.env.cr.execute("""CREATE OR REPLACE VIEW vendor_payment_report AS (
            SELECT
                id,
                name,
                payment_date,
                partner_id,
                id as account_payment_id,
                NULL as account_voucher_id,
                journal_id,
                reference,
                amount as payment_amount,
                currency_id,
                company_id,
                state
            FROM account_payment
            WHERE
                payment_type='outbound'
            UNION
            SELECT
                id,
                number as name,
                date as payment_date,
                partner_id,
                NULL as account_payment_id,
                id as account_voucher_id,
                journal_id,
                name as reference,
                amount as payment_amount,
                currency_id,
                company_id,
                state
            FROM account_voucher
                WHERE
                voucher_type='purchase' )""")



