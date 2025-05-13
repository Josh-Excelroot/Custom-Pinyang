from odoo import fields, models, api
from odoo.exceptions import UserError


class FreightBookingInherit(models.Model):
    _inherit = 'freight.booking'

    # scac_type = fields.Selection([('scac', 'EGLV'), ('gcnl', 'GCNL')], string='SCAC',
    #                              track_visibility='onchange')
    # scac = fields.Char(string='SCAC', track_visibility='onchange')
    # truck_name = fields.Char(string='Truck name', track_visibility='onchange')

    c_place_of_issue = fields.Char(compute="_compute_place_of_issue")
    c_no_of_original_bl = fields.Selection([('0', '0'), ('1', '1'), ('3', '3')], string="No Of original B/L",
                                           track_visibility='onchange', compute='compute_no_of_original_bl')
    intended_ck2_cut_off = fields.Datetime(string='Intended CK2/CIPL Cut Off', track_visibility='onchange')

    def _compute_place_of_issue(self):
        for val in self:
            record = self.env['freight.bol'].search([('booking_ref', '=', val.id)])
            if record:
                val.c_place_of_issue = record[0].place_of_issue

    def compute_no_of_original_bl(self):
        for val in self:
            record = self.env['freight.bol'].search([('booking_ref', '=', val.id)])
            if record:
                val.c_no_of_original_bl = record[0].no_of_original_bl

    def get_booking_type(self):
        data = {
            "ocean":{"import":"SI","export":"SE"},
            "air":{"import":"AI","export":"AE"},
            "land":{"import":"RI","export":"RE"},

        }
        # "transhipment": {"import": "CT", "export": "CT"}
        direction = self.direction
        if  direction != 'transhipment':
           service_type = data.get(self.service_type)
        else:
            service_type = {"transhipment":"CT"}
        return service_type.get(direction)

    def set_booking_no(self, vals=False):
        # vals=True: Create
        # vals=False: Write
        number, number_suffix = '', ''
        get_sq_code = self.get_booking_type()
        if vals and self.booking_no:
            len_check = 7
            booking_no = self.booking_no
        else:
            len_check = 7
            booking_no = self.env['ir.sequence'].next_by_code('fb')
        number_suffix = booking_no[:len_check].split('-')[1]
        number = booking_no[len_check:].split('-')[1]
        booking_no = get_sq_code + number_suffix  +  number
        if self.booking_no != booking_no:
            self.booking_no = booking_no

    @api.model
    def create(self, vals):
        res = super(FreightBookingInherit, self).create(vals)
        res.set_booking_no(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(FreightBookingInherit, self).write(vals)
        if 'booking_no' not in vals:
            self.set_booking_no(vals)
        return res
