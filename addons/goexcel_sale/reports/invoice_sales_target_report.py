# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class AccountInvoiceReportSalesTarget(models.Model):
    _name = "invoice.line.report.sales.target"
    _description = "Invoice Analysis Report sales target"
    _auto = False
    _order = 'date desc'

    name = fields.Char(string="Inv. No", readonly=True)
    date = fields.Date(string='Invoice Date', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    vol = fields.Float(string="Volume", readonly=True)
    vol_sub_total = fields.Float(string="SubTotal Volume", readonly=True)
    uom_id = fields.Many2one('uom.uom', string='UOM', readonly=True)
    invoice_qty = fields.Float(string="Invoice Qty", readonly=True)
    price_unit = fields.Float(string="Unit Price", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    product_group_id = fields.Many2one('product.group', string="Prod.Group", readonly=True)
    product_grade_id = fields.Many2one('product.grade', string="Prod.Grade", readonly=True)
    product_brand_id = fields.Many2one('product.brand', string="Prod.Brand", readonly=True)
    type_of_product_id = fields.Many2one('type.of.product', string="Type of Prod.", readonly=True)
    product_category_id = fields.Many2one('product.category', string="Prod.Category", readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('approve', 'To Approve'), ('open', 'Open'), ('in_payment', 'In Payment'),
         ('paid', 'Paid'), ('cancel', 'Cancelled')], string="Status", readonly=True)
    user_id = fields.Many2one('res.users', string="SalesPerson", readonly=True)
    subtotal = fields.Float(string="SubTotal Price", readonly=True)
    sector_id = fields.Many2one('customer.sector', string="Sector", readonly=True)
    company_id = fields.Many2one("res.company", "Company")
    city = fields.Char(string="City", readonly=True)
    first_order = fields.Boolean(string="First Order", readonly=True)
    # kashif 2may23 - added new field
    target_sale = fields.Float(string="Target Sales")
    target_sale_percentage = fields.Float(string="Target Achievement %")

    # END
    #kashif 22may23 : update the subtotal calculation so it will consider exchange rate for diffrent currency

    def _select(self):
        select_str = """
            SELECT
                min(ail.id) as id,
                ai.number as name,
                ai.date_invoice as date,
                ai.partner_id as partner_id,
                ail.product_id as product_id,
                ail.price_unit as price_unit,
                ail.quantity as invoice_qty,
                ail.uom_id as uom_id,
                ai.state as state,
                ai.company_id as company_id,
                ai.first_order as first_order,
                t.categ_id as product_category_id,
                ai.user_id as user_id,
                partner.type_of_sector_id as sector_id,
                partner.city as city,
                t.product_group_id as product_group_id,
                t.product_grade_id as product_grade_id,
                t.product_brand_id as product_brand_id,
                t.type_of_product_id as type_of_product_id,               
                (vt.target)/(select count(acc_il.id) from account_invoice_line as acc_il where acc_il.invoice_id in (select acc.id from account_invoice as acc where vt.company_id =  acc.company_id and acc.user_id=ai.user_id and vt.sales_man=acc.user_id and acc.date_invoice >= vt.target_month_date and  acc.date_invoice <= vt.target_month_end_date and acc.state not in ('draft', 'cancel') and 
                 acc.type = 'out_invoice')) as target_sale,
                ail.inv_volume as vol,
                sum(ail.quantity*ail.inv_volume) as vol_sub_total,
                (( ((ail.price_subtotal))*100) /sum(vt.target))  as target_sale_percentage,
                sum(ail.price_subtotal * ai.exchange_rate_inverse) as subtotal

        """

        return select_str
#end
    def _from(self):
        from_str = """
            account_invoice_line ail
            join account_invoice ai on (ail.invoice_id=ai.id)
            join res_partner partner on ai.partner_id = partner.id
            left join product_product p on (ail.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom u on (u.id=ail.uom_id)
            left join uom_uom u2 on (u2.id=u.id)
             join visit_target vt on (vt.sales_man=ai.user_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
            ai.number,
            ai.date_invoice,
            ail.price_unit,
            ail.quantity,
            ail.partner_id,
            ail.uom_id,
            ail.product_id,
            ai.state,
            ai.company_id,
            ai.first_order,
            u2.factor,
            ai.user_id,
            t.categ_id,
            ai.partner_id,
            t.product_group_id,
            t.product_grade_id,
            t.product_brand_id,
            t.type_of_product_id,
            partner.type_of_sector_id,
            partner.city,
            ail.inv_volume,
             vt.target ,
             vt.sales_man,
             vt.target_month_date,
             vt.target_month_end_date,
             ail.price_subtotal,
             vt.company_id

        """
        return group_by_str

    def _where(self):
        return """
            and  ai.date_invoice >= vt.target_month_date and  ai.date_invoice <= vt.target_month_end_date and vt.company_id =  ai.company_id
        """

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s ) WHERE ai.state not in ('draft', 'cancel') and 
            ai.type = 'out_invoice'
            %s
            %s
            )""" % (self._table, self._select(), self._from(), self._where(), self._group_by()))
