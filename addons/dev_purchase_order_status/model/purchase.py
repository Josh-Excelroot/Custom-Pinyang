# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://devintellecs.com>).
#
##############################################################################

from odoo import api, fields, models, _

class purchase_order(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _compute_invoiced(self):
        for purchase in self:
            if purchase.invoice_ids:
                a=0
                inv_len = len(purchase.invoice_ids)
                for invoice in purchase.invoice_ids:
                    if invoice.state == 'paid':
                        a += 1
                if inv_len == a:
                    purchase.invoice_status_new = True
                else:
                    count = 0
                    for invoice in purchase.invoice_ids:
                        if invoice.state == 'open' and invoice.residual < invoice.amount_total: 
                            purchase.invoice_partial = True
    @api.multi
    def _compute_invoiced_open(self):
        for purchase in self:
            purchase.invoice_open = False
            if purchase.invoice_ids:
                a=0
                inv_len = len(purchase.invoice_ids)
                for invoice in purchase.invoice_ids:
                    if invoice.state == 'open':
                        a += 1
                if inv_len == a:
                    purchase.invoice_open = True
#                    
#                
    @api.multi
    def _compute_shiped(self):
        for purchase in self:
            if purchase.picking_ids:
                a=0
                picking_len = len(purchase.picking_ids)
                for picking in purchase.picking_ids:
                    if picking.state == 'done':
                        a += 1
                if picking_len == a:
                    purchase.ship_status = True
                if a != 0 and not picking_len == a:
                    purchase.ship_partial = True

    
    invoice_open = fields.Boolean(string='Invoiced', compute='_compute_invoiced_open',search='_search_open_invoice')
    invoice_status_new = fields.Boolean(string='Paid', compute='_compute_invoiced', search='_search_full_paid_invoice')
    invoice_partial = fields.Boolean(string='Partial Paid', compute='_compute_invoiced', search='_search_partial_paid_invoice',copy=False)
    ship_status = fields.Boolean(string='Received',compute='_compute_shiped',copy=False, search='_search_full_shipment')
    ship_partial = fields.Boolean(string='Partial Received',compute='_compute_shiped',copy=False, search='_search_partial_shipment')
    
    
    
    def _search_full_shipment(self, operator, value):
        purchase_order = self.env['purchase.order'].search([])
        purchase_ids = []
        for purchase in purchase_order:
            if operator == '=':
                if purchase.picking_ids:
                    a=0
                    picking_len = len(purchase.picking_ids)
                    for picking in purchase.picking_ids:
                        if picking.state == 'done':
                            a += 1
                    if picking_len == a:
                        purchase_ids.append(purchase.id)
            else:
                if purchase.picking_ids:
                    a=0
                    picking_len = len(purchase.picking_ids)
                    for picking in purchase.picking_ids:
                        if picking.state != 'done':
                            a += 1
                    if picking_len == a:
                        purchase_ids.append(purchase.id)
                if not purchase.picking_ids:
                    purchase_ids.append(purchase.id)
        return [('id', 'in', purchase_ids)]
        
    def _search_partial_shipment(self, operator, value):
        purchase_order = self.env['purchase.order'].search([])
        purchase_ids = []
        for purchase in purchase_order:
            if operator == '=':
                if purchase.picking_ids:
                    a=0
                    picking_len = len(purchase.picking_ids)
                    for picking in purchase.picking_ids:
                        if picking.state == 'done':
                            a += 1
                    if a != 0 and picking_len != a:
                        purchase_ids.append(purchase.id)
            else:
                if purchase.picking_ids:
                    a=0
                    picking_len = len(purchase.picking_ids)
                    for picking in purchase.picking_ids:
                        if picking.state != 'done':
                            a += 1
                    if picking_len == a:
                        purchase_ids.append(purchase.id)
                if not purchase.picking_ids:
                    purchase_ids.append(purchase.id)
    
        return [('id', 'in', purchase_ids)]
#        
#        
#    
    def _search_partial_paid_invoice(self, operator, value):
        purchase_order = self.env['purchase.order'].search([])
        purchase_ids = []
        for purchase in purchase_order:
            if operator == '=':
                if purchase.invoice_ids:
                    a=0
                    inv_len = len(purchase.invoice_ids)
                    for invoice in purchase.invoice_ids:
                        if invoice.state == 'open' and invoice.residual < invoice.amount_total:
                            a += 1
                    if a != 0:
                        purchase_ids.append(purchase.id)
            else:
                if purchase.invoice_ids:
                    a=0
                    for invoice in purchase.invoice_ids:
                        if invoice.state != 'open':
                            purchase_ids.append(purchase.id)
                if not purchase.invoice_ids:
                    purchase_ids.append(purchase.id)
                
        return [('id', 'in', purchase_ids)]
#        
#        
    def _search_full_paid_invoice(self, operator, value):
        purchase_order = self.env['purchase.order'].search([])
        purchase_ids = []
        for purchase in purchase_order:
            if operator == '=':
                if purchase.invoice_ids:
                    a=0
                    inv_len = len(purchase.invoice_ids)
                    for invoice in purchase.invoice_ids:
                        if invoice.state == 'paid':
                            a += 1
                    if inv_len == a:
                        purchase_ids.append(purchase.id)
            else:
                if purchase.invoice_ids:
                    for invoice in purchase.invoice_ids:
                        if invoice.state != 'paid':
                            purchase_ids.append(purchase.id)
                if not purchase.invoice_ids:
                    purchase_ids.append(purchase.id)
        return [('id', 'in', purchase_ids)]
#        

    @api.depends('invoice_ids','state')
    def _search_open_invoice(self, operator, value):
        purchase_order = self.env['purchase.order'].search([])
        purchase_ids = []
        if operator == '=':
            for purchase in purchase_order:
                if purchase.invoice_ids:
                    a=0
                    inv_len = len(purchase.invoice_ids)
                    for invoice in purchase.invoice_ids:
                        if invoice.state == 'open':
                            a += 1
                    if inv_len == a:
                        purchase_ids.append(purchase.id)
        else:
            for purchase in purchase_order:
                if purchase.invoice_ids:
                    a=0
                    inv_len = len(purchase.invoice_ids)
                    for invoice in purchase.invoice_ids:
                        if invoice.state != 'open':
                            purchase_ids.append(purchase.id)
                if not purchase.invoice_ids:
                    purchase_ids.append(purchase.id)
        return [('id', 'in', purchase_ids)]
#    
#    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
