from odoo import models, fields, api
from odoo import tools


# Ahmad Zaman - 28/2/25 - Pivot table for invoiced booking records
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def trigger_compute_amount(self):
        invoices = self.search([('company_id', '=', self.env.user.company_id.id),
                                ('type', 'in', ['out_refund', 'in_refund']),
                                ('currency_id', '!=', self.env.user.company_id.currency_id.id)])
        for inv in invoices:
            inv._compute_amount()

    invoiced_booking_cost = fields.Float(
        string="Booking Cost", digits=(16, 2)
    )

    invoiced_booking_sales = fields.Float(
        string="Booking Sales", digits=(16, 2)
    )

    invoiced_booking_profit = fields.Float(
        string="Booking Profit", digits=(16, 2)
    )

    invoiced_booking_date = fields.Date(string='Invoiced Booking Date')

    update_margins = fields.Boolean(string='Update Margins', default=False)

    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if any(field in vals for field in
               ['state', 'freight_booking', 'amount_total_company_signed', 'date_invoice', 'update_margins']):
            self.compute_previous_margins()
        return res

    def trigger_compute_previous_margins(self):
        invoices = self.search([('company_id', '=', self.env.user.company_id.id),
                                ('state', 'not in', ['draft', 'cancel']), ('freight_booking', '!=', False)])
        for inv in invoices:
            inv.write({'update_margins': True})

    def compute_previous_margins(self):
        invoices_to_update = self.filtered(lambda inv: inv.freight_booking)
        if invoices_to_update:
            for inv in invoices_to_update:
                if inv.update_margins:
                    inv.update_margins = False
                booking = inv.freight_booking
                invoices = inv.search(
                    [('company_id', '=', inv.env.user.company_id.id), ('state', 'not in', ['draft', 'cancel']),
                     ('freight_booking', '=', booking.id), ('type', 'in', ['out_invoice', 'out_refund'])]).sorted(
                    'date_invoice')

                vendor_bills = inv.search(
                    [('company_id', '=', inv.env.user.company_id.id), ('state', 'not in', ['draft', 'cancel']),
                     ('freight_booking', '=', booking.id), ('type', 'in', ['in_invoice', 'in_refund'])])

                first_invoice_date = invoices[0].date_invoice if invoices else False
                for rec in invoices + vendor_bills:
                    if not rec.invoiced_booking_date:
                        rec.invoiced_booking_date = first_invoice_date

                if inv.state in ['draft', 'cancel']:
                    inv.update({
                        'invoiced_booking_date': False,
                        'invoiced_booking_cost': 0.0,
                        'invoiced_booking_sales': 0.0,
                        'invoiced_booking_profit': 0.0,
                    })

                if invoices and invoices[0].id != inv.id and not self._context.get('balance_updated', False):
                    inv.update({
                        'invoiced_booking_cost': 0.0,
                        'invoiced_booking_sales': 0.0,
                        'invoiced_booking_profit': 0.0,
                    })
                    invoices[0].with_context(balance_updated=True).compute_previous_margins()

                elif invoices and invoices[0].id == inv.id:
                    previous_cost = sum(vb.amount_total_company_signed for vb in vendor_bills) if vendor_bills else 0.0
                    previous_sales = sum(rm_inv.amount_total_company_signed for rm_inv in invoices)

                    inv.update({
                        'invoiced_booking_cost': previous_cost,
                        'invoiced_booking_sales': previous_sales,
                        'invoiced_booking_profit': previous_sales - previous_cost,
                    })
                else:
                    inv.update({
                        'invoiced_booking_cost': 0.0,
                        'invoiced_booking_sales': 0.0,
                        'invoiced_booking_profit': 0.0,
                    })


