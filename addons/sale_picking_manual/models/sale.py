# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _action_launch_stock_rule(self):
        create_delivery = self._context.get('create_delivery')
        if create_delivery:
            res = super(SaleOrderLine,self)._action_launch_stock_rule()
            return res
        else:
            return super(SaleOrderLine,self)._action_launch_stock_rule()
        #return True
    