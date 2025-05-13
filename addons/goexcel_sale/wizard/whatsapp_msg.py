# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class SendWAMessage_XXXXX(models.TransientModel):
    _name = 'whatsapp.msg'

class SendWAMessage(models.TransientModel):
    _inherit = 'whatsapp.msg'

    @api.model
    def default_get(self, fields):
        result = super(SendWAMessage, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        if not active_model or active_model == 'pos.order':
            return result
        res_id = self.env.context.get('active_id')
        rec = self.env[active_model].browse(res_id)
        msg = result.get('message', '')
        if active_model == 'sale.order':
            doc_name = 'quotation' if rec.state in ('draft', 'sent') else 'order'
            msg = "Dear *" + rec.partner_id.name + "*"
            if rec.partner_id.parent_id:
                msg += "(" + rec.partner_id.parent_id.name + ")"
            msg += "\n\nHere is"
            if self.env.context.get('proforma'):
                msg += "in attachment your pro-forma invoice"
            else:
                msg += " the " + doc_name + " *" + rec.name + "* "
            if rec.origin:
                msg += "(with reference: " + rec.origin + ")"
            msg += " amounting in *" + self.format_amount(rec.amount_total, rec.pricelist_id.currency_id) + "*"
            msg += " from " + rec.company_id.name + ".\n\n"
            msg += "Do not hesitate to contact us if you have any question.\n\n\n"
        result['message'] = msg
        return result

    def sale_order_send_msg(self, so):
        if so:
            doc_name = 'quotation' if so.state in ('draft', 'sent') else 'order'
            msg = "Dear " + so.partner_id.name
            if so.partner_id.parent_id:
                msg += "(" + so.partner_id.parent_id.name + ")"
            msg += "\n\nHere is"
            msg += " the " + doc_name + so.name
            if so.origin:
                msg += "(with reference: " + so.origin + ")"
            msg += " amounting in " + self.format_amount(so.amount_total, so.pricelist_id.currency_id)
            msg += " from " + so.company_id.name + ".\n\n"
            msg += "Do not hesitate to contact us if you have any question.\n\n\n"
            return msg





