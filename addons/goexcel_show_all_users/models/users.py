# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ServerActions(models.Model):
    _inherit = 'ir.actions.server'

    activity_user_type = fields.Selection([
        ('specific', 'Specific User'),
        ('generic', 'Generic User From Record')], default="specific",
        help="Use 'Specific User' to always assign the same user on the next activity. Use 'Generic User From Record' to specify the field name of the user to choose on the record.")

class users(models.Model):
    _inherit = "res.users"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user_rec = self.env.user
        erp_manager_id = self.env['ir.model.data'].get_object_reference('goexcel_show_all_users',
                                                                        'user_show_all_record_group')[1]
        if user_rec and erp_manager_id  in user_rec.groups_id.ids and not 'user_all' in self.env.context:
            args += [('company_ids','child_of',[user_rec.company_id.id])]
            res = super(users, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        else:
            res = super(users, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        return res

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     user_rec = self.env['res.users'].browse(self._uid)
    #     erp_manager_id = self.env['ir.model.data'].get_object_reference('base',
    #                                                                     'group_erp_manager')[1]
    #     if user_rec and erp_manager_id not in user_rec.groups_id.ids:
    #         # if user_rec.store_ids:
    #         #     args += ['|', ('store_id', 'in', user_rec.store_ids.ids), ('store_id', '=', False)]
    #         res = super(users, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
    #     else:
    #         res = super(users, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
    #     return res
    @api.model
    def open_user_window(self):
        action = self.env.ref('base.action_res_users').read()[0]
        action['domain'] = [('company_ids','child_of',[self.env.user.company_id.id])]
        action['context'] = dict(self.env.context, user_all=1)
        return action
