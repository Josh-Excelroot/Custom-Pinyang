from odoo import models
from datetime import datetime


class BulkBankPaymentsXlsx(models.AbstractModel):
    _name = 'report.bulk_bank_payments.report_bulk_bank_payments_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        format_header = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        format_bold = workbook.add_format({'bold': True})
        number_format = workbook.add_format({'num_format': '#,##0.00'})

        sheet = workbook.add_worksheet('Payments')

        # Alliance Bank
        headers = ['Payment Mode',
                   'Beneficiary Name',
                   'Beneficiary Account',
                   'Beneficiary Bank Code',
                   'Amount',
                   'Payment Description',
                   'Payment Reference',
                   'Beneficiary New IC No',
                   'Beneficiary Old IC No',
                   'Beneficiary Business Registration',
                   'Beneficiary Others',
                   'Payment Advice Indicator',
                   'Mobile Phone No',
                   'Beneficiary Email 1',
                   'Beneficiary Email 2',
                   'Generic Payment Information',
                   'Payment Date',
                   'Beneficiary Address',
                   ]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, format_header)
            sheet.set_column(col, col, (len(header)*1.5))

        row = 1
        for payment in lines.vendor_payment_ids:
            payment_mode = dict(payment._fields['payment_type'].selection).get(payment.payment_type) or ''
            beneficiary_name = payment.partner_id.name or ''
            beneficiary_account = (', '.join([bank.bank_id.name for bank in payment.partner_id.bank_ids])) or ''
            beneficiary_bank_code = (', '.join([bank.acc_number for bank in payment.partner_id.bank_ids])) or ''
            amount = payment.amount or ''
            payment_description = ''
            payment_reference = payment.reference or ''
            beneficiary_new_ic_no = ''
            beneficiary_old_ic_no = ''
            beneficiary_business_registration = ''
            beneficiary_others = ''
            payment_advice_indicator = ''
            mobile_phone_no = '' # payment.partner_id.phone
            beneficiary_email_1 = payment.partner_id.email or ''
            beneficiary_email_2 = ''
            generic_payment_information = ''
            payment_date = str(payment.payment_date) or str(datetime.today().strftime('%d/%m/%y'))
            beneficiary_address = payment.partner_id.street or ''

            sheet.write(row, 0, payment_mode)
            sheet.write(row, 1, beneficiary_name)
            sheet.write(row, 2, beneficiary_account)
            sheet.write(row, 3, beneficiary_bank_code)
            sheet.write(row, 4, amount, number_format)
            sheet.write(row, 5, payment_description)
            sheet.write(row, 6, payment_reference)
            sheet.write(row, 7, beneficiary_new_ic_no)
            sheet.write(row, 8, beneficiary_old_ic_no)
            sheet.write(row, 9, beneficiary_business_registration)
            sheet.write(row, 10, beneficiary_others)
            sheet.write(row, 11, payment_advice_indicator)
            sheet.write(row, 12, mobile_phone_no)
            sheet.write(row, 13, beneficiary_email_1)
            sheet.write(row, 14, beneficiary_email_2)
            sheet.write(row, 15, generic_payment_information)
            sheet.write(row, 16, payment_date)
            sheet.write(row, 17, beneficiary_address)
            row += 1