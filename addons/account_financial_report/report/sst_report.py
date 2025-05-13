# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from datetime import datetime, timedelta


class SSTReport(models.TransientModel):
    _name = "report_sst_report"
    _inherit = 'account_financial_report_abstract'
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * SSTReport
    ** SSTReportDetails
    *** SSTReportTax
    """

    # Filters fields, used for data computation
    company_id = fields.Many2one(comodel_name='res.company')
    date_from = fields.Date()
    date_to = fields.Date()
    paid_only = fields.Selection([('paid', 'Paid SST'),
                                  ('unpaid', 'Unpaid SST'), ('all', 'All')], string='Paid SST or All', required=True,
                                 default='all')
    is_b2b_exemption = fields.Boolean(string="Include B2B Exemption")
    type_of_tax = fields.Selection([('Sales Tax', 'Sales Tax'), ('Service Tax', 'Service Tax'), ], string='Type of Tax',
                                   required=True, default='Sales Tax')
    # Data fields, used to browse report data
    taxdetails_ids = fields.One2many(
        comodel_name='report_sst_report_taxdetails',
        inverse_name='report_id'
    )
    sst_6_taxable_invoice_amount = fields.Float(digits=(16, 2))
    sst_8_taxable_invoice_amount = fields.Float(digits=(16, 2))
    sst_02_b2b_exemption_amt = fields.Float(digits=(16, 2))
    sst_total = fields.Float(digits=(16, 2))


class SSTReportTaxDetails(models.TransientModel):
    _name = 'report_sst_report_taxdetails'
    _inherit = 'account_financial_report_abstract'
    _order = 'invoice_date ASC'

    report_id = fields.Many2one(
        comodel_name='report_sst_report',
        ondelete='cascade',
        index=True
    )

    invoice_id = fields.Many2one(
        'account.invoice',
        index=True,
        string='Invoice',
    )
    # Data fields, used to keep link with real object
    # taxtag_id = fields.Many2one(
    #     'account.account.tag',
    #     index=True
    # )
    # taxgroup_id = fields.Many2one(
    #     'account.tax.group',
    #     index=True
    # )

    # Data fields, used for report display
    customer = fields.Many2one('res.partner', string="Customer")
    # customer = fields.Char(string="Customer")
    invoice_no = fields.Char(string='Inv. No')
    invoice_date = fields.Date(string='Inv. Date')
    invoice_paid_date = fields.Date(string='Inv. Paid Date')
    invoice_amount = fields.Float(digits=(16, 2), string='Inv. Amount')
    invoice_taxable_amount = fields.Float(digits=(16, 2), string='Taxable Amount')
    taxable_amount_6_percent = fields.Float(digits=(16, 2), string='Taxable Amount 6%')
    taxable_amount_8_percent = fields.Float(digits=(16, 2), string='Taxable Amount 8%')
    sst_amount = fields.Float(digits=(16, 2), string='SST Amount')
    b2b_exemption_amt = fields.Float(digits=(16, 2), string='B2B Exemption Amount')
    sst_6_percent = fields.Float(digits=(16, 2), string='SST 6%')
    sst_8_percent = fields.Float(digits=(16, 2), string='SST 8%')
    received_invoice_amount = fields.Float(digits=(16, 2), string='Received Amount')
    received_taxable_invoice_amount = fields.Float(digits=(16, 2), string='Received Taxable Amount')
    received_taxable_invoice_amount_6_percent = fields.Float(digits=(16, 2), string='Received Taxable Amount 6%')
    received_taxable_invoice_amount_8_percent = fields.Float(digits=(16, 2), string='Received Taxable Amount 8%')
    received_taxable_amount = fields.Float(digits=(16, 2), string='Received SST Amount')
    received_taxable_amount_6_percent = fields.Float(digits=(16, 2), string='Received SST Amount 6%')
    received_taxable_amount_8_percent = fields.Float(digits=(16, 2), string='Received SST Amount 8%')

    # Data fields, used to browse report data
    tax_ids = fields.One2many(
        comodel_name='report_sst_report_tax',
        inverse_name='report_tax_id',
        string='Taxes'
    )


class SSTReportTax(models.TransientModel):
    _name = 'report_sst_report_tax'
    _inherit = 'account_financial_report_abstract'
    _order = 'invoice_date ASC'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    report_tax_id = fields.Many2one(
        comodel_name='report_sst_report_taxdetails',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    invoice_id = fields.Many2one(
        'account.invoice',
        index=True,
        string='Invoice',
    )

    # Data fields, used for report display
    # customer = fields.One2many('res.partner', string="Customer")
    customer = fields.Char(string="Customer")
    invoice_no = fields.Char(string='Inv. No')
    invoice_date = fields.Date(string='Inv. Date')
    invoice_paid_date = fields.Date(string='Inv. Paid Date')
    invoice_amount = fields.Float(digits=(16, 2), string='Inv. Amount')
    invoice_taxable_amount = fields.Float(digits=(16, 2), string='Taxable Amount')
    sst_amount = fields.Float(digits=(16, 2), string='SST Amount')
    # sst_6_percent = fields.Float(digits=(16, 2), string='SST 6%')
    # sst_8_percent = fields.Float(digits=(16, 2), string='SST 8%')
    received_invoice_amount = fields.Float(digits=(16, 2), string='Received Amount', default=0.00)
    received_taxable_invoice_amount = fields.Float(digits=(16, 2), string='Received Taxable Amount', default=0.00)
    received_taxable_amount = fields.Float(digits=(16, 2), string='Received SST Amount', default=0.00)
    # company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})


class SSTReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_sst_report'

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_sst_report_xlsx'
        else:
            report_name = 'account_financial_report.report_sst_report_qweb'
        context = dict(self.env.context)
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self, config=False)

    def print_report_sst(self, report_type='qweb'):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_sst_report_xlsx'
        else:
            report_name = 'account_financial_report.second_report_sst_report_qweb'
        context = dict(self.env.context)
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self, config=False)

    def last_day_of_next_month(self,input_date):
        # Convert the input date to a datetime object
        date_obj = datetime.strptime(str(input_date), '%Y-%m-%d')

        # Calculate the first day of the next month
        first_day_next_month = date_obj.replace(day=1) + timedelta(days=32)

        # Calculate the last day of the next month
        last_day_next_month = (first_day_next_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        print(type(last_day_next_month))
        return last_day_next_month.strftime('%d-%m-%Y')

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref('account_financial_report.report_sst_report').render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # TS Enhancement - add to get the unpaid invoices over X days
        ctx = self._context
        if self.paid_only == 'paid' or ctx.get('sst_02', False):
            self.get_sst_data_calculation()
        elif self.paid_only == 'unpaid':
            self._inject_unpaid_sst_values()
        elif self.paid_only == 'all':
            self._inject_all_sst_values()

        # Compute report data
        # if self.paid_only == 'paid':
        #     self._inject_sst_paid_values()
        # else:
        #     self._inject_all_sst_values()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

    def _inject_sst_paid_values(self):
        query_inject_sstpaid = """
            SELECT
                ai.id as invoice_id,
                ai.partner_id as customer,
                ai.number as invoice_no,
                ai.date_invoice as invoice_date,
                ai.amount_total as invoice_amount,
                ai.amount_untaxed as invoice_taxable_amount,
                ai.amount_tax as sst_amount,
                ai.amount_total as received_invoice_amount,
                ai.amount_untaxed as received_taxable_invoice_amount,
                ai.amount_tax as received_taxable_amount
            FROM
                account_invoice ai
            LEFT JOIN
                res_company company on (company.id = ai.company_id)
            WHERE
                ai.company_id = %s AND
                ai.type in ('out_invoice', 'out_refund') AND
                ai.state = 'paid' AND
                ai.date_invoice >= %s AND
                ai.date_invoice <= %s AND
                ai.amount_tax > 0
            ORDER BY
                ai.date_invoice asc
        """
        query_inject_sstpaid_params = (self.company_id.id, self.date_from,
                                       self.date_to)
        self.env.cr.execute(query_inject_sstpaid, query_inject_sstpaid_params)
        sst_results = self._cr.dictfetchall()
        # print('_inject_sst_paid_values after dicfetchall')
        # print (">>>>>>>>>>>>sst_results", sst_results)
        if sst_results:
            # print('sst_results=' + str(len(sst_results)))
            # print('sst_results=' + str(sst_results))
            ReportLine = self.env['report_sst_report_taxdetails']
            self.taxdetails_ids = [ReportLine.new(line).id for line in sst_results]

    def _inject_unpaid_sst_values(self):
        b2b_exempt_tax = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 0),
             ('active', '=', True)], limit=1)
        b2b_exempt_tax_name = b2b_exempt_tax.name if b2b_exempt_tax else ''
        if b2b_exempt_tax_name and '%' == b2b_exempt_tax_name[-1]:
            b2b_exempt_tax_name = b2b_exempt_tax_name + '%'
        sst_6_percent_search = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 6),
             ('active', '=', True)], limit=1)
        sst_6_percent_name = sst_6_percent_search.name if sst_6_percent_search else ''
        if sst_6_percent_name and '%' == sst_6_percent_name[-1]:
            sst_6_percent_name = sst_6_percent_name + '%'
        sst_8_percent_search = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 8),
             ('active', '=', True)], limit=1)
        sst_8_percent_name = sst_8_percent_search.name if sst_8_percent_search else ''
        if sst_8_percent_name and '%' == sst_8_percent_name[-1]:
            sst_8_percent_name = sst_8_percent_name + '%'
        query_inject_unpaid_sst_values = f"""
           SELECT
                ai.id AS invoice_id,
                ai.type AS invoice_type,
                ai.partner_id AS customer,
                ai.number AS invoice_no,
                ai.date_invoice AS invoice_date,
                sum(aml.credit) AS invoice_amount,
                SUM(
                    CASE
                        WHEN aml.name like '{sst_6_percent_name}'
                        THEN aml.tax_base_amount
                        ELSE 0
                    END
                ) AS taxable_amount_6_percent,
                SUM(
                    CASE
                        WHEN aml.name LIKE '{sst_6_percent_name}' THEN 
                            CASE
                                WHEN ai.type = 'out_invoice' THEN aml.credit
                                WHEN ai.type = 'out_refund' THEN aml.debit
                                ELSE 0
                            END
                        ELSE 0
                    END
                ) AS sst_6_percent,
                SUM(
                    CASE
                        WHEN aml.name LIKE '{sst_8_percent_name}'
                        THEN aml.tax_base_amount
                        ELSE 0
                    END
                ) AS taxable_amount_8_percent,
                SUM(
                    CASE
                        WHEN aml.name LIKE '{sst_8_percent_name}' THEN
                        CASE
                            WHEN ai.type = 'out_invoice' THEN aml.credit
                            WHEN ai.type = 'out_refund' THEN aml.debit
                        END
                        ELSE 0
                    END
                ) AS sst_8_percent
            FROM
                account_invoice ai
            LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id
            LEFT JOIN account_invoice_tax ait ON ait.invoice_id = ai.id
            WHERE
                ai.company_id = %s AND
                ai.date_invoice >= %s AND
                ai.date_invoice <= %s AND
                ai.type in ('out_invoice', 'out_refund') AND
                ai.state in ('open') AND
                ait.id IS NOT NULL
            GROUP BY
                ai.id
            ORDER BY
                ai.date_invoice asc;
        """
        query_inject_unpaid_sst_values_b2b = f"""
        SELECT
            ai.id AS invoice_id,
            ai.type AS invoice_type,
            ai.partner_id AS customer,
            ai.number AS invoice_no,
            ai.date_invoice AS invoice_date,
            sum(aml.credit) AS invoice_amount,
            SUM(
                CASE
                    WHEN aml.name like '{sst_6_percent_name}' OR aml.name like '{b2b_exempt_tax_name}'
                    THEN aml.tax_base_amount
                    ELSE 0
                END
            ) AS taxable_amount_6_percent,
            SUM(
                CASE
                    WHEN aml.name LIKE '{sst_6_percent_name}' THEN 
                        CASE
                            WHEN ai.type = 'out_invoice' THEN aml.credit
                            WHEN ai.type = 'out_refund' THEN aml.debit
                            ELSE 0
                        END
                    ELSE 0
                END
            ) AS sst_6_percent,
            SUM(
                CASE
                    WHEN aml.name LIKE '{sst_8_percent_name}'
                    THEN aml.tax_base_amount
                    ELSE 0
                END
            ) AS taxable_amount_8_percent,
            SUM(
                CASE
                    WHEN aml.name LIKE '{sst_8_percent_name}' THEN
                    CASE
                        WHEN ai.type = 'out_invoice' THEN aml.credit
                        WHEN ai.type = 'out_refund' THEN aml.debit
                    END
                    ELSE 0
                END
            ) AS sst_8_percent,
            SUM(
                CASE
                    WHEN aml.name like '{b2b_exempt_tax_name}' THEN 
                        CASE
                            WHEN ai.type = 'out_invoice' THEN aml.credit
                            WHEN ai.type = 'out_refund' THEN aml.debit
                            ELSE 0
                        END
                    ELSE 0
                END
            ) AS b2b_exemption_amt
        FROM
            account_invoice ai
        LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id
        LEFT JOIN account_invoice_tax ait ON ait.invoice_id = ai.id
        WHERE
            ai.company_id = %s AND
            ai.date_invoice >= %s AND
            ai.date_invoice <= %s AND
            ai.type in ('out_invoice', 'out_refund') AND
            ai.state in ('open') AND
            ait.id IS NOT NULL
        GROUP BY
            ai.id
        ORDER BY
            ai.date_invoice asc;
        """
        # ai.amount_total as received_invoice_amount,
        # ai.amount_untaxed as received_taxable_invoice_amount,
        # ai.amount_tax as received_taxable_amount
        # ai.amount_untaxed as invoice_taxable_amount,
        query = """"""
        if self.is_b2b_exemption:
            query = query_inject_unpaid_sst_values_b2b
        else:
            query = query_inject_unpaid_sst_values
        # TODO # TS - Have to loop into invoice to get the Taxable amount / Received invoice amount (if partially paid)
        self.env.cr.execute(query, (self.company_id.id, self.date_from, self.date_to))
        sst_values = self.env.cr.dictfetchall()
        for val in sst_values:
            if val.get('invoice_type') and val.get('invoice_type') in ['in_refund', 'out_refund']:
                val['invoice_amount'] = -val['invoice_amount']
                val['sst_6_percent'] = -val['sst_6_percent']
                val['taxable_amount_6_percent'] = -val['taxable_amount_6_percent']
                val['sst_8_percent'] = -val['sst_8_percent']
                val['taxable_amount_8_percent'] = -val['taxable_amount_8_percent']
                if val.get('b2b_exemption_amt', False):
                    val['b2b_exemption_amt'] = -val['b2b_exemption_amt']
        sst_results = sst_values
        if sst_results:
            ReportLine = self.env['report_sst_report_taxdetails']
            self.taxdetails_ids = [ReportLine.new(line).id for line in sst_results]

    def get_sst_data_calculation(self):
        qry = """
            SELECT
                ap.id as payment_id,
                ap.name as payment_name,
                ap.partner_id as partner_id,
                ap.amount as payment_amount,
                ap.payment_date as payment_date,
                ap.payment_type as payment_type,
                ai.id as invoice_id,
                aml.id as move_line_id,
                aml.amount_residual,
                aml.credit
            FROM
                account_payment ap
            LEFT JOIN
                account_invoice_payment_rel aipr ON ap.id = aipr.payment_id
            LEFT JOIN
                account_invoice ai ON ai.id = aipr.invoice_id
            LEFT JOIN
                account_move_line aml ON aml.invoice_id = ai.id
            WHERE
                ap.company_id = %s AND
                ap.partner_type = 'customer' AND
                ap.payment_date >= %s AND
                ap.payment_date <= %s AND
                ap.amount > 0 AND
                aml.amount_residual = 0 AND
                aml.credit > 0
            ORDER BY
                ap.payment_date ASC
        """
        qry_param = (self.company_id.id, self.date_from, self.date_to)
        self.env.cr.execute(qry, qry_param)
        qry_result = self._cr.dictfetchall()

        inv = {}
        for res in qry_result:
            invoice_id = res.get('invoice_id')
            move_line_id = res.get('move_line_id')
            if invoice_id not in inv:
                inv[invoice_id] = []
            inv[invoice_id].append(move_line_id)

        final_inv = []
        sst_6_taxable_invoice_amount = 0.0
        sst_8_taxable_invoice_amount = 0.0
        for invoice_id, move_lines in inv.items():
            invoice = self.env['account.invoice'].browse(invoice_id)
            if invoice.amount_tax > 0 and invoice.company_id == self.company_id and invoice.state in ['paid',
                                                                                                      'open'] and invoice.amount_total and invoice.amount_untaxed:
                # paid_amt = sum([self.env['account.move.line'].browse(ml_id).credit for ml_id in move_lines])
                result = self.get_tax_percentage(invoice)
                if result:
                    final_inv.append(result)
            elif invoice.partner_id.property_account_position_id and invoice.tax_line_ids and invoice.company_id == self.company_id and invoice.state in [
                'paid', 'open'] and invoice.amount_total:
                # paid_amt = sum([self.env['account.move.line'].browse(ml_id).credit for ml_id in move_lines])
                result = self.get_tax_percentage(invoice)
                if result:
                    final_inv.append(result)

        current_invoices = [x['invoice_id'] for x in final_inv]
        remaining_sst_invoices = self.with_context(get_paid_invoices=True)._inject_all_sst_values()
        for data in remaining_sst_invoices:
            if data['invoice_id'] not in current_invoices:
                if data.get('invoice_paid_date', False):
                    paid_date = data['invoice_paid_date']
                    if self.date_from <= paid_date <= self.date_to:
                        # Invoice Total
                        data['received_invoice_amount'] = data['invoice_amount']
                        # Taxable Total
                        data['received_taxable_invoice_amount'] = data.get('taxable_amount_6_percent', 0) + data.get(
                            'taxable_amount_8_percent', 0)
                        # Tax Amount
                        data['received_taxable_amount'] = data.get('sst_6_percent', 0) + data.get('sst_8_percent', 0)
                        final_inv.append(data)

        if final_inv:
            if self._context.get('sst_02', False):
                self.sst_6_taxable_invoice_amount = sum(res['taxable_amount_6_percent'] for res in final_inv)
                self.sst_8_taxable_invoice_amount = sum(res['taxable_amount_8_percent'] for res in final_inv)
                self.sst_total = (sst_6_taxable_invoice_amount * 0.06) + (sst_8_taxable_invoice_amount * 0.08)
                self.sst_02_b2b_exemption_amt = sum(res['b2b_exemption_amt'] for res in final_inv)
                self.invoice_taxable_amount = sst_6_taxable_invoice_amount + sst_8_taxable_invoice_amount
                ReportLine = self.env['report_sst_report_taxdetails']
                self.taxdetails_ids = [ReportLine.new(line).id for line in final_inv]

    def get_tax_percentage(self, inv, paid_amt=0):
        paid_amt = sum(
            p.amount
            for move_line in inv.payment_move_line_ids
            for p in move_line.matched_debit_ids
            if p.debit_move_id in inv.move_id.line_ids
        )

        if not inv or not paid_amt:
            return

        taxable_amount = taxable_amount_6_percent = taxable_amount_8_percent = 0
        tax_amount_6_percent = tax_amount_8_percent = 0

        # Ahmad Zaman - 21/1/25 - Added handling for negative invoice line values
        for line in inv.invoice_line_ids:
            current_line_tax = line.invoice_line_tax_ids[0] if line.invoice_line_tax_ids else False
            if line.price_tax != 0:
                taxable_amount += line.price_subtotal
                if current_line_tax.amount_type == 'percent':
                    if current_line_tax.amount == 6:
                        taxable_amount_6_percent += line.price_subtotal
                        tax_amount_6_percent += line.price_tax
                    elif current_line_tax.amount == 8:
                        taxable_amount_8_percent += line.price_subtotal
                        tax_amount_8_percent += line.price_tax
            elif current_line_tax:
                if current_line_tax.amount_type == 'percent' and current_line_tax.amount == 0:
                    taxable_amount_6_percent += line.price_subtotal

        tax_amount_6_percent = round(tax_amount_6_percent, 2)
        tax_amount_8_percent = round(tax_amount_8_percent, 2)

        received_taxable_inv_amount = received_taxable_amount = 0
        if taxable_amount != 0:
            received_taxable_inv_amount = round((taxable_amount / inv.amount_total) * paid_amt, 2)
            received_taxable_amount = round((received_taxable_inv_amount / taxable_amount) * inv.amount_tax, 2)

        received_taxable_inv_amount_6_percent = received_taxable_amount_6_percent = 0
        if taxable_amount_6_percent != 0:
            received_taxable_inv_amount_6_percent = round((taxable_amount_6_percent / inv.amount_total) * paid_amt, 2)
            received_taxable_amount_6_percent = round(
                (received_taxable_inv_amount_6_percent / taxable_amount_6_percent) * tax_amount_6_percent, 2)

        received_taxable_inv_amount_8_percent = received_taxable_amount_8_percent = 0
        if taxable_amount_8_percent != 0:
            received_taxable_inv_amount_8_percent = round((taxable_amount_8_percent / inv.amount_total) * paid_amt, 2)
            received_taxable_amount_8_percent = round(
                (received_taxable_inv_amount_8_percent / taxable_amount_8_percent) * tax_amount_8_percent, 2)

        b2b_amt = 0.0
        if inv.partner_id.property_account_position_id:
            b2b_source_taxes = set(inv.partner_id.property_account_position_id.tax_ids.mapped('tax_src_id.id'))
            b2b_dest_taxes = set(inv.partner_id.property_account_position_id.tax_ids.mapped('tax_dest_id.id'))
            for line in inv.invoice_line_ids:
                if line.invoice_line_tax_ids:
                    for tax in line.invoice_line_tax_ids:
                        if tax.id in b2b_source_taxes:
                            b2b_amt += (tax.amount * line.price_subtotal) / 100
                            if tax.amount == 6 and b2b_amt > 0:
                                tax_amount_6_percent = 0
                            elif tax.amount == 8 and b2b_amt > 0:
                                tax_amount_8_percent = 0
                        elif tax.id in b2b_dest_taxes:
                            b2b_amt += (6 * line.price_subtotal) / 100
                            if tax.amount == 6 and b2b_amt > 0:
                                tax_amount_6_percent = 0
                            elif tax.amount == 8 and b2b_amt > 0:
                                tax_amount_8_percent = 0

        exchange_rate = 1
        if inv.currency_id.id != self.env.user.company_id.currency_id.id:
            exchange_rate = inv.exchange_rate_inverse

        base_data = {
            'customer': inv.partner_id.id,
            'invoice_no': inv.number,
            'invoice_date': inv.date_invoice,
            'invoice_id': inv.id,
            'b2b_exemption_amt': b2b_amt,
            'invoice_paid_date': inv.payment_move_line_ids and inv.payment_move_line_ids[0].date or '',
        }

        if inv.type in ['in_refund', 'out_refund']:
            return_data = {
                **base_data,
                'invoice_amount': -inv.amount_total * exchange_rate,
                'invoice_taxable_amount': -(taxable_amount + b2b_amt) * exchange_rate,
                'taxable_amount_6_percent': -taxable_amount_6_percent * exchange_rate,
                'taxable_amount_8_percent': -taxable_amount_8_percent * exchange_rate,
                'sst_amount': -(inv.amount_tax + b2b_amt) * exchange_rate,
                'received_invoice_amount': -paid_amt * exchange_rate,
                'received_taxable_invoice_amount': -received_taxable_inv_amount * exchange_rate,
                'received_taxable_invoice_amount_6_percent': -received_taxable_inv_amount_6_percent * exchange_rate,
                'received_taxable_invoice_amount_8_percent': -received_taxable_inv_amount_8_percent * exchange_rate,
                'received_taxable_amount': -received_taxable_amount * exchange_rate,
                'received_taxable_amount_6_percent': -received_taxable_amount_6_percent * exchange_rate,
                'received_taxable_amount_8_percent': -received_taxable_amount_8_percent * exchange_rate,
                'sst_6_percent': -tax_amount_6_percent * exchange_rate,
                'sst_8_percent': -tax_amount_8_percent * exchange_rate,
            }
        else:
            return_data = {
                **base_data,
                'invoice_amount': inv.amount_total * exchange_rate,
                'invoice_taxable_amount': taxable_amount + b2b_amt * exchange_rate,
                'taxable_amount_6_percent': taxable_amount_6_percent * exchange_rate,
                'taxable_amount_8_percent': taxable_amount_8_percent * exchange_rate,
                'sst_amount': inv.amount_tax + b2b_amt * exchange_rate,
                'received_invoice_amount': paid_amt * exchange_rate,
                'received_taxable_invoice_amount': received_taxable_inv_amount * exchange_rate,
                'received_taxable_invoice_amount_6_percent': received_taxable_inv_amount_6_percent * exchange_rate,
                'received_taxable_invoice_amount_8_percent': received_taxable_inv_amount_8_percent * exchange_rate,
                'received_taxable_amount': received_taxable_amount * exchange_rate,
                'received_taxable_amount_6_percent': received_taxable_amount_6_percent * exchange_rate,
                'received_taxable_amount_8_percent': received_taxable_amount_8_percent * exchange_rate,
                'sst_6_percent': tax_amount_6_percent * exchange_rate,
                'sst_8_percent': tax_amount_8_percent * exchange_rate,
            }
        return return_data

    def _inject_all_sst_values(self):
        b2b_exempt_tax = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 0),
             ('active', '=', True)], limit=1)
        b2b_exempt_tax_id = b2b_exempt_tax.id if b2b_exempt_tax else False
        b2b_exempt_tax_name = b2b_exempt_tax.name if b2b_exempt_tax else ''
        if b2b_exempt_tax_name and '%' == b2b_exempt_tax_name[-1]:
            b2b_exempt_tax_name = b2b_exempt_tax_name + '%'
        sst_6_percent_search = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 6),
             ('active', '=', True)], limit=1)
        sst_6_percent_id = sst_6_percent_search.id if sst_6_percent_search else False
        sst_6_percent_name = sst_6_percent_search.name if sst_6_percent_search else ''
        if sst_6_percent_name and '%' == sst_6_percent_name[-1]:
            sst_6_percent_name = sst_6_percent_name + '%'
        sst_8_percent_search = self.env['account.tax'].search(
            [('company_id', '=', self.env.user.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 8),
             ('active', '=', True)], limit=1)
        sst_8_percent_id = sst_8_percent_search.id if sst_8_percent_search else False
        sst_8_percent_name = sst_8_percent_search.name if sst_8_percent_search else ''
        if sst_8_percent_name and '%' == sst_8_percent_name[-1]:
            sst_8_percent_name = sst_8_percent_name + '%'
        context = self._context
        b2b_additional_select = f""",
            (
                SELECT SUM(base)
                FROM account_invoice_tax ait_sub
                WHERE ait_sub.invoice_id = ai.id
                AND (ait_sub.tax_id = {b2b_exempt_tax_id})
            ) AS taxable_b2b_amt,
            (
                CASE
                    WHEN (
                        SELECT SUM(base)
                        FROM account_invoice_tax ait_sub
                        WHERE ait_sub.invoice_id = ai.id
                        AND (ait_sub.tax_id = {b2b_exempt_tax_id})
                    ) > 0 THEN 0.06 * (
                        SELECT SUM(base)
                        FROM account_invoice_tax ait_sub
                        WHERE ait_sub.invoice_id = ai.id
                        AND (ait_sub.tax_id = {b2b_exempt_tax_id})
                    )
                    ELSE 0
                END
            ) AS b2b_exemption_amt"""
        max_date_cte_query = """WITH move_lines AS (
                                    SELECT id, invoice_id
                                    FROM account_move_line
                                ),
                                max_date_cte AS (
                                    SELECT
                                        ml.invoice_id,
                                        MAX(apr.max_date) AS max_date
                                    FROM
                                        account_partial_reconcile apr
                                    JOIN
                                        move_lines ml ON apr.credit_move_id = ml.id OR apr.debit_move_id = ml.id
                                    GROUP BY
                                        ml.invoice_id
                                )"""
        exemption_condition = f"OR (ait.tax_id = {b2b_exempt_tax_id})" if self.is_b2b_exemption else ""
        sst_6_percent_condition = f"(ait.tax_id = {sst_6_percent_id})" if sst_6_percent_id else ""
        sst_8_percent_condition = f"OR (ait.tax_id = {sst_8_percent_id})" if sst_8_percent_id else ""
        if context and context.get('get_paid_invoices', False):
            query_inject_unpaid_sst_values = max_date_cte_query + f"""
                SELECT
                    ai.id AS invoice_id,
                    ai.type AS invoice_type,
                    ai.partner_id AS customer,
                    ai.number AS invoice_no,
                    ai.date_invoice AS invoice_date,
                    md.max_date AS invoice_paid_date,
                    ai.account_id AS invoice_account,
                    {(self.is_b2b_exemption and 'ai.amount_total') or 'SUM(aml.credit)'} AS invoice_amount,
                    rc.name as currency,
                    SUM(
                        CASE
                            WHEN aml.name LIKE '{sst_6_percent_name}'
                            THEN aml.tax_base_amount
                            ELSE 0
                        END
                    ) AS taxable_amount_6_percent,
                    SUM(
                        CASE
                            WHEN aml.name LIKE '{sst_6_percent_name}' THEN 
                                CASE
                                    WHEN ai.type = 'out_invoice' THEN aml.credit
                                    WHEN ai.type = 'out_refund' THEN aml.debit
                                    ELSE 0
                                END
                            ELSE 0
                        END
                    ) AS sst_6_percent,
                    SUM(
                        CASE
                            WHEN aml.name LIKE '{sst_8_percent_name}'
                            THEN aml.tax_base_amount
                            ELSE 0
                        END
                    ) AS taxable_amount_8_percent,
                    SUM(
                        CASE
                            WHEN aml.name LIKE '{sst_8_percent_name}' THEN
                                CASE
                                    WHEN ai.type = 'out_invoice' THEN aml.credit
                                    WHEN ai.type = 'out_refund' THEN aml.debit
                                END
                            ELSE 0
                        END
                    ) AS sst_8_percent {(self.is_b2b_exemption and b2b_additional_select) or ''}
                FROM
                    account_invoice ai
                    LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id
                    LEFT JOIN account_invoice_tax ait ON ait.invoice_id = ai.id
                    LEFT JOIN res_currency rc ON ai.currency_id = rc.id
                    LEFT JOIN max_date_cte md ON ai.id = md.invoice_id
                    WHERE
                    ai.company_id = %s AND
                    ai.type IN ('out_invoice', 'out_refund')
                    AND ai.state IN ('paid')
                    AND ({sst_6_percent_condition} {sst_8_percent_condition} {exemption_condition})
                GROUP BY
                ai.id, ai.type, ai.partner_id, ai.number, ai.date_invoice, rc.name, md.max_date
                ORDER BY
                    ai.date_invoice ASC;
            """
            query = query_inject_unpaid_sst_values
            self.env.cr.execute(query, (self.company_id.id,))
        else:
            query_inject_unpaid_sst_values = max_date_cte_query + f"""
                            SELECT
                                ai.id AS invoice_id,
                                ai.type AS invoice_type,
                                ai.partner_id AS customer,
                                ai.number AS invoice_no,
                                ai.date_invoice AS invoice_date,
                                md.max_date AS invoice_paid_date,
                                ai.account_id AS invoice_account,
                                {(self.is_b2b_exemption and 'ai.amount_total') or 'SUM(aml.credit)'} AS invoice_amount,
                                rc.name as currency,
                                SUM(
                                    CASE
                                        WHEN aml.name LIKE '{sst_6_percent_name}'
                                        THEN aml.tax_base_amount
                                        ELSE 0
                                    END
                                ) AS taxable_amount_6_percent,
                                SUM(
                                    CASE
                                        WHEN aml.name LIKE '{sst_6_percent_name}' THEN 
                                            CASE
                                                WHEN ai.type = 'out_invoice' THEN aml.credit
                                                WHEN ai.type = 'out_refund' THEN aml.debit
                                                ELSE 0
                                            END
                                        ELSE 0
                                    END
                                ) AS sst_6_percent,
                                SUM(
                                    CASE
                                        WHEN aml.name LIKE '{sst_8_percent_name}'
                                        THEN aml.tax_base_amount
                                        ELSE 0
                                    END
                                ) AS taxable_amount_8_percent,
                                SUM(
                                    CASE
                                        WHEN aml.name LIKE '{sst_8_percent_name}' THEN
                                            CASE
                                                WHEN ai.type = 'out_invoice' THEN aml.credit
                                                WHEN ai.type = 'out_refund' THEN aml.debit
                                            END
                                        ELSE 0
                                    END
                                ) AS sst_8_percent {(self.is_b2b_exemption and b2b_additional_select) or ''}
                            FROM
                                account_invoice ai
                                LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id
                                LEFT JOIN account_invoice_tax ait ON ait.invoice_id = ai.id
                                LEFT JOIN res_currency rc ON ai.currency_id = rc.id
                                LEFT JOIN max_date_cte md ON ai.id = md.invoice_id
                                WHERE
                                ai.company_id = %s AND 
                                ai.date_invoice >= %s AND
                                ai.date_invoice <= %s AND
                                ai.type IN ('out_invoice', 'out_refund')
                                AND ai.state IN ('open', 'paid')
                                AND ({sst_6_percent_condition} {sst_8_percent_condition} {exemption_condition})
                            GROUP BY
                            ai.id, ai.type, ai.partner_id, ai.number, ai.date_invoice, rc.name, md.max_date
                            ORDER BY
                                ai.date_invoice ASC;
                        """
            query = query_inject_unpaid_sst_values
            self.env.cr.execute(query, (self.company_id.id, self.date_from, self.date_to))

        sst_values = self.env.cr.dictfetchall()
        for val in sst_values:
            if val.get('currency', False) != self.env.user.company_id.currency_id.name:
                inv = self.env['account.invoice'].browse(val['invoice_id'])
                if val.get('taxable_b2b_amt', False):
                    val['taxable_b2b_amt'] = val['taxable_b2b_amt'] * inv.exchange_rate_inverse
                if val.get('b2b_exemption_amt', False):
                    val['b2b_exemption_amt'] = val['b2b_exemption_amt'] * inv.exchange_rate_inverse
                if val.get('invoice_amount', False):
                    val['invoice_amount'] = val['invoice_amount'] * inv.exchange_rate_inverse

            # if val.get('customer',False):
            #     partner = self.env['res.partner'].browse(val.get('customer'))
            #     fiscal_position = partner.property_account_position_id.id
            #     if fiscal_position and (val.get('sst_6_percent', 0) or val.get('sst_8_percent', 0) != 0):
            #         val['b2b_exemption_amt'] = val['b2b_exemption_amt'] + val['sst_6_percent'] + val['sst_8_percent']
            #         val['sst_6_percent'] = 0
            #         val['sst_8_percent'] = 0

            if val.get('taxable_amount_6_percent', 0) == 0 and val.get('taxable_b2b_amt', 0) != 0:
                val['taxable_amount_6_percent'] = val['taxable_b2b_amt']
            if val.get('invoice_type') and val.get('invoice_type') in ['in_refund', 'out_refund']:
                val['invoice_amount'] = -val['invoice_amount']
                val['sst_6_percent'] = -val['sst_6_percent']
                val['taxable_amount_6_percent'] = -val['taxable_amount_6_percent']
                val['sst_8_percent'] = -val['sst_8_percent']
                val['taxable_amount_8_percent'] = -val['taxable_amount_8_percent']
                if val.get('b2b_exemption_amt', False):
                    val['b2b_exemption_amt'] = -val['b2b_exemption_amt']

        if context and context.get('get_paid_invoices', False):
            return sst_values

        sst_results = sst_values
        if sst_results:
            ReportLine = self.env['report_sst_report_taxdetails']
            self.taxdetails_ids = [ReportLine.new(line).id for line in sst_results]