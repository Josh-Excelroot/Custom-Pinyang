from odoo import api, fields, models, exceptions
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class Booking(models.Model):
    _inherit = "freight.booking"

    # @api.onchange('sq_reference')
    # def onchange_sq_reference(self):
    #     if self.sq_reference:
    #         sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
    #         booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)])
    #
    #         self.billing_address = sq.partner_id.id or False,
    #         self.sales_person = sq.user_id.id,
    #         self.incoterm = sq.incoterm.id or False,
    #         self.port_of_loading = sq.POL.id or False,
    #         self.port_of_discharge = sq.POD.id or False,
    #         self.commodity = sq.commodity.id or False,
    #         self.payment_term = sq.payment_term_id.id or False,
    #         if sq.carrier_booking_no:
    #             self.carrier_booking_no = sq.carrier_booking_no
    #         self.contact_name = sq.contact_name.id or False,
    #         self.forwarding_agent_code = sq.forwarding_agent_code.id or False,
    #         self.hs_code = sq.hs_code.id or False,
    #         if sq.coo:
    #             self.coo = True
    #         else:
    #             self.coo = False
    #         if sq.fumigation:
    #             self.fumigation = True
    #         else:
    #             self.fumigation = False
    #         if sq.insurance:
    #             self.insurance = True
    #         else:
    #             self.insurance = False
    #         if sq.cpc:
    #             self.cpc = True
    #         else:
    #             self.cpc = False
    #         self.warehouse_hours = sq.warehouse_hours.id or False,
    #         self.airport_departure = sq.airport_departure.id or False,
    #         self.airport_destination = sq.airport_destination.id or False,
    #         self.transporter_company = sq.transporter_company.id or False,
    #         shipper_adr = ''
    #         consignee_adr = ''
    #         notify_party_adr = ''
    #         if sq.shipper:
    #             shipper_adr += sq.shipper.name + "\n"
    #             if sq.shipper.street:
    #                 shipper_adr += sq.shipper.street
    #             if sq.shipper.street2:
    #                 shipper_adr += ' ' + sq.shipper.street2
    #             if sq.shipper.zip:
    #                 shipper_adr += ' ' + sq.shipper.zip
    #             if sq.shipper.city:
    #                 shipper_adr += ' ' + sq.shipper.city
    #             if sq.shipper.state_id:
    #                 shipper_adr += ', ' + sq.shipper.state_id.name
    #             if sq.shipper.country_id:
    #                 shipper_adr += ', ' + sq.shipper.country_id.name + "\n"
    #             if not sq.shipper.country_id:
    #                 shipper_adr += "\n"
    #             if sq.shipper.phone:
    #                 shipper_adr += 'Phone: ' + sq.shipper.phone
    #             elif sq.shipper.mobile:
    #                 shipper_adr += '. Mobile: ' + sq.shipper.mobile
    #         if sq.consignee:
    #             consignee_adr += sq.consignee.name + "\n"
    #             if sq.consignee.street:
    #                 consignee_adr += sq.consignee.street
    #             if sq.consignee.street2:
    #                 consignee_adr += ' ' + sq.consignee.street2
    #             if sq.consignee.zip:
    #                 consignee_adr += ' ' + sq.consignee.zip
    #             if sq.consignee.city:
    #                 consignee_adr += ' ' + sq.consignee.city
    #             if sq.consignee.state_id:
    #                 consignee_adr += ', ' + sq.consignee.state_id.name
    #             if sq.consignee.country_id:
    #                 consignee_adr += ', ' + sq.consignee.country_id.name + "\n"
    #             if not sq.consignee.country_id:
    #                 consignee_adr += "\n"
    #             if sq.consignee.phone:
    #                 consignee_adr += 'Phone: ' + sq.consignee.phone
    #             elif sq.consignee.mobile:
    #                 consignee_adr += '. Mobile: ' + sq.consignee.mobile
    #         if sq.partner_id:
    #             notify_party_adr = sq.partner_id.name + "\n"
    #             if sq.partner_id.street:
    #                 notify_party_adr += sq.partner_id.street
    #             if sq.partner_id.street2:
    #                 notify_party_adr += ' ' + sq.partner_id.street2
    #             if sq.partner_id.zip:
    #                 notify_party_adr += ' ' + sq.partner_id.zip
    #             if sq.partner_id.city:
    #                 notify_party_adr += ' ' + sq.partner_id.city
    #             if sq.partner_id.state_id:
    #                 notify_party_adr += ', ' + sq.partner_id.state_id.name
    #             if sq.partner_id.country_id:
    #                 notify_party_adr += ', ' + sq.partner_id.country_id.name + "\n"
    #             if not sq.partner_id.country_id:
    #                 notify_party_adr += "\n"
    #             if sq.partner_id.phone:
    #                 notify_party_adr += 'Phone: ' + sq.partner_id.phone
    #             elif sq.partner_id.mobile:
    #                 notify_party_adr += '. Mobile: ' + sq.partner_id.mobile
    #         booking.write({'direction': sq.mode or False,
    #                        'customer_name': sq.partner_id.id or False,
    #                        'cargo_type': sq.type or False,
    #                        'service_type': sq.service_type,
    #                        'shipper': sq.shipper.id or False,
    #                        'consignee': sq.consignee.id or False,
    #                        'notify_party': sq.partner_id.id or False,
    #                        'notify_party_address_input': notify_party_adr,
    #                        'consignee_address_input': consignee_adr,
    #                        'shipper_address_input': shipper_adr,
    #                        })
    #         for line in booking.cost_profit_ids:
    #             line.unlink()
    #         cost_profit_obj = self.env['freight.cost_profit']
    #         ocean_freight_rate_product = self.env['product.product'].sudo().search(
    #             [(
    #                 'id', '=', self.env['ir.config_parameter'].sudo().get_param(
    #                     'sci_goexcel_ocean_freight_rate.product_ocean_freight_rate'))]
    #             , limit=1)
    #         current_date = datetime.today()
    #         for line in sq.order_line:
    #             if line.product_id:
    #                 if line.freight_foreign_price > 0.0:
    #                     price_unit = line.freight_foreign_price
    #                 elif line.product_id == ocean_freight_rate_product:
    #                     print(ocean_freight_rate_product)
    #                     price_unit = 0
    #                     ocean_freight_rate_ids = self.env['freight.ocean.freight.rate.line'].search(
    #                         [('valid_from', '<=', current_date), ('valid_to', '>=', current_date),
    #                          ('customer', '=', sq.partner_id.id)])
    #                     port_pair_ids = self.env['freight.port.pair'].search(
    #                         [('port_of_loading', '=', sq.POL.id),
    #                          ('port_of_discharge', '=', sq.POD.id)], limit=1)
    #                     if ocean_freight_rate_ids:
    #                         for i in ocean_freight_rate_ids:
    #                             if port_pair_ids in i.ocean_freight_rate_id.port_pair:
    #                                 if sq.carrier == i.ocean_freight_rate_id.carrier:
    #                                     if sq.container_product_id == i.ocean_freight_rate_id.container_product_id:
    #                                         if i.ocean_freight_rate_id.state == 'active':
    #                                             price_unit = line.price_unit
    #                 else:
    #                     price_unit = line.price_unit
    #                 print(price_unit)
    #                 cost_profit_line = cost_profit_obj.create({
    #                     'product_id': line.product_id.id or False,
    #                     'product_name': line.name or False,
    #                     'booking_id': booking.id or '',
    #                     'profit_qty': line.product_uom_qty or 0,
    #                     'profit_currency': line.freight_currency.id,
    #                     'profit_currency_rate': line.freight_currency_rate or 1.0,
    #                     'list_price': price_unit or 0.0,
    #                 })
    #                 booking.write({'cost_profit_ids': cost_profit_line or False})