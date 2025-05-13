from odoo import fields, models, api
from lxml import etree

from odoo.exceptions import UserError


class CreateCompany(models.Model):
    _inherit = 'res.company'

    def create_customer_inv(self,record,customer_invoice_obj):
        data = {
            "name": customer_invoice_obj.name,
            "type": "sale",
            "company_id": record.id,
            "code": customer_invoice_obj.code,
            "sequence_number_next": customer_invoice_obj.sequence_number_next,
            "sequence_id": customer_invoice_obj.sequence_id.id,
            "refund_sequence": customer_invoice_obj.refund_sequence,
            "debitnote_sequence": customer_invoice_obj.debitnote_sequence,
            "debitnote_sequence_number_next": customer_invoice_obj.debitnote_sequence_number_next,
            "debitnote_sequence_id": customer_invoice_obj.debitnote_sequence_id.id,
            "update_posted": customer_invoice_obj.update_posted
        }
        self.env['account.journal'].sudo().create(data)

    def create_vendor(self,record,vendor_bill):
        data = {
            "name": vendor_bill.name,
            "type": vendor_bill.type,
            "company_id": record.id,
            "code": vendor_bill.code,
            "sequence_number_next": vendor_bill.sequence_number_next,
            "sequence_id": vendor_bill.sequence_id.id,
            "refund_sequence": vendor_bill.refund_sequence,
            "debitnote_sequence": vendor_bill.debitnote_sequence,
            "debitnote_sequence_number_next": vendor_bill.debitnote_sequence_number_next,
            "debitnote_sequence_id": vendor_bill.debitnote_sequence_id.id,
            "update_posted": vendor_bill.update_posted
        }
        self.env['account.journal'].sudo().create(data)

    def create_miscell(self,record,miscell):
        data = {
            "name": miscell.name,
            "type": miscell.type,
            "company_id": record.id,
            "code": miscell.code,
            "sequence_number_next": miscell.sequence_number_next,
            "sequence_id": miscell.sequence_id.id,
            "update_posted": miscell.update_posted
        }
        self.env['account.journal'].sudo().create(data)

    def create_exchnage(self,record,exchange):
        data = {
            "name": exchange.name,
            "type": exchange.type,
            "company_id": record.id,
            "code": exchange.code,
            "sequence_number_next": exchange.sequence_number_next,
            "sequence_id": exchange.sequence_id.id,
            "default_debit_account_id":exchange.default_debit_account_id.id,
            "default_credit_account_id":exchange.default_credit_account_id.id,
            "update_posted": exchange.update_posted
        }
        self.env['account.journal'].sudo().create(data)

    def create_stock(self,record,stock):
        data = {
            "name": stock.name,
            "type": stock.type,
            "company_id": record.id,
            "code": stock.code,
            "sequence_number_next": stock.sequence_number_next,
            "sequence_id": stock.sequence_id.id,
            "update_posted": stock.update_posted
        }
        self.env['account.journal'].sudo().create(data)


    @api.model
    def create(self, values):
        main_company_obj = self.env['res.company'].search([('id','=',1)])
        if main_company_obj:

            customer_invoice_obj = self.env['account.journal'].search([('name','=','Customer Invoices'),('company_id','=',main_company_obj.id)])
            vendor_bill = self.env['account.journal'].search([('name','=','Vendor Bills'),('company_id','=',main_company_obj.id)])
            miscell = self.env['account.journal'].search([('name','=','Miscellaneous Operations'),('company_id','=',main_company_obj.id)])
            exchnage = self.env['account.journal'].search([('name','=','Exchange Difference'),('company_id','=',main_company_obj.id)])
            stock = self.env['account.journal'].search(
                [('name', '=', 'Stock Journal'), ('company_id', '=', main_company_obj.id)])

            record = super(CreateCompany, self).create(values)
            if customer_invoice_obj:
                self.create_customer_inv(record,customer_invoice_obj)

            if vendor_bill:
                self.create_vendor(record,vendor_bill)

            if miscell:
                self.create_miscell(record,miscell)
            if exchnage:
                self.create_exchnage(record,exchnage)

            if stock:
                self.create_stock(record,stock)

            return record

        return super(CreateCompany, self).create(values)