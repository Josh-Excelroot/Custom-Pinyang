from odoo import api, models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def _get_default_team(self):
        user_id = self.env.user.id,
        company_id = self.env.user.company_id.id,
        team_id = self.env['crm.team'].search([
            '|', ('user_id', '=', user_id), ('member_ids', '=', user_id),
            '|', ('company_id', '=', False), ('company_id', 'child_of', [company_id])], limit=1)
        return team_id

    team_id = fields.Many2one('crm.team', 'Sales Team', default=_get_default_team)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        sale_user = self.user_has_groups('sales_team.group_sale_salesman')
        sale_manager = self.user_has_groups('sales_team.group_sale_manager')
        if sale_manager:
            team_id = self.env['crm.team'].search([('user_id', '=', self.env.uid)], limit=1)
            if team_id and team_id.member_ids:
                team_member_ids = team_id.member_ids.ids
                if team_member_ids:
                    args += ['|', ('user_id', 'in', team_member_ids), ('user_id', '=', False)]
        elif sale_user and not sale_manager:
            args += [('user_id', '=', self.env.user.id)]
        return super(ResPartner, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        sale_user = self.user_has_groups('sales_team.group_sale_salesman')
        sale_manager = self.user_has_groups('sales_team.group_sale_manager')
        if sale_manager:
            team_id = self.env['crm.team'].search([('user_id', '=', self.env.uid)], limit=1)
            if team_id and team_id.member_ids:
                team_member_ids = team_id.member_ids.ids
                if team_member_ids:
                    args += ['|', ('user_id', 'in', team_member_ids), ('user_id', '=', False)]
        elif sale_user and not sale_manager:
            args += [('user_id', '=', self.env.user.id)]
        return super(ResPartner, self).name_search(name, args=args, operator='ilike', limit=100)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(ResPartner, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        quant = []
        for result in res:
            value = groupby and groupby[0] + '_count'
            if self.search_count(result['__domain']):
                result[value] = self.search_count(result['__domain'])
                quant.append(result)
            else:
                result[value] = 0
        return quant


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(ResUsers, self).create(vals)

    @api.multi
    def write(self, vals):
        self.clear_caches()
        return super(ResUsers, self).write(vals)
