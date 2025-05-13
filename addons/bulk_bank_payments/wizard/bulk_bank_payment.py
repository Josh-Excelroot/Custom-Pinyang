import io
from io import BytesIO
import xlsxwriter
import base64
import os
from datetime import date
from datetime import datetime, timedelta
from odoo import api, fields, models, _
import csv
from io import StringIO
from odoo import http


class BulkBankPayments(models.TransientModel):
    _name = 'bulk.bank.payments'

    bank_id = fields.Many2one('res.bank', string='Bank')
    date_from = fields.Date(string='Date From', default=str(datetime.now() - timedelta(days=365)))
    date_to = fields.Date(string='Date To', default=fields.Date.today())
    state = fields.Selection([('all', 'All'), ('posted', 'Posted Only'),('paid','Paid'),('reconciled','Reconciled')], string='Payment Status', default='posted')
    vendor_payment_ids = fields.Many2many('account.payment', string='Vendor Payments')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)

    @api.onchange('bank_id','date_from','date_from','currency_id','state')
    def filter_vendor_payments(self):
        # filters based on payment journal
        if self.state == 'all':
            domain = [('journal_id.bank_id', '=', self.bank_id.id), ('payment_date', '>=', self.date_from),
                      ('payment_date', '<=', self.date_to), ('currency_id', '=', self.currency_id.id),
                      ('company_id', '=', self.env.user.company_id.id), ('payment_type', '=', 'outbound'),
                      ('partner_type', '=', 'supplier')]
        else:
            domain = [('journal_id.bank_id', '=', self.bank_id.id), ('state', '=', 'posted'),
                      ('payment_date', '>=', self.date_from), ('payment_date', '<=', self.date_to),
                      ('company_id', '=', self.env.user.company_id.id), ('payment_type', '=', 'outbound'),
                      ('partner_type', '=', 'supplier'), ('currency_id', '=', self.currency_id.id)]

        # filter based on partner bank
        # if self.state == 'all':
        #     domain = [('partner_id.bank_ids.bank_id', '=', self.bank_id.id), ('payment_date', '>=', self.date_from),
        #               ('payment_date', '<=', self.date_to), ('currency_id', '=', self.currency_id.id),
        #               ('company_id', '=', self.env.user.company_id.id), ('payment_type', '=', 'outbound'),
        #               ('partner_type', '=', 'supplier')]
        # else:
        #     domain = [('partner_id.bank_ids.bank_id', '=', self.bank_id.id), ('state', '=', 'posted'),
        #               ('payment_date', '>=', self.date_from), ('payment_date', '<=', self.date_to),
        #               ('company_id', '=', self.env.user.company_id.id), ('payment_type', '=', 'outbound'),
        #               ('partner_type', '=', 'supplier'), ('currency_id', '=', self.currency_id.id)]

        payments = self.env['account.payment'].sudo().search(domain)
        self.vendor_payment_ids = [[6, 0, payments.ids]]
        return {
            "type": "ir.actions.do_nothing"
        }

    def print_xlsx_report(self):
        action = self.env.ref('bulk_bank_payments.action_bulk_payment_report_xlsx').read()[0]
        return action

    def refresh_filters(self):
        # for vp in self.vendor_payment_ids:
        self.vendor_payment_ids = False
        return {
            "type": "ir.actions.do_nothing"
        }

    def print_csv_report(self):
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        headers_1 = [
            'Employer Info', self.env.user.company_id.name
        ]
        writer.writerow(headers_1)
        headers_2 = [
            'Crediting Date', str(self.date_to)
        ]
        writer.writerow(headers_2)
        headers_3 = [
            'Payment Reference', 'Bulk Payment'
        ]
        writer.writerow(headers_3)
        headers_4 = [
            'Payment Description', ''
        ]
        writer.writerow(headers_4)
        headers_5 = [
            'Bulk Payment Type', ''
        ]
        writer.writerow(headers_5)
        additional_headers = [
            'Beneficiary Name', 'Beneficiary Bank', 'Beneficiary Account Number', 'ID Type', 'ID Number',
            'Payment Type', 'Payment Amount','Payment Reference', 'Payment Description'
        ]
        writer.writerow(additional_headers)

        payments = self.env['account.payment'].browse(self.vendor_payment_ids.ids)
        for payment in payments:
            column_data = [payment.partner_id.name or '',
                           (', '.join([bank.bank_id.name for bank in payment.partner_id.bank_ids])) or '',
                           (', '.join([str(bank.acc_number) for bank in payment.partner_id.bank_ids])) or '',
                           '',
                           '',
                           dict(payment._fields['payment_type'].selection).get(payment.payment_type) or '',
                           "{:,.2f}".format(payment.amount) if payment.amount else '',
                           payment.reference or '',
                           '']
            writer.writerow(column_data)

        csv_data = output.getvalue()
        output.close()
        csv_data_base64 = base64.encodebytes(csv_data.encode())
        attachment = self.env['ir.attachment'].create({
            'name': 'Bulk Bank Payments.csv',
            'type': 'binary',
            'datas': csv_data_base64,
            'datas_fname': 'Bulk Bank Payments.csv'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self'
        }
