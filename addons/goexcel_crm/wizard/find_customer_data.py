# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class FindCustomerWizard(models.TransientModel):
    _name = 'find.customer.wiz'
    _description = "Find Other Sales person Customer"

    name = fields.Char(string="Name")
    company_registry = fields.Char(string="Company Registry")
    partner_list_ids = fields.One2many("find.customer.wiz.line", 'wiz_id', string="Customer")

    @api.onchange('name', 'company_registry')
    def onchange_data(self):
        partners = False
        self.partner_list_ids = False
        domain = []
        if self.name:
            domain.append(('name', 'like', self.name.upper()))
        if self.company_registry:
            domain.append(('company_registry', '=', self.company_registry))
        if domain:
            partners = self.env['res.partner'].sudo().search(domain + [('customer', '=', True)])
        if partners:
            lst = []
            for par in partners:
                data = {'wiz_id': self.id, 'partner_id': par.id, 'user_id': par.user_id.id}
                if par.user_id and par.user_id.sale_team_id:
                    data.update({'team_id': par.user_id.sale_team_id})
                lst.append((0, 0, data))
            self.partner_list_ids = lst

    @api.multi
    def action_ok(self):
        print ("pass")


class PartnerListLine(models.TransientModel):
    _name = 'find.customer.wiz.line'
    _description = "Find Other Sales person Customer Data"

    wiz_id = fields.Many2one('find.customer.wiz', string="Wizard")
    partner_id = fields.Many2one("res.partner", string="Customer")
    user_id = fields.Many2one('res.users', string="Sales Person")
    city = fields.Char(related='partner_id.city',  string="City")
    address = fields.Char(related="partner_id.street", string="Address")
    status = fields.Selection(related="partner_id.status", string="Status")
    team_id = fields.Many2one('crm.team', string="Team")
    team_leader_id = fields.Many2one(related="team_id.user_id", string="Team Leader")
    company_registry = fields.Char(related="partner_id.company_registry", string="Team Leader")
