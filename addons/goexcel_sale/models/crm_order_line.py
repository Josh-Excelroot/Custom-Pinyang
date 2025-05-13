from odoo import api, models, fields, _
from odoo.exceptions import UserError


class Lead(models.Model):
    _inherit = "crm.lead"
    _order = 'crm_qty_total desc,crm_order_total desc'

    crm_line_ids = fields.One2many('crm.line', 'crm_lead_id', string="Crm Line", copy=False)
    is_first_order = fields.Boolean(string="First Order", readonly=True, copy=False)
    first_order_date = fields.Date(related="first_order_id.first_order_date", string="First Order Date", readonly=True, copy=False)
    first_order_id = fields.Many2one('sale.order', string="First Order#", copy=False)
    crm_order_total = fields.Float(string="Order TOtal", compute="get_full_total", store=True, copy=False)
    crm_qty_total = fields.Float(string="Order TOtal", compute="get_full_total", store=True, copy=False)
    is_prospect = fields.Boolean(string="Is Prospect", default=True)

    @api.multi
    def sale_action_quotations_new(self):
        if not self.partner_id:
            raise UserError(_("Please create Prospect or Select Customer"))
        order_line = []
        for res in self.crm_line_ids:
            data = {
                'product_id': res.product_id.id,
                'name': res.product_id.display_name,
                'product_uom_qty': res.product_uom_qty,
                'product_uom': res.product_uom.id,
                'price_unit': res.price,
            }
            order_line.append((0, 0, data))
        action = self.env.ref('sale_crm.sale_action_quotations_new').read()[0]
        action['views'] = [(False, 'form')]
        action['context'] = {
                'default_opportunity_id': self.id,
                'default_order_line': order_line,
                'default_partner_id': self.partner_id.id or False
            }
        return action

    @api.depends('crm_line_ids', 'crm_line_ids.sub_total')
    def get_full_total(self):
        for res in self:
            total = sum([amount.sub_total for amount in res.crm_line_ids])
            total_qty = sum([amount.product_uom_qty for amount in res.crm_line_ids])
            res.crm_qty_total = total_qty
            res.crm_order_total = total
            res.planned_revenue = total


class CrmLine(models.Model):
    _name = 'crm.line'
    _description = 'Crm Line Ids'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'price', 'currency_id')
    def get_sub_total(self):
        for res in self:
            res.sub_total = res.product_uom_qty * res.price

    crm_lead_id = fields.Many2one('crm.lead')
    categ_id = fields.Many2one('product.category', string="Product Catagory")
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price = fields.Monetary('Price')
    currency_id = fields.Many2one('res.currency')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sub_total = fields.Float(string="Sub Total", compute="get_sub_total")

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        result = {'domain': domain}
        vals['categ_id'] = self.product_id.categ_id.id
        vals['price'] = self.product_id.lst_price
        self.update(vals)

        return result
