from odoo import models, fields, api
from odoo.exceptions import Warning

class ContainerVolumeCharges(models.Model):
    _name = 'container.volume.charges'
    _description = 'Container Volume Charges'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.env['product.product'].search([('id', '=', self.product_id.id)])
        if product:
            self.name = product.name

    @api.onchange('uom')
    def _onchange_uom(self):
        uom = self.env['uom.uom'].search([('id', '=', self.uom.id)])
        if uom:
            self.name = uom.name

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.product', string='Product')
    uom = fields.Many2one('uom.uom', string="UoM")
    line_ids = fields.One2many('container.volume.charges.line', 'charges_id', string="Container Volume Charges Line",
                                      copy=True, auto_join=True, track_visibility='always')


class ContainerVolumeChargesLine(models.Model):
    _name = 'container.volume.charges.line'
    _description = 'Container Volume Charges Line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.env['product.product'].search([('id', '=', self.product_id.id)])
        if product:
            self.name = product.name

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.product', string='Product')
    charges_id = fields.Many2one('container.volume.charges', string='Container Volume Charges', required=True, ondelete='cascade',
                                     index=True, copy=False)