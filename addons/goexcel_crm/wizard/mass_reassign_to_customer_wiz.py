# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SalespersonReassignToCustWiz(models.TransientModel):
    _name = 'salesperson.reassign.cust.wiz'
    _description = "Reassign Sales person"

    type = fields.Selection([('customer', 'Reassign Cust.'), ('opportunity', 'Reassign. Opp.'),
                             ('prospect', 'Reassign Prosp.')], string="Type",
                            default="customer")
    based_on = fields.Selection([('city', 'City'), ('sales_person', 'Sales Person')], default="sales_person")
    opportunity_stage = fields.Many2one("crm.stage", string="Stage")
    city_name = fields.Char(string="City")
    reassign_user_id = fields.Many2one('res.users', 'Original Salesperson')
    replace_user_id = fields.Many2one('res.users', 'Replacement Salesperson')
    partner_list_ids = fields.One2many("saleperson.partners.list.wiz", 'wiz_id', string="Customer")
    opportunity_list_ids = fields.One2many("saleperson.opportunities.list.wiz", 'wiz_id', string="Opportunities")

    @api.onchange('based_on')
    def onchange_based_on(self):
        if self.based_on == 'sales_person':
            self.city_name = ''
        if self.based_on == 'city':
            self.reassign_user_id = False

    @api.onchange('city_name', 'reassign_user_id', 'opportunity_stage')
    def onchange_data(self):
        # print('>>>>>>>>>>>>>>onchange_data')
        partners = False
        opportunities = False
        if self.type == 'customer':
            self.partner_list_ids = False
            # TS- Bug 25/11/2022 Shipper and contact person has to be reassigned as well...
            domain = [('type', '!=', 'related_company'), ('customer', '=', True), ('is_company', '=', True),
                      ('company_id', '=', self.env.user.company_id.id)]
            # End - TS
            if self.based_on == 'sales_person' and self.reassign_user_id:
                domain.append(('user_id', '=', self.reassign_user_id.id))
                partners = self.env['res.partner'].search(domain)
                # print('>>>>>>>>>>>>>>onchange_data partners=', len(partners))
            if self.based_on == 'city' and self.city_name:
                partners = self.env['res.partner'].search(domain + [('city', 'like', self.city_name.upper())])
            if partners:
                lst = []
                for par in partners:
                    lst.append((0, 0, {'wiz_id': self.id, 'partner_id': par.id, 'user_id': par.user_id.id}))
                self.partner_list_ids = lst
        elif self.type == 'prospect':
            self.partner_list_ids = False
            # all_compnay_partner = self.env['res.company'].sudo().search([])
            # partner_ids = [con.partner_id.id for con in all_compnay_partner]
            # c_domain = [('id', 'not in', partner_ids)]
            # TS- bug 25/11/2022 Shipper aand contact person has to be reassigned as well...
            domain = [('type', '!=', 'related_company'), ('is_prospect', '=', True), ('is_company', '=', True),
                      ('company_id', '=', self.env.user.company_id.id)]
            # domain = [('company_id', '=', self.env.user.company_id.id)]
            if self.based_on == 'sales_person' and self.reassign_user_id:
                domain.append(('user_id', '=', self.reassign_user_id.id))
                partners = self.env['res.partner'].search(domain)
                # print('>>>>>>>>>>>>>>onchange_data partners=', len(partners))
            if self.based_on == 'city' and self.city_name:
                partners = self.env['res.partner'].search(domain + [('city', 'like', self.city_name.upper())])
            if partners:
                lst = []
                for par in partners:
                    lst.append((0, 0, {'wiz_id': self.id, 'partner_id': par.id, 'user_id': par.user_id.id}))
                self.partner_list_ids = lst
        elif self.type == 'opportunity':
            # print('>>>>>>>>>>>>> onchange_data 0')
            self.opportunity_list_ids = False
            domain = [('company_id', '=', self.env.user.company_id.id)]
            if self.based_on == 'sales_person' and self.reassign_user_id:
                domain.append(("user_id", '=', self.reassign_user_id.id))
                if self.opportunity_stage:
                    domain.append(("stage_id", '=', self.opportunity_stage.id))
                opportunities = self.env['crm.lead'].search(domain)
            elif self.based_on == 'city' and self.city_name:
                # print('>>>>>>>>>>>>> onchange_data 1 City')
                domain.append(('city', 'like', self.city_name.upper()))
                if self.opportunity_stage:
                    domain.append(("stage_id", '=', self.opportunity_stage.id))
                opportunities = self.env['crm.lead'].search(domain)
            if opportunities:
                lst = []
                for opp in opportunities:
                    lst.append((0, 0, {'wiz_id': self.id, 'opportunity_id': opp.id, 'user_id': opp.user_id.id}))
                self.opportunity_list_ids = lst

        elif self.type == 'address':
            self.partner_list_ids = False
            if self.based_on == 'sales_person' and self.reassign_user_id:
                domain = [('company_id', '=', self.env.user.company_id.id),
                          ('parent_id.user_id', '=', self.reassign_user_id.id)]
                # domain.append(('user_id', '=', self.reassign_user_id.id))
                partners = self.env['res.partner'].search(domain)
                # print('>>>>>>>>>>>>>>onchange_data partners=', len(partners))
            # if self.based_on == 'city' and self.city_name:
            #     partners = self.env['res.partner'].search(domain + [('city', 'like', self.city_name.upper())])
            if partners:
                lst = []
                for par in partners:
                    lst.append((0, 0, {'wiz_id': self.id, 'partner_id': par.id, 'user_id': par.user_id.id}))
                self.partner_list_ids = lst

    # Ahmad Zaman - 5 Oct 2023 - Mass Reassignment Fixes and Enhancements
    @api.multi
    def action_reassign(self):
        # print('>>>>>>>>>>>action_reassign')
        if self.type == 'customer' or self.type == 'prospect':
            for res in self:
                # partners = False
                for partner in res.partner_list_ids:
                    if partner.partner_select is True:
                        # partner.partner_id.write({'user_id': res.replace_user_id.id})
                        res.env.cr.execute("UPDATE res_partner "
                                           "SET user_id=%s "
                                           "WHERE id=%s",
                                           (res.replace_user_id.id, partner.partner_id.id))
                        child_partners = self.env['res.partner'].search([('parent_id', '=', partner.partner_id.id)])
                        for child in child_partners:
                            #     # if child.user_id:
                            #     child.write({'user_id': res.replace_user_id.id})
                            res.env.cr.execute("UPDATE res_partner "
                                               "SET user_id=%s "
                                               "WHERE id=%s",
                                               (res.replace_user_id.id, child.parent_id.id))
                # if res.based_on == 'sales_person':
                #     if res.reassign_user_id == res.replace_user_id and self.type == 'customer':
                #         raise UserError(_("Both Sales person can not be same!!!"))
                #     partners = self.env['res.partner'].search([('user_id', '=', res.reassign_user_id.id)])
                # if res.based_on == 'city' and res.city_name:
                #     partners = self.env['res.partner'].search([('city', '=', res.city_name)])
                # if partners:
                # partners.write({'user_id': res.replace_user_id.id})
        elif self.type == 'address':
            for res in self:
                # partners = False
                for partner in res.partner_list_ids:
                    if res.partner_list_ids.partner_select is True:
                        # partner.partner_id.write({'user_id': res.replace_user_id.id})
                        res.env.cr.execute("UPDATE res_partner "
                                           "SET user_id=%s "
                                           "WHERE id=%s",
                                           (res.replace_user_id.id, partner.partner_id.id))
        elif self.type == 'opportunity':
            # print('>>>>>>>>>>>action_reassign Opp')
            for res in self:
                # opportunities = False
                for opp in res.opportunity_list_ids:
                    if opp.opportunity_select is True:
                        # opp.opportunity_id.write({'user_id': res.replace_user_id.id})
                        res.env.cr.execute("UPDATE crm_lead "
                                           "SET user_id=%s "
                                           "WHERE id=%s",
                                           (res.replace_user_id.id, opp.opportunity_id.id))
                # if self.based_on == 'sales_person':
                #     if not res.replace_user_id:
                #         raise UserError(_("Please Select the Replacement Salesperson!!!"))
                #     # opportunities = self.env['crm.lead'].search([('user_id', '=', res.reassign_user_id.id),
                #     #                                              ("stage_id", "=", self.opportunity_stage.id)])
                #     #print('>>>>>>>>>>>action_reassign Opp len=',  str(len(opportunities)))
                #
                #
                #
                # elif self.based_on == 'city':
                #     domain = [('company_id', '=', self.env.user.company_id.id), ('city', 'like', self.city_name.upper())]
                #     if self.opportunity_stage:
                #         domain.append(("stage_id", '=', self.opportunity_stage.id))
                #     opportunities = self.env['crm.lead'].search(domain)
                # if opportunities:
                #     for opp in opportunities:
                #         opp.opportunity_id.write({'user_id': res.replace_user_id.id})


