from odoo import api, fields, models


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    branch = fields.Many2one("account.analytic.tag", string="Branch", copy='False')

    @api.model
    def create(self, vals):
        if not vals.get('branch'):
            vals["branch"] = self.env.user.default_branch.id
            branch = self.env.user.default_branch.id
        else:
            branch = vals.get('branch')
        # sequence = self.env["ir.sequence"].search(
        #     [("code", "=", "fb"), ("branch", "=", self.env.user.default_branch.id),],
        #     limit=1,
        # )
        # if not sequence:
        #     sequence = self.env["ir.sequence"].create(
        #         {"code": "fb", "branch": self.env.user.default_branch.id,}
        #     )
        service_type = vals.get("service_type")
        res = super(FreightBooking, self).create(vals)
        # print(sequence)
        # if service_type == "ocean" or service_type == "air" or service_type == "land":
        #     if sequence:
        #         res.booking_no = sequence._next()
        return res

    # @api.multi
    # def action_update_branch(self):
    #     bookings = self.env['freight.booking'].search([
    #         ('id', '!=', 0),
    #     ])
    #     for booking in bookings:
    #         booking.write({'branch': 4})


class FreightMasterBooking(models.Model):
    _inherit = "freight.master.booking.transport"

    branch = fields.Many2one("account.analytic.tag", string="Branch")

    @api.model
    def create(self, vals):
        #print('>>>>>>>>>>>> sci_goexcel_branch Vals=', vals)
        # 5/2/2023 - TS - user may not use the default branch
        branch = False
        if vals.get("branch"):
            branch = vals.get("branch")
        else:
            branch = self.env.user.default_branch.id
        #print('>>>>>>>>>>>> sci_goexcel_branch booking_inherit Branch=', branch)
        vals["branch"] = branch
        res = super(FreightMasterBooking, self).create(vals)

        return res

    # @api.multi
    # def action_update_branch(self):
    #     bookings = self.env['freight.master.booking.transport'].search([
    #         ('id', '!=', 0),
    #     ])
    #     for booking in bookings:
    #         booking.write({'branch': 4})