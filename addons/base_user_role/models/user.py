# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from datetime import date

class ResUsers(models.Model):
    _inherit = "res.users"

    role_line_ids = fields.One2many(
        comodel_name="res.users.role.line",
        inverse_name="user_id",
        string="Role lines",
        default=lambda self: self._default_role_lines(),
    )
    role_ids = fields.One2many(
        comodel_name="res.users.role",
        string="Roles",
        compute="_compute_role_ids",
    )

    @api.model
    def _default_role_lines(self):
        default_user = self.env.ref(
            'base.default_user', raise_if_not_found=False).sudo()
        default_values = []
        if default_user:
            for role_line in default_user.role_line_ids:
                default_values.append(
                    {
                        "role_id": role_line.role_id.id,
                        "date_from": role_line.date_from,
                        "date_to": role_line.date_to,
                        "is_enabled": role_line.is_enabled,
                    }
                )
        return default_values

    @api.multi
    @api.depends("role_line_ids.role_id")
    def _compute_role_ids(self):
        for user in self:
            user.role_ids = user.role_line_ids.mapped("role_id")

    @api.model
    def create(self, vals):
        new_record = super(ResUsers, self).create(vals)
        new_record.set_groups_from_roles()
        return new_record

    @api.multi
    def write(self, vals):
        new_all_companies = []
        all_existing_companies = []
        new_company_ids = []
        # Ahmad Zaman - 22/01/24 - Fixing Company Creation Error
        try:
            if vals['company_ids'][0][2]:
                all_existing_companies = self.company_ids.ids
                new_all_companies = vals['company_ids'][0][2]
                new_company_ids = set(new_all_companies) - set(all_existing_companies)
        except:
            if vals.get('company_ids'):
                all_existing_companies = self.company_ids.ids
                new_all_companies = vals['company_ids'][0]
                new_company_ids = set(new_all_companies) - set(all_existing_companies)
        # end
        res = super(ResUsers, self).write(vals)
        if vals.get('company_ids'):
            if new_company_ids and len(new_all_companies) > len(all_existing_companies):
                all_roles = self.env['res.users.role'].sudo().search([])
                # print(list(new_company_ids))
                company_ids_lst = list(new_company_ids)
                if company_ids_lst and all_roles:
                    for company_id in company_ids_lst:
                        for roles in all_roles:
                            self.env['res.users.role.line'].sudo().create({
                                'user_id': self.id,
                                'active_role': True,
                                'company_id': company_id,
                                'role_id': roles.id,
                            })
                            if self.role_line_ids:
                                roles_exist = self.env['res.users.role.line'].search([('user_id','=',self.id),
                                                                                      ('company_id','=',self.company_id.id),
                                                                                      ('role_id','=',roles.id)])
                                if not roles_exist:
                                    self.env['res.users.role.line'].sudo().create({
                                        'user_id': self.id,
                                        'active_role': True,
                                        'company_id': self.company_id.id,
                                        'role_id': roles.id,
                                    })
        self.sudo().set_groups_from_roles()
        return res

    def _get_applicable_roles(self):
        return self.role_line_ids.filtered(
            lambda rec: rec.is_enabled
            and (
                not rec.company_id or rec.company_id == rec.user_id.company_id
            )
        )

    @api.multi
    def set_groups_from_roles(self, force=False):
        """Set (replace) the groups following the roles defined on users.
        If no role is defined on the user, its groups are let untouched unless
        the `force` parameter is `True`.
        """
        role_groups = {}
        # We obtain all the groups associated to each role first, so that
        # it is faster to compare later with each user's groups.
        for role in self.mapped("role_line_ids.role_id"):
            role_groups[role] = list(
                set(
                    role.group_id.ids
                    + role.implied_ids.ids
                    + role.trans_implied_ids.ids
                )
            )
        for user in self:
            if not user.role_line_ids and not force:
                continue
            group_ids = []
            for role_line in user._get_applicable_roles():
                role = role_line.role_id
                if role:
                    group_ids += role_groups[role]
            group_ids = list(set(group_ids))  # Remove duplicates IDs
            groups_to_add = list(set(group_ids) - set(user.groups_id.ids))
            groups_to_remove = list(set(user.groups_id.ids) - set(group_ids))
            to_add = [(4, gr) for gr in groups_to_add]
            to_remove = [(3, gr) for gr in groups_to_remove]
            groups = to_remove + to_add
            if groups:
                vals = {
                    "groups_id": groups,
                }
                super(ResUsers, user).write(vals)
        return True