class PartnerList(models.TransientModel):
    _name = 'saleperson.partners.list.wiz'
    _description = "List of Partner change sales person"

    wiz_id = fields.Many2one('salesperson.reassign.cust.wiz', string="Wizard")
    partner_id = fields.Many2one("res.partner", string="Customer")
    user_id = fields.Many2one('res.users', string="Sales Person")
    city = fields.Char(related='partner_id.city', string="City")
    address = fields.Char(related="partner_id.street", string="Address")
    partner_select = fields.Boolean(string="Select ", default=False)


class OpportunityList(models.TransientModel):
    _name = 'saleperson.opportunities.list.wiz'
    _description = "List of Opportunity change for sales person"

    wiz_id = fields.Many2one('salesperson.reassign.cust.wiz', string="Wizard")
    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")
    user_id = fields.Many2one('res.users', string="Sales Person")
    stage_id = fields.Many2one(related='opportunity_id.stage_id', string="Stage")
    city = fields.Char(related='opportunity_id.partner_id.city', string="City")
    customer_id = fields.Many2one(related="opportunity_id.partner_id", string="Customer")
    # city = fields.Char(related='opportunity_id.partner_id.city',  string="city")
    # address = fields.Char(related="opportunity_id.partner_id.street", string="Address")
    opportunity_select = fields.Boolean(string="Select Opp", default=False)
