from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools.misc import formatLang
import html2text


class print_customer_statement_xlsx(models.AbstractModel):
    _name = 'report.goexcel_customer_statement.cust_statement_template_xlsx'
    _inherit = ['report.report_xlsx.abstract', 'report.goexcel_customer_statement.cust_statement_template']

    @api.multi
    def set_amount(self, amount):
        if amount == 0:
            return '-'
        amount = formatLang(self.env, amount)
        return amount

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            #'border': True
        })
        self.content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'border': True,
            'font': 'Arial',
        })
        self.content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'bottom': True,
            'font': 'Arial',
        })
        self.line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'top': True,
            'bottom': True,
            'font': 'Arial',
        })
        self.line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'text_wrap': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'bottom': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'valign': 'top'
        })

    def _format_float_and_dates(self, currency_id, lang_id):

        self.line_header.num_format = currency_id.excel_format
        self.line_header_light.num_format = currency_id.excel_format
        self.line_header_light_initial.num_format = currency_id.excel_format
        self.line_header_light_ending.num_format = currency_id.excel_format


        self.line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        self.content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

    def convert_to_date(self, datestring=False):
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(self.language_id.date_format)
            return datetime.strptime(datestring, self.language_id.date_format)
        else:
            return False

    def generate_xlsx_report(self, workbook, data, record):
        self._define_formats(workbook)

        partner = record.partner_ids[0]
        if partner.soa_type == 'all':
            data = self.get_lines(partner)
        else:
            data = self.get_lines_open(partner)

        for currency, lines in data.items():
            sheet = workbook.add_worksheet(currency.name)

            # HEADER
            if partner.account_type == 'ar':
                report_name = "Customer Statement Of Account"
            elif partner.account_type == 'ap':
                report_name = "Supplier Statement Of Account"
            else:
                report_name = "Statement Of Account"
            sheet.merge_range(1, 0, 1, 6, report_name, self.line_header)

            # CONTACT INFO
            start_row = 3
            sheet.merge_range(start_row, 0, start_row, 3, partner.name, self.line_header_left)
            if partner.street:
                start_row += 1
                sheet.merge_range(start_row, 0, start_row, 3, partner.street, self.line_header_left)
            address = ', '.join([ad
                               for ad in
                               [partner.street2, partner.zip, partner.city, partner.state_id.name, partner.country_id.name]
                               if ad])
            if address:
                start_row += 1
                sheet.merge_range(start_row, 0, start_row, 3, address, self.line_header_left)
            if partner.phone:
                start_row += 1
                sheet.write_string(start_row, 0, "Tel", self.line_header)
                sheet.merge_range(start_row, 1, start_row, 2, partner.phone, self.line_header)
            if partner.attention:
                start_row += 1
                sheet.write_string(start_row, 0, "Attn", self.line_header)
                sheet.merge_range(start_row, 1, start_row, 2, partner.attention, self.line_header)
            if partner.ref and record.print_partner_ref:
                start_row += 1
                sheet.write_string(start_row, 0, "Internal ref", self.line_header_left)
                sheet.merge_range(start_row, 1, start_row, 2, partner.ref, self.line_header)

            # REPORT INFO
            sheet.write_string(4, 5, "As Of", self.line_header)
            sheet.write_string(4, 6, partner.overdue_date.strftime('%d-%m-%Y'), self.line_header)
            sheet.write_string(5, 5, "Currency", self.line_header)
            sheet.write_string(5, 6, currency.name, self.line_header)

            start_row += 2
            if start_row <= 5:
                start_row += 2

            # DATA HEADINGS
            show_term = False
            if partner.account_type == 'ar' and partner.show_payment_term:
                show_term = True
                headings = "Date,Invoice #,Ref,Due Date,Term,Debit,Credit,Balance".split(',')
            else:
                headings = "Date,Invoice #,Ref,Due Date,Debit,Credit,Balance".split(',')

            # DATA LISTS
            sheet.set_column(0, len(headings), 15)
            for idx, heading in enumerate(headings):
                sheet.write_string(start_row, idx, heading, self.format_header)
            total_debit, total_credit, total_balance, total = 0, 0, 0, 0
            for line in lines:
                start_row += 1
                if not line.get('date'):
                    sheet.write_string(start_row, 1, line.get('ref'), self.line_header)
                    sheet.write_string(start_row, 6 + show_term, self.set_amount(line.get('total')), self.line_header)
                    total += line.get('total')
                else:
                    # if partner.aging_by == 'due_date':
                    #     date = line.get('date_maturity').strftime('%d-%m-%Y')
                    # else:
                    #     date = line.get('date').strftime('%d-%m-%Y')
                    sheet.write_string(start_row, 0, line.get('date').strftime('%d-%m-%Y'), self.line_header)
                    sheet.write_string(start_row, 1, line.get('inv_ref', ''), self.line_header)
                    sheet.write_string(start_row, 2, line.get('payment_ref', ''), self.line_header)
                    sheet.write_string(start_row, 3, line.get('date_maturity').strftime('%d-%m-%Y'), self.line_header)
                    if show_term:
                        sheet.write_string(start_row, 4, line.get('payment_term') or '', self.line_header)
                    sheet.write_string(start_row, 4 + show_term, self.set_amount(line.get('debit')), self.line_header)
                    sheet.write_string(start_row, 5 + show_term, self.set_amount(line.get('credit')), self.line_header)
                    total += line.get('total')
                    sheet.write_string(start_row, 6 + show_term, self.set_amount(total), self.line_header)
                    total_debit += line.get('debit')
                    total_credit += line.get('credit')

            # DATA SUB-TOTAL
            start_row += 1
            sheet.merge_range(start_row, 0, start_row, 3 + show_term, 'Sub-Total', self.format_header)
            sheet.write_string(start_row, 4 + show_term, self.set_amount(total_debit), self.line_header)
            sheet.write_string(start_row, 5 + show_term, self.set_amount(total_credit), self.line_header)
            sheet.write_string(start_row, 6 + show_term, self.set_amount(total), self.line_header)

            # AGING DATA
            start_row += 2
            # if partner.soa_type == 'all':
            #     aging = self.set_ageing_all(partner)
            # else:
            #     aging = self.set_ageing_all(partner).get(currency, [{}])
            aging = self.set_ageing_all(partner)

            if partner.aging_group == 'by_month':
                headings = "Not Due,Current Month,1 Month,2 Months,3 Months,4 Months,5 Months & Above,Total".split(',')
                # del aging[currency]['not_due']
            else:
                headings = "Not Due,1-30,31-60,61-90,91-120,121-150,Over 150,Total".split(',')
            for idx, heading in enumerate(headings):
                sheet.write_string(start_row, idx, heading, self.format_header)
            start_row += 1
            for idx, amount in enumerate(aging[currency][0].values()):
                sheet.write_string(start_row, idx, self.set_amount(amount), self.line_header)

            # SOA NOTE
            start_row += 2
            sheet.write_string(start_row, 0, 'SOA NOTE', self.line_header)
            soa_note = self.env.user.company_id.soa_note or ''
            sheet.merge_range(start_row, 1, start_row + 5, 6, html2text.html2text(soa_note), self.line_header_left)
