# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class Inventory_picking(models.Model):
    _inherit = "stock.picking"

    def set_to_draft(self):
        self.write({'state': 'draft'})
        for move in self.move_ids_without_package:
            move.write({'state': 'draft'})
        return

    def action_cancel(self):
        for line in self:
            if line.state == 'done':
                line.cancel_stock_picking()
        res = super(Inventory_picking, self).action_cancel()
        return res

    def cancel_stock_picking(self):
        for move in self.move_ids_without_package:
            if move.product_id.type == 'product':
                lot_id = False
                for lot in move.move_line_ids:
                    lot_id = lot.lot_id

                if move.picking_id.picking_type_id.code == 'outgoing':

                    if move.product_id.tracking == 'none':

                        # quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)],limit=1)

                        # quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done)

                        vals = {
                            'product_id': move.product_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'product_uom': move.product_id.uom_id.id,
                            'picking_id': False,
                            'state': 'draft',
                            'date_expected': fields.Datetime.now(),
                            'location_id': move.location_dest_id.id,
                            'location_dest_id': move.location_id.id,
                            'picking_type_id': False,
                            'warehouse_id': self.picking_type_id.warehouse_id.id,
                            'origin_returned_move_id': False,
                            'procure_method': 'make_to_stock',
                            'reference': move.reference
                        }

                        in_move = move.copy(vals)

                        in_move.write({'reference': self.name})

                        in_move._action_confirm()
                        in_move._action_assign()
                        for j in in_move.move_line_ids:
                            j.unlink()

                        # kashif 16june23 : should not create move line whome qty done is 0
                        for i in move.move_line_ids.filtered(lambda r: r.qty_done > 0):
                            # i.write({'qty_done': move.product_uom_qty})
                            a = self.env['stock.move.line'].create({
                                'move_id': in_move.id,
                                'product_id': in_move.product_id.id,
                                'product_uom_id': in_move.product_uom.id,
                                'location_id': in_move.location_id.id,
                                'location_dest_id': in_move.location_dest_id.id,
                                'picking_id': False,
                                # 'lot_id':i.lot_id.id,
                                'qty_done': i.qty_done
                            })
                        # end kashif

                        in_move._action_done()

                    else:
                        # quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id),('lot_id','=',lot_id.id)],limit=1)
                        # quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done,lot_id)

                        vals = {
                            'product_id': move.product_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'product_uom': move.product_id.uom_id.id,
                            'picking_id': False,
                            'state': 'draft',
                            'date_expected': fields.Datetime.now(),
                            'location_id': move.location_dest_id.id,
                            'location_dest_id': move.location_id.id,
                            'picking_type_id': False,
                            'warehouse_id': self.picking_type_id.warehouse_id.id,
                            'origin_returned_move_id': False,
                            'procure_method': 'make_to_stock',
                            'reference': self.name
                        }

                        in_move = move.copy(vals)

                        in_move._action_confirm()
                        in_move._action_assign()
                        for j in in_move.move_line_ids:
                            j.unlink()

                        for i in move.move_line_ids:
                            # i.write({'qty_done': move.product_uom_qty})

                            a = self.env['stock.move.line'].create({
                                'move_id': in_move.id,
                                'product_id': in_move.product_id.id,
                                'product_uom_id': in_move.product_uom.id,
                                'location_id': in_move.location_id.id,
                                'location_dest_id': in_move.location_dest_id.id,
                                'picking_id': False,
                                'lot_id': i.lot_id.id,
                                'qty_done': i.qty_done
                            })

                        in_move._action_done()




                elif move.picking_id.picking_type_id.code == 'incoming':
                    if move.product_id.tracking == 'none':
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id)],
                            limit=1)
                        quant._update_available_quantity(move.product_id, move.location_dest_id, -move.quantity_done)
                    else:
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id),
                             ('lot_id', '=', lot_id.id)], limit=1)

                        quant._update_available_quantity(move.product_id, move.location_dest_id, -move.quantity_done,
                                                         lot_id)


                elif move.picking_id.picking_type_id.code == 'internal':
                    if move.product_id.tracking == 'none':
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_id.id)],
                            limit=1)
                        quant._update_available_quantity(move.product_id, move.location_id, move.quantity_done)

                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id)],
                            limit=1)
                        quant._update_available_quantity(move.product_id, move.location_dest_id, -move.quantity_done)
                    else:
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_id.id),
                             ('lot_id', '=', lot_id.id)], limit=1)
                        quant._update_available_quantity(move.product_id, move.location_id, move.quantity_done, lot_id)

                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id),
                             ('lot_id', '=', lot_id.id)], limit=1)

                        quant._update_available_quantity(move.product_id, move.location_dest_id, -move.quantity_done,
                                                         lot_id)

            move.sudo()._action_cancel()
            for j in move.move_line_ids:
                j.unlink()

            journal_rec = self.env['account.move'].sudo().search([('stock_move_id', '=', move.id)], order="id desc",
                                                                 limit=1)
            journal_rec.button_cancel()
            journal_rec.sudo().unlink()
            move.write({'state': 'draft'})
            move.move_line_ids.with_context(force=True).unlink()
            # move.sudo().unlink()

        self.write({'state': 'cancel'})
        return


