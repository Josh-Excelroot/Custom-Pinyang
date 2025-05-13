from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
import re

class CopyBookingWizard(models.TransientModel):
    _name = 'copy.booking.wizard'

    carrier_booking_no = fields.Char(string='Carrier Booking No', help='Enter Carrier Booking No to Copy From')
    job_no = fields.Char(string='Job No', help='Enter Job No to Copy From')
    copy_booking_line_ids = fields.One2many('copy.booking.wizard.line', 'copy_booking_line_id',string="Copy From Job")

    @api.multi
    def action_copy_to_job(self):
        for operation in self:
            copy_to = self.env['freight.booking'].browse(self.env.context.get('booking_id'))
            for booking_line in operation.copy_booking_line_ids:
                if booking_line.job_to_copy:
                    booking = booking_line.job_to_copy
                    copy_to.service_type = booking.service_type
                    copy_to.direction = booking.direction
                    copy_to.cargo_type = booking.cargo_type
                    copy_to.shipment_type = booking.shipment_type
                    copy_to.booking_type = booking.booking_type
                    copy_to.shipment_term = booking.shipment_term.id
                    copy_to.slot_type = booking.slot_type
                    copy_to.customer_name = booking.customer_name.id
                    copy_to.shipper = booking.shipper.id
                    copy_to.consignee = booking.consignee.id
                    copy_to.notify_party = booking.notify_party.id
                    copy_to.slot_owner = booking.slot_owner.id
                    copy_to.operator_code = booking.operator_code.id
                    copy_to.port_of_loading = booking.port_of_loading.id
                    copy_to.port_of_discharge = booking.port_of_discharge.id
                    copy_to.terminal = booking.terminal.id
                    copy_to.depot_name = booking.depot_name.id
                    copy_to.shipping_agent_code = booking.shipping_agent_code
                    copy_to.shipping_agent_smk_code = booking.shipping_agent_smk_code
                    #TODO - Insert Manifest and Cost&Profit and CMO
                    #fcl_line_obj = self.env['freight.operations.line']
                    for line in booking.operation_line_ids:
                        operation_line = {
                            'container_no': line.container_no or False,
                            'container_product_id': line.container_product_id.id or False,
                            'operation_id': booking.id or '',
                            'container_no': line.container_no or '',
                            'seal_no': line.seal_no or '',
                            'container_product_name': line.container_product_name or '',
                            'packages_no': line.packages_no or 0.0,
                            'packages_no_uom': line.packages_no_uom.id,
                            'exp_gross_weight': line.exp_gross_weight or 0.0,
                            'exp_net_weight': line.exp_net_weight or 0.0,
                            'exp_vol': line.exp_vol or 0.0,
                            'remark': line.remark or '',
                            'container_type': line.container_type or '',
                            'cargo_type': line.cargo_type or '',
                            'vgm': line.vgm or 0.0,
                        }
                        copy_to.operation_line_ids = [(0, 0, operation_line)]
                        #copy_to.write({'operation_line_ids': operation_line or False})

                    #cost_profit_obj = self.env['freight.cost_profit']
                    for line in booking.cost_profit_ids:
                        cost_profit_line = {
                            'product_id': line.product_id.id or False,
                            'product_name': line.product_name or False,
                            'booking_id': booking.id or '',
                            'profit_qty': line.profit_qty or 0,
                            'profit_currency': line.profit_currency.id,
                            'profit_currency_rate': line.profit_currency_rate or 1.0,
                            'list_price': line.list_price or 0.0,
                            'cost_price': line.cost_price or 0.0,
                            'cost_qty': line.cost_qty or 0,
                            'cost_currency': line.cost_currency.id or False,
                            'cost_currency_rate': line.cost_currency_rate or 1.0,
                        }
                        copy_to.cost_profit_ids = [(0, 0, cost_profit_line)]
                        #copy_to.write({'cost_profit_ids': cost_profit_line or False})




    @api.onchange('job_no')
    def _onchange_job_no(self):
        for operation in self:
            if operation.job_no:
                booking = self.env['freight.booking'].search([
                    ('booking_no', '=', operation.job_no)], limit=1)
                line_list = []
                if booking:
                    copy_booking_line = self.env['copy.booking.wizard.line']
                    vals = ({
                        'job_to_copy': booking.id,
                        'carrier_booking_no': booking.carrier_booking_no,
                        'vessel_name': booking.vessel_name.id,
                        'voyage_no': booking.voyage_no,
                        'booking_date': booking.booking_date_time,
                        'port_of_loading': booking.port_of_loading.id,
                        'port_of_discharge': booking.port_of_discharge.id,
                    })
                    copy_booking = copy_booking_line.create(vals)
                    line_list.append(copy_booking.id)
                    operation.copy_booking_line_ids = line_list


class CopyBookingWizardLine(models.TransientModel):

    _name = 'copy.booking.wizard.line'
    copy_booking_line_id = fields.Many2one('copy.booking.wizard', 'Copy Job')

    job_to_copy = fields.Many2one('freight.booking', string='Job to Copy')
    carrier_booking_no = fields.Char(string='Carrier Booking No')
    vessel_name = fields.Many2one("freight.vessels", string="Vessel Name", track_visibility="onchange")
    voyage_no = fields.Char(string="Voyage No", track_visibility="onchange")
    booking_date = fields.Date(string="ETA/ETD Date")
    port_of_loading = fields.Many2one("freight.ports", string="Port of Loading")
    port_of_discharge = fields.Many2one("freight.ports", string="Port of Discharge")

