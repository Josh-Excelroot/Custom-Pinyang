from odoo import api, fields, models, exceptions,_
import logging
from datetime import date
from odoo.tools import float_round


class RFTInvoice2(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        res = super(RFTInvoice2, self).create(vals)
        if vals.get('type') == 'out_invoice' and vals.get('rft_id'):
            attached_files = self.env["ir.attachment"].search(
                    [("res_model", "=", "transport.rft"), ("res_id", "=", vals.get('rft_id'))]
                )
            if len(attached_files) > 0:
                for attachment in attached_files:
                    #attached_file = attachment.read()
                    self.env["ir.attachment"].sudo().create(
                        {
                            "name": attachment.name,
                            "res_model": "account.invoice",
                            "res_id": res.id,
                            "type": "binary",
                            "datas_fname": attachment.name,
                            "datas": attachment.datas,
                        }
                    )
        return res