class stock_move_line(models.Model):
    _inherit = "stock.move.line"

    def unlink(self):
        # custom code
        flag = True

        if not any(line.move_id.picking_id or line.move_id.inventory_id for line in self):
            flag = False

        if flag == False:

            for ml in self:
                if ml.state in ('done', 'cancel'):
                    raise UserError(
                        _('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
        # custom code

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ml in self:
            # if ml.state in ('done', 'cancel'):
            #    raise UserError(_('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
            # Unlinking a move line should unreserve.
            if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation() and not float_is_zero(
                    ml.product_qty, precision_digits=precision):
                try:
                    self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty,
                                                                      lot_id=ml.lot_id, package_id=ml.package_id,
                                                                      owner_id=ml.owner_id, strict=True)
                except UserError:
                    if ml.lot_id:
                        self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id,
                                                                          -ml.product_qty, lot_id=False,
                                                                          package_id=ml.package_id,
                                                                          owner_id=ml.owner_id, strict=True)
                    else:
                        raise
        moves = self.mapped('move_id')
        if flag == False:
            if moves:
                moves._recompute_state()
            res = super(stock_move_line, self).unlink()
            return res
        if moves:
            moves._recompute_state()

        if self._context.get('force') == True:
            res = super(stock_move_line, self).unlink()
            return res

        return


class stock_move_inherit(models.Model):
    _inherit = "stock.move"

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):

        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        ref = self.reference
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                  credit_account_id, debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            new_account_move.post()

    def _action_cancel(self):

        # custom code
        flag = True
        if not any(move.picking_id or move.inventory_id for move in self):
            flag = False

        if flag == False:

            if any(move.state == 'done' for move in self):
                raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
        # custom code

        for move in self:
            if move.state == 'cancel':
                continue
            move._do_unreserve()
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
    #kashif 1AUG2023: added code here to manage sale.purchase received qty when we cancel the GR/GS
            if move.purchase_line_id:
                move.purchase_line_id.write({
                    'qty_received': move.purchase_line_id.qty_received - move.quantity_done
                })
            elif move.sale_line_id:
                move.sale_line_id.write({
                    'qty_delivered': move.sale_line_id.qty_delivered - move.quantity_done
                })
    #end
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True

    def _do_unreserve(self):

        # custom code
        flag = True
        if not any(move.picking_id or move.inventory_id for move in self):
            flag = False

        if flag == False:

            if any(move.state == 'done' for move in self):
                raise UserError(_('You cannot unreserve a stock move that has been set to \'Done\'.'))
        # custom code

        moves_to_unreserve = self.env['stock.move']
        for move in self:
            if move.state == 'cancel':
                # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                continue
            if move.state == 'done':
                if move.scrapped:
                    # We may have done move in an open picking in a scrap scenario.
                    continue

            moves_to_unreserve |= move
        moves_to_unreserve.mapped('move_line_ids').unlink()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
