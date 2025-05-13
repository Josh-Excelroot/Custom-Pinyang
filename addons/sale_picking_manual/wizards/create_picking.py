# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class create_picking(models.TransientModel):
    _name = 'sale.order.picking'

    orderline_ids = fields.Many2many(
        'sale.order.line',
    )

    def action_create_picking(self):
        if not self.orderline_ids:
            raise exceptions.UserError(
                _('Please Select at least One Order Line')
            )
        active_id = self._context.get('active_id')
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'create_delivery': True,
        })
        self.orderline_ids._action_launch_stock_rule()
        
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        order = self.env['sale.order'].search([('id','=',active_id)])
        pickings = order.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.model
    def default_get(self, fields_list):
        call_super = super(create_picking,self).default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id:
            order = self.env['sale.order'].browse(active_id)
            orderline = order.order_line.filtered(
                lambda line: line.product_id.type != 'service' and line.qty_delivered < line.product_uom_qty)
            call_super['orderline_ids'] = orderline.ids
        return call_super
