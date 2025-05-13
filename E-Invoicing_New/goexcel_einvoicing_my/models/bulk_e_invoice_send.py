# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class BulkEInvoiceSend(models.TransientModel):

    _name = "bulk.einvoice.send"
    _description = "Send the selected invoices"

    @api.multi
    def einvoice_send(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        invoice_list = self.env['account.invoice'].browse(active_ids).sorted(lambda i: (i.date_invoice or fields.Date.context_today(self), i.reference or '', i.id))
        print(invoice_list)
        for record in invoice_list:
            if record.state == 'draft':
                raise UserError(_("Selected invoice(s) cannot be confirmed as they are in 'Draft' state."))

            if record.e_invoice_status and record.state == 'open':
                raise UserError(f'Invoice { record.number } had been submitted to E-Invoice. You cannot resend submitted e-invoice!')

            if not record.e_invoice_status and record.state == 'open':
                record.send_e_invoice()

        return {'type': 'ir.actions.act_window_close'}
