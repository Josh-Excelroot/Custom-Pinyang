# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'sale_user_only' in self._context:
            group_id = self.env.ref('sales_team.group_sale_salesman')
            sales_group_usr_lst = group_id.users
            args += [('id', 'in', sales_group_usr_lst.ids)]
            recs = self.search(args, limit=limit)
            return recs.name_get()
        return super(ResUsers, self).name_search(name, args=None, operator='ilike', limit=100)