class InvoiceBookingReport(models.Model):
    _name = 'invoice.booking.report'
    _description = 'Invoice and Invoice Line Booking Report'
    _auto = False
    _rec_name = 'invoice_id'

    # Invoice Fields
    id = fields.Integer(string="ID", readonly=True)
    invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    date_invoice = fields.Date(string='Invoice Date', readonly=True)
    freight_booking = fields.Many2one('freight.booking', string='Booking', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string='Invoice Status', readonly=True)
    amount_total = fields.Float(string='Total Amount', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    sales = fields.Float(string='Sales', readonly=True)
    cost = fields.Float(string='Cost', readonly=True)
    profit = fields.Float(string='Profit', readonly=True)
    invoiced_booking_date = fields.Date(string='Invoiced Booking Date', readonly=True)

    # Booking Fields
    direction = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Direction", readonly=True)
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air')], string="Shipment Mode", readonly=True)
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', readonly=True)
    shipment_booking_status = fields.Selection([('01', 'Booking Draft'),
                                                ('02', 'Booking Confirmed'),
                                                ('03', 'SI Received'),
                                                ('04', 'BL Confirmed'),
                                                ('05', 'OBL confirmed'),
                                                ('06', 'AWB Confirmed'),
                                                ('07', 'Shipment Arrived'), ('08', 'Done'), ('09', 'Cancelled'),
                                                ('10', 'Invoiced'), ('11', 'Paid')], string="Booking Status",
                                               readonly=True)
    booking_no = fields.Char(string='Booking No', readonly=True)
    booking_date_time = fields.Date(string='Booking Date', readonly=True)
    carrier_booking_no = fields.Char(string='Carrier Booking No', readonly=True)
    booking_type = fields.Selection([('master', 'Master'), ('sub', 'Sub')], string='Master or Sub', readonly=True)
    # Party
    customer_name = fields.Many2one('res.partner', string='Customer Name', readonly=True)
    contact_name = fields.Many2one('res.partner', string='Contact Name', readonly=True)
    payment_term = fields.Many2one('account.payment.term', string='Payment Term', readonly=True)
    incoterm = fields.Many2one('freight.incoterm', string='Incoterm', readonly=True)
    shipper = fields.Many2one('res.partner', string='Shipper', readonly=True)
    consignee = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight")
    commodity = fields.Many2one('product.product', readonly=True)
    commodity1 = fields.Many2one('freight.commodity1', string='Commodity', track_visibility='onchange')
    commodity_type = fields.Many2one('freight.commodity', string="Commodity Type", readonly=True)
    notify_party = fields.Many2one('res.partner', string='Notify Party', readonly=True)
    lcl_pcs = fields.Integer(string='LCL Pcs', readonly=True)
    lcl_weight = fields.Integer(string='LCL Weight', readonly=True)
    lcl_volume = fields.Integer(string='LCL Volume', readonly=True)
    # Shipment Info
    shipment_type = fields.Selection([('house', 'House'), ('direct', 'Direct')], string='Shipment Type', readonly=True)
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', readonly=True)
    place_of_receipt = fields.Char(string='Place of Receipt', readonly=True)
    place_of_receipt_ata = fields.Date(string='Receipt ATA', readonly=True)
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', readonly=True)
    port_of_loading_eta = fields.Date(string='Loading ETA', readonly=True)
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', readonly=True)
    port_of_discharge_eta = fields.Date(string='Discharge ETA', readonly=True)
    place_of_delivery = fields.Char(string='Place of Delivery', readonly=True)
    shipment_close_date_time = fields.Datetime(string='Closing Date Time', readonly=True)
    carrier = fields.Many2one('res.partner', string="Carrier", readonly=True)
    # Vessel Details
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', readonly=True)
    vessel_id = fields.Char(string='Vessel ID', readonly=True)
    terminal = fields.Char(string='Terminal', readonly=True)
    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], string='Freight Type',
                                    readonly=True)
    owner = fields.Many2one('res.users', string="Owner", readonly=True)
    sales_person = fields.Many2one('res.users', string="Salesperson", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            MIN(ai.id) as id,
            ai.id AS invoice_id,
            ai.partner_id,
            ai.invoiced_booking_date,
            ai.date_invoice,
            ai.freight_booking,
            ai.state,
            ai.amount_total,
            ai.currency_id,
            ai.company_id,
            ai.invoiced_booking_sales as sales,
            ai.invoiced_booking_cost as cost,
            ai.invoiced_booking_profit as profit,
            fb.direction,
            fb.service_type,
            fb.cargo_type,
            fb.shipment_booking_status,
            fb.booking_no,
            fb.booking_date_time,
            fb.carrier_booking_no,
            fb.booking_type,
            fb.customer_name,
            fb.contact_name,
            fb.payment_term,
            fb.incoterm,
            fb.shipper,
            fb.consignee,
            fb.commodity,
            fb.commodity1,
            fb.commodity_type,
            fb.notify_party,
            fb.lcl_pcs,
            fb.lcl_weight,
            fb.lcl_volume,
            fb.shipment_type,
            fb.priority,
            fb.place_of_receipt,
            fb.place_of_receipt_ata,
            fb.port_of_loading,
            fb.port_of_loading_eta,
            fb.port_of_discharge,
            fb.port_of_discharge_eta,
            fb.place_of_delivery,
            fb.shipment_close_date_time,
            fb.carrier,
            fb.vessel_name,
            fb.vessel_id,
            fb.terminal,
            fb.freight_type,
            fb.owner,
            fb.sales_person
        """

        for field in fields.values():
            select_ += field

        from_ = f"""
            account_invoice ai
            LEFT JOIN res_currency rc ON rc.id = ai.currency_id
            LEFT JOIN freight_booking fb ON fb.id = ai.freight_booking
            %s
        """ % from_clause

        groupby_ = f"""
            ai.id,
            ai.invoiced_booking_date,
            ai.partner_id,
            ai.date_invoice,
            ai.freight_booking,
            ai.state,
            ai.amount_total,
            ai.currency_id,
            ai.company_id,
            rc.name,
            fb.direction,
            fb.service_type,
            fb.cargo_type,
            fb.shipment_booking_status,
            fb.booking_no,
            fb.booking_date_time,
            fb.carrier_booking_no,
            fb.booking_type,
            fb.customer_name,
            fb.contact_name,
            fb.payment_term,
            fb.incoterm,
            fb.shipper,
            fb.consignee,
            fb.commodity,
            fb.commodity1,
            fb.commodity_type,
            fb.notify_party,
            fb.lcl_pcs,
            fb.lcl_weight,
            fb.lcl_volume,
            fb.shipment_type,
            fb.priority,
            fb.place_of_receipt,
            fb.place_of_receipt_ata,
            fb.port_of_loading,
            fb.port_of_loading_eta,
            fb.port_of_discharge,
            fb.port_of_discharge_eta,
            fb.place_of_delivery,
            fb.shipment_close_date_time,
            fb.carrier,
            fb.vessel_name,
            fb.vessel_id,
            fb.terminal,
            fb.freight_type,
            fb.owner,
            fb.sales_person,
            ai.invoiced_booking_sales,
            ai.invoiced_booking_cost,
            ai.invoiced_booking_profit %s
        """ % (groupby)

        company_id = self.env.user.company_id.id
        query = (
                "%s (SELECT %s FROM %s WHERE ai.freight_booking IS NOT NULL AND ai.company_id = %s AND ai.state NOT IN ('draft', 'cancel') AND fb.shipment_booking_status != '09' and ai.invoiced_booking_date IS NOT NULL GROUP BY %s)"
                % (with_, select_, from_, company_id, groupby_))
        return query

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(InvoiceBookingReport, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        filtered_res = []
        return_filtered_res = False
        for line in res:
            if line.get('invoice_id', False):
                invoice = self.env['account.invoice'].browse(line.get('invoice_id')[0])
                if invoice.type in ['out_invoice', 'out_refund']:
                    line['sales'] = invoice.amount_total_company_signed
                    line['cost'] = 0.00
                    line['profit'] = invoice.amount_total_company_signed
                    filtered_res.append(line)
                    return_filtered_res = True
        if return_filtered_res:
            return filtered_res
        return res
