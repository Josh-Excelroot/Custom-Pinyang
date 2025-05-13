from odoo import api, models, fields
from lxml import etree


class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_prospect = fields.Boolean(string='Is a Prospect', default=True)

    log_in_user = fields.Boolean(string="Logged User",compute='_get_log_user_id')

    @api.depends('user_id')
    def _get_log_user_id(self):
        for rec in self:
            if rec.user_id.id == self.env.user.id:
                rec.log_in_user = True
            else:
                rec.log_in_user = False




    @api.onchange("is_prospect")
    def onchange_is_prospect(self):
        if self.is_prospect:
            self.customer = False

    @api.onchange("customer")
    def onchange_is_customer(self):
        if self.customer:
            self.is_prospect = False

    # customer = fields.Boolean(string='Is a Customer', default=False,
    #                           help="Check this box if this contact is a customer. It can be selected in sales orders.")

