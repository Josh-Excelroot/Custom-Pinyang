from odoo import api, models, fields, _
import ast
from lxml import etree


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        # TDE FIXME: clean that brol
        defaults = self.default_get(['name', 'picking_type_id'])
        origin = vals.get('origin')
        if origin:
            sale_id = self.env['sale.order'].search([('name', '=', origin)], limit=1)
            if sale_id and sale_id.order_type == 'cash_order' and sale_id.make_auto_delivery:
                vals['name'] = self.env['ir.sequence'].next_by_code('cash.sale.delivery') or '/'
            if sale_id and sale_id.order_type == 'cash_order' and not sale_id.make_auto_delivery:
                vals['cash_address'] = sale_id.cash_address
                vals['cash_contact_name'] = sale_id.cash_contact_name
                vals['cash_sale'] = True
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                          defaults.get(
                                                                                                  'picking_type_id')):
            vals['name'] = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()
        res = super(Picking, self).create(vals)
        res._autoconfirm_picking()
        return res

    cash_address = fields.Text(string="Delivery Address")
    cash_contact_name = fields.Char(string="Contact Name")
    cash_sale = fields.Boolean(string="Is cash Sale Order?", default=False)

    # kashif 12july23 : hide cancel button for non accounting users
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Picking, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            user = self.env.user
            user_is_billing_manager = user.has_group('account.group_account_manager')
            user_is_billing_user = user.has_group('account.group_account_invoice')
            if (not user_is_billing_manager) and (not user_is_billing_user):
                doc = etree.XML(res['arch'])
                for button in doc.xpath("//button[@name='cancel_stock_picking']"):
                    modifiers_dict = ast.literal_eval(
                        button.get('modifiers').replace('true', 'True').replace('false', 'False'))
                    modifiers_dict['invisible'] = True
                    # replace Title Case to lower case to make it readable for JS
                    modifiers_str = str(modifiers_dict).replace("'", '"').replace('True', 'true').replace('False',
                                                                                                          'false')
                    button.set('modifiers', modifiers_str)
                res['arch'] = etree.tostring(doc)
        return res

# end
