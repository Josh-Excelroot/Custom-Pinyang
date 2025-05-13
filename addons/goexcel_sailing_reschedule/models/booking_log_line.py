from odoo import fields, models, api


class FreightRescheduleBooking(models.Model):
    _inherit = "freight.booking"

    booking_log_lines_ids = fields.One2many('booking.log.line', 'booking_log_id', string="Reschedule",
            copy=True, auto_join=True, track_visibility='always')


class BookingLogLines(models.Model):
    _name = "booking.log.line"

    booking_log_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    update_date = fields.Datetime(string='Date', default=fields.Datetime.now)
    field_value = fields.Char(string='Description')
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    update_by = fields.Many2one('res.users', string='Update By', default=lambda self: self.env.user.id)


