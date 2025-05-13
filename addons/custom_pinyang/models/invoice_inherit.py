from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class InvoiceInherit(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def write(self, vals):
        # Store old invoice numbers before the write operation
        old_numbers = {invoice.id: invoice.number for invoice in self}

        # Call the original write method
        res = super(InvoiceInherit, self).write(vals)

        # Check if 'number' field was changed
        if 'number' in vals:
            for invoice in self:
                old_number = old_numbers.get(invoice.id)
                new_number = invoice.number

                # Only proceed if the number actually changed
                if old_number and new_number and old_number != new_number:
                    # If this invoice is linked to a booking
                    if invoice.freight_booking:
                        booking = invoice.freight_booking

                        # Find the booking invoice line with the old number
                        old_line = self.env['booking.invoice.line'].search([
                            ('booking_id', '=', booking.id),
                            ('invoice_no', '=', old_number),
                            ('type', '=', invoice.type)
                        ], limit=1)

                        # If found, update it with the new number
                        if old_line:
                            old_line.write({
                                'invoice_no': new_number,
                                'reference': new_number if invoice.type in ['out_invoice',
                                                                            'out_refund'] else invoice.reference
                            })
                        else:
                            # If not found, trigger a full refresh of booking invoice lines
                            booking.action_reupdate_booking_invoice_one()

                    # For vendor bills that might be linked to multiple bookings through invoice lines
                    elif invoice.type in ['in_invoice', 'in_refund']:
                        # Get all bookings linked to this invoice through invoice lines
                        booking_ids = set()
                        for line in invoice.invoice_line_ids:
                            if line.freight_booking:
                                booking_ids.add(line.freight_booking.id)

                        # Update booking invoice lines for each booking
                        for booking_id in booking_ids:
                            booking = self.env['freight.booking'].browse(booking_id)

                            # Find the booking invoice line with the old number
                            old_line = self.env['booking.invoice.line'].search([
                                ('booking_id', '=', booking.id),
                                ('invoice_no', '=', old_number),
                                ('type', '=', invoice.type)
                            ], limit=1)

                            # If found, update it with the new number
                            if old_line:
                                old_line.write({
                                    'invoice_no': new_number,
                                    'reference': invoice.reference
                                })
                            else:
                                # If not found, trigger a full refresh of booking invoice lines
                                booking.action_reupdate_booking_invoice_one()

        return res

