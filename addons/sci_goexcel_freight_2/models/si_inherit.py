from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ShippingInstruction1(models.Model):
    _inherit = "freight.website.si"

    shipper_load = fields.Boolean('Shipper Load, Seal and Count')

    @api.onchange('fcl_line_ids')
    def _onchange_fcl_line_ids(self):
        container_product_name = False
        for fcl_line in self.fcl_line_ids:
            if fcl_line.container_product_name:
                container_product_name = fcl_line.container_product_name
            if not fcl_line.container_product_name:
                if container_product_name:
                    fcl_line.container_product_name = container_product_name

    @api.onchange('lcl_line_ids')
    def _onchange_lcl_line_ids(self):
        container_product_name = False
        for lcl_line in self.lcl_line_ids:
            if lcl_line.container_product_name:
                container_product_name = lcl_line.container_product_name
            if not lcl_line.container_product_name:
                if container_product_name:
                    lcl_line.container_product_name = container_product_name

    # @api.onchange('si_status')
    # def _onchange_si_status(self):
    #     if self.si_status == '03' and self.direction == 'export':
    #         if self.booking_ref:
    #             booking = self.env['freight.booking'].search([('id', '=', self.booking_ref.id), ])
    #             if self.cargo_type == 'fcl':
    #                 booking_val = {
    #                     'shipper_address_input': self.shipper,
    #                     'consignee_address_input': self.consignee,
    #                     'notify_party_address_input': self.notify_party,
    #                     'place_of_delivery': self.place_of_delivery,
    #                     'place_of_receipt': self.place_of_receipt,
    #                     'freight_type': self.freight_type,
    #                     'note': self.note,
    #                     'shipment_booking_status': '03',
    #                     'bol_status': self.bol_status,
    #                     'no_of_original_bl': self.no_of_original_bl,
    #                 }
    #                 booking.sudo().write(booking_val)
    #                 # remove all existing booking fcl lines
    #                 # for booking_line in booking.operation_line_ids:
    #                 #     booking_line.sudo().unlink()
    #                 container_line = self.fcl_line_ids
    #                 for line in container_line:
    #                     if line.container_product_name:
    #                         operation_line_obj = self.env['freight.operations.line']
    #                         op_line = operation_line_obj.create({
    #                             'operation_id': booking.id,
    #                             'container_product_id': line.container_product_id.id or False,
    #                             'container_commodity_id': line.container_commodity_id.id or False,
    #                             'container_product_name': line.container_product_name or '',
    #                             'fcl_container_qty': line.fcl_container_qty or 0,
    #                             'container_no': line.container_no or '',
    #                             'packages_no': line.packages_no or '',
    #                             'seal_no': line.seal_no or '',
    #                             'packages_no_uom': line.packages_no_uom.id,
    #                             'exp_vol': line.exp_vol or '',
    #                             'exp_gross_weight': line.exp_gross_weight or '',
    #                             'remark': line.remark or '',
    #                         })
    #                         booking.operation_line_ids = op_line
    #             else:
    #                 # for booking_line in booking.operation_line_ids2:
    #                 #     booking_line.sudo().unlink()
    #                 container_line = self.lcl_line_ids
    #                 for line in container_line:
    #                     if line.container_product_name:
    #                         operation_line_obj = self.env['freight.operations.line2']
    #                         op_line = operation_line_obj.create({
    #                             'operation_id2': booking.id,
    #                             'container_product_id': line.container_product_id.id or False,
    #                             'container_commodity_id': line.container_product_id.id or False,
    #                             'container_product_name': line.container_product_name or '',
    #                             'container_no': line.container_no or '',
    #                             'packages_no': line.packages_no or '',
    #                             'packages_no_uom': line.packages_no_uom.id,
    #                             'exp_vol': line.exp_vol or '',
    #                             'dim_length': line.dim_length or '',
    #                             'dim_width': line.dim_width or '',
    #                             'dim_height': line.dim_height or '',
    #                             'exp_net_weight': line.exp_net_weight or '',
    #                             'exp_gross_weight': line.exp_gross_weight or '',
    #                             'shipping_mark': line.shipping_mark or '',
    #                         })
    #                         booking.operation_line_ids2 = op_line

    @api.multi
    def action_update_job(self):
        #print('>>>>>>>>>>>>>>>action_update_job')
        for obj in self:

            if obj.booking_ref:
                booking = self.env['freight.booking'].search([('id', '=', self.booking_ref.id), ])
                if obj.cargo_type == 'fcl':
                    # remove all existing booking fcl lines
                    #print('>>>>>>>>>>>>>>>_onchange_si_status booking job no=', booking.booking_no)
                    #for booking_line in booking.operation_line_ids:
                    booking.operation_line_ids.unlink()
                    #container_line = self.fcl_line_ids
                    #print('>>>>>>>>>>>>>>>_onchange_si_status len container_lines=', len(container_line))
                    operation_line_obj = self.env['freight.operations.line']
                    for line in obj.fcl_line_ids:
                        if line.container_product_name:
                            op_line = operation_line_obj.create({
                                'operation_id': booking.id,
                                'container_product_id': line.container_product_id.id or False,
                                'container_commodity_id': line.container_commodity_id.id or False,
                                'container_product_name': line.container_product_name or '',
                                'fcl_container_qty': line.fcl_container_qty or 0,
                                'container_no': line.container_no or '',
                                'seal_no': line.seal_no or '',
                                'packages_no': line.packages_no or '',
                                'packages_no_uom': line.packages_no_uom.id,
                                'exp_vol': line.exp_vol or '',
                                'exp_gross_weight': line.exp_gross_weight or '',
                                'remark': line.remark or '',
                            })
                            #booking.operation_line_ids = op_line
                    obj.write({'si_status': '03'})
                else:
                    #for booking_line in booking.operation_line_ids2:
                    #    booking_line.sudo().unlink()
                    container_line = obj.lcl_line_ids
                    operation_line_obj = self.env['freight.operations.line2']
                    for line in container_line:
                        if line.container_product_name:

                            op_line = operation_line_obj.create({
                                'operation_id2': booking.id,
                                'container_product_id': line.container_product_id.id or False,
                                'container_commodity_id': line.container_product_id.id or False,
                                'container_product_name': line.container_product_name or '',
                                'container_no': line.container_no or '',
                                'packages_no': line.packages_no or '',
                                'packages_no_uom': line.packages_no_uom.id,
                                'exp_vol': line.exp_vol or '',
                                'dim_length': line.dim_length or '',
                                'dim_width': line.dim_width or '',
                                'dim_height': line.dim_height or '',
                                'exp_net_weight': line.exp_net_weight or '',
                                'exp_gross_weight': line.exp_gross_weight or '',
                                'shipping_mark': line.shipping_mark or '',
                            })
                            #booking.operation_line_ids2 = op_line
                    obj.write({'si_status': '03'})

            elif obj.bl_ref:
                bol = self.env['freight.bol'].search([('id', '=', self.bl_ref.id), ])
                # remove all existing booking fcl lines
                #print('>>>>>>>>>>>>>>>action_update_job BOL no=', bol.bol_no)
                #for booking_line in booking.operation_line_ids:
                bol.cargo_line_ids.unlink()
                #container_line = self.fcl_line_ids
                #print('>>>>>>>>>>>>>>>_onchange_si_status len container_lines=', len(container_line))
                operation_line_obj = self.env['freight.bol.cargo']
                for line in obj.fcl_line_ids:
                    #if line.container_product_name:
                    op_line = operation_line_obj.create({
                        'cargo_line': bol.id,
                        'container_product_id': line.container_product_id.id or False,
                        #'container_commodity_id': line.container_commodity_id.id or False,
                        'container_product_name': line.container_product_name or '',
                        #'fcl_container_qty': line.fcl_container_qty or 0,
                        'container_no': line.container_no or '',
                        'seal_no': line.seal_no or '',
                        'packages_no_value': line.packages_no or '',
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_vol': line.exp_vol or '',
                        'exp_gross_weight': line.exp_gross_weight or '',
                        'marks': line.remark or '',
                    })
                        #booking.operation_line_ids = op_line
                obj.write({'si_status': '03'})




    @api.multi
    def action_upload_shipping_instruction(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_freight_2.si_upload_wizard')
        return {
            'name': 'Import',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'si.upload.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(id=self.id),
        }



class ShippingInstructionWizard1(models.TransientModel):
    _inherit = 'shipping.instruction.wizard'

    report_type = fields.Selection([('2', 'Shipping Instruction to Carrier')], string="Report Type", default='2')


class FCLLine1(models.Model):
    _inherit = "freight.website.si.fcl"
    """
    @api.model
    def create(self, vals):
        si = False
        description = False
        if vals.get("fcl_line"):
            si = self.env['freight.website.si'].browse(vals.get("fcl_line"))
        for product in si.fcl_line_ids:
            if product.container_product_name:
                description = product.container_product_name
                break
        if description and not vals.get("container_product_name"):
            vals['container_product_name'] = description
        res = super(FCLLine1, self).create(vals)
        content = ""
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("fcl_container_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("fcl_container_qty")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 Pckg No: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 Pckg No UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight: " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 G. Weight " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        res.fcl_line.message_post(body=content)
        return res
    """

class LCLLine1(models.Model):
    _inherit = "freight.website.si.lcl"

    """
    @api.model
    def create(self, vals):
        si = False
        description = False
        if vals.get("lcl_line"):
            si = self.env['freight.website.si'].browse(vals.get("lcl_line"))
        for product in si.lcl_line_ids:
            if product.container_product_name:
                description = product.container_product_name
                break
        if description and not vals.get("container_product_name"):
            vals['container_product_name'] = description
        res = super(LCLLine1, self).create(vals)
        content = ""
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"

        if vals.get("packages_no"):
            content = content + "  \u2022 Pckg No: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 Pckg No UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight: " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 G. Weight " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        res.fcl_line.message_post(body=content)
        return res
    """