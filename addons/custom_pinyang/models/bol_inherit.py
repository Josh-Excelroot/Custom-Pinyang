from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BolInherit(models.Model):
    _inherit = "freight.bol"

    bol_sequence = fields.Integer("BOL Sequence", readonly=True, copy=False)

    @api.model
    def create(self, vals):
        res = super(BolInherit, self).create(vals)

        # Get the booking reference
        booking_ref = res.booking_ref
        if booking_ref:
            # Count existing BOLs for this booking and add 1 for the new one
            existing_bols = self.env['freight.bol'].search([
                ('booking_ref', '=', booking_ref.id),
                ('id', '!=', res.id)  # Exclude current BOL
            ])

            # Set the sequence number (count + 1)
            sequence_number = len(existing_bols) + 1
            res.bol_sequence = sequence_number

            # Format the BOL number based on booking number and sequence
            booking_no = booking_ref.booking_no
            if booking_no:
                # Format the sequence as 2 digits (01, 02, etc.)
                formatted_sequence = f"{sequence_number:02d}"

                # Create the BOL number with the format: BOOKING_NO-SEQUENCE
                bol_no = f"{booking_no}-{formatted_sequence}"

                # Update the BOL fields based on service type
                if res.service_type == 'ocean':
                    res.bol_no = bol_no
                    res.display_name = bol_no
                elif res.service_type == 'air':
                    res.awb_no = bol_no
                    res.bol_no = bol_no
                    res.display_name = bol_no
                elif res.service_type == 'land':
                    res.sn_no = bol_no
                    res.bol_no = bol_no
                    res.display_name = bol_no

        return res