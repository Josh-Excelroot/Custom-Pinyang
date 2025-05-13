# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class SSTReportXslx(models.AbstractModel):
    _name = 'report.a_f_r.report_sst_report_xlsx'
    _inherit = 'report.account_financial_report.abstract_report_xlsx'

    def _get_report_name(self, report):
        report_name = _('SST Report')
        return self._get_report_complete_name(report, report_name)

    def _get_report_columns(self, report): #Customer Inv. No Inv. Date Paid Date Inv. Total Taxable SST Amt Received
        if report.is_b2b_exemption:
            return {
                0: {'header': _('Customer'), 'field': 'customer', 'type':'many2one', 'width': 40},
                1: {'header': _('Inv. No'), 'field': 'invoice_no',  'width': 15},
                2: {'header': _('Inv. Date'),'field': 'invoice_date', 'type':'date', 'width': 10},
                3: {'header': _('Paid Date'),'field': 'invoice_paid_date','type':'date',  'width': 10},
                4: {'header': _('Inv. Total'),'field': 'invoice_amount', 'type': 'sst_report_amount', 'width': 10},
                5: {'header': _('Taxable Amt 6%'),'field': 'taxable_amount_6_percent','type': 'sst_report_amount',  'width': 20},
                6: {'header': _('Taxable Amt 8%'),'field': 'taxable_amount_8_percent','type': 'sst_report_amount',  'width': 20},
                7: {'header': _('SST Amt 6%'),'field': 'sst_6_percent','type': 'sst_report_amount',  'width': 20},
                8: {'header': _('SST Amt 8%'),'field': 'sst_8_percent','type': 'sst_report_amount',  'width': 20},
                9: {'header': _('B2B Exemption Amt'),'field': 'b2b_exemption_amt','type': 'sst_report_amount',  'width': 20},
                10: {'header': _('Received Amt'),'field': 'received_invoice_amount', 'type': 'sst_report_amount', 'width': 20},
                11: {'header': _('Received Taxable Amt'),'field': 'received_taxable_invoice_amount', 'type': 'sst_report_amount', 'width': 20},
                12: {'header': _('Received SST Amt'),'field': 'received_taxable_amount','type': 'sst_report_amount',  'width': 20},
            }
        else:
            return {
                0: {'header': _('Customer'), 'field': 'customer', 'type': 'many2one', 'width': 40},
                1: {'header': _('Inv. No'), 'field': 'invoice_no', 'width': 15},
                2: {'header': _('Inv. Date'), 'field': 'invoice_date', 'type': 'date', 'width': 10},
                3: {'header': _('Paid Date'), 'field': 'invoice_paid_date', 'type': 'date', 'width': 10},
                4: {'header': _('Inv. Total'), 'field': 'invoice_amount', 'type': 'amount_currency', 'width': 10},
                5: {'header': _('Taxable Amt 6%'), 'field': 'taxable_amount_6_percent',
                    'type': 'amount_currency', 'width': 20},
                6: {'header': _('Taxable Amt 8%'), 'field': 'taxable_amount_8_percent',
                    'type': 'amount_currency', 'width': 20},
                7: {'header': _('SST Amt 6%'), 'field': 'sst_6_percent', 'type': 'amount_currency', 'width': 20},
                8: {'header': _('SST Amt 8%'), 'field': 'sst_8_percent', 'type': 'amount_currency', 'width': 20},
                7: {'header': _('Received Amt'), 'field': 'received_invoice_amount', 'type': 'amount_currency',
                    'width': 20},
                8: {'header': _('Received Taxable Amt'), 'field': 'received_taxable_invoice_amount',
                    'type': 'amount_currency', 'width': 20},
                9: {'header': _('Received SST Amt'), 'field': 'received_taxable_amount', 'type': 'amount',
                     'width': 20},
            }


    def _get_report_filters(self, report):
        return [
            [_('Date from'), report.date_from.strftime('%d-%m-%Y')],
            [_('Date to'), report.date_to.strftime('%d-%m-%Y')],
            [_('Paid SST'), report.paid_only],
        ]

    def _get_col_count_filter_name(self):
        return 0

    def _get_col_count_filter_value(self):
        return 2

    def write_totals(self, totals_dict):
        col = 3
        self.sheet.write_string(self.row_pos, col, "Totals", self.format_header_left)
        for total_key, total_value in totals_dict.items():
            col += 1
            self.sheet.write_number(self.row_pos, col, float(total_value), self.format_sst_report_amount)

    def _generate_report_content(self, workbook, report):
        # For each taxtag
        self.write_array_header()
        inv_total = 0.0000
        total_taxable_amount_6_percent = 0.0000
        total_taxable_amount_8_percent = 0.0000
        total_sst_6_percent = 0.0000
        total_sst_8_percent = 0.0000
        total_b2b_exemption_amt = 0.0000
        total_received_invoice_amount = 0.0000
        total_received_taxable_invoice_amount = 0.0000
        total_received_taxable_amount = 0.0000
        if report.is_b2b_exemption:
            for taxtag in report.taxdetails_ids:
                # if taxtag.customer.property_account_position_id:
                #         if taxtag.b2b_exemption_amt == 0 and taxtag.sst_6_percent != 0:
                #             taxtag.b2b_exemption_amt = taxtag.sst_6_percent
                #             taxtag.sst_6_percent = 0
                #         elif taxtag.b2b_exemption_amt == 0 and taxtag.sst_8_percent != 0:
                #             taxtag.b2b_exemption_amt = taxtag.sst_8_percent
                #             taxtag.sst_8_percent = 0
                #         taxtag.received_taxable_invoice_amount = 0
                #         taxtag.received_taxable_amount = 0
                # else:
                #     taxtag.b2b_exemption_amt = 0

                inv_total += taxtag.invoice_amount
                total_taxable_amount_6_percent += taxtag.taxable_amount_6_percent
                total_taxable_amount_8_percent += taxtag.taxable_amount_8_percent
                total_sst_6_percent += taxtag.sst_6_percent
                total_sst_8_percent += taxtag.sst_8_percent
                total_b2b_exemption_amt += taxtag.b2b_exemption_amt
                total_received_invoice_amount += taxtag.received_invoice_amount
                total_received_taxable_invoice_amount += taxtag.received_taxable_invoice_amount
                total_received_taxable_amount += taxtag.received_taxable_amount
                self.write_line(taxtag)
        else:
            for taxtag in report.taxdetails_ids:
                inv_total += taxtag.invoice_amount
                total_taxable_amount_6_percent += taxtag.taxable_amount_6_percent
                total_taxable_amount_8_percent += taxtag.taxable_amount_8_percent
                total_sst_6_percent += taxtag.sst_6_percent
                total_sst_8_percent += taxtag.sst_8_percent
                total_b2b_exemption_amt += taxtag.b2b_exemption_amt
                total_received_invoice_amount += taxtag.received_invoice_amount
                total_received_taxable_invoice_amount += taxtag.received_taxable_invoice_amount
                total_received_taxable_amount += taxtag.received_taxable_amount
                self.write_line(taxtag)
        currency = self.env.user.company_id.currency_id

        # Dictionary with the totals
        totals = {
            'inv_total': inv_total,
            'total_taxable_amount_6_percent': total_taxable_amount_6_percent,
            'total_taxable_amount_8_percent': total_taxable_amount_8_percent,
            'total_sst_6_percent': total_sst_6_percent,
            'total_sst_8_percent': total_sst_8_percent,
            'total_b2b_exemption_amt': total_b2b_exemption_amt,
            'total_received_invoice_amount': total_received_invoice_amount,
            'total_received_taxable_invoice_amount': total_received_taxable_invoice_amount,
            'total_received_taxable_amount': total_received_taxable_amount,
        }

        # Round each total using the currency rounding method
        rounded_totals = {key: currency.round(value) for key, value in totals.items()}
        self.write_totals(totals)

        # self.write_account_footer(report,
        #                           _('Total'),
        #                           'field_footer_total',
        #                           self.format_header_right,
        #                           self.format_header_amount,
        #                           False)
            # self.write_ending_balance(report.taxdetails_ids)