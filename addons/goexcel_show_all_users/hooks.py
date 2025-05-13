# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def _post_init_hook(cr, registry):
    ''' Need to reenable the `product` pricelist multi-company rule that were
        disabled to be 'overriden' for multi-website purpose
    '''
    env = api.Environment(cr, SUPERUSER_ID, {})
    pl_rule = env.ref('base.res_users_rule', raise_if_not_found=False)
    pl_item_rule = env.ref('base.res_partner_rule', raise_if_not_found=False)
    menu = env.ref('base.menu_action_res_users', raise_if_not_found=False)


    multi_company_rules = pl_rule or env['ir.rule']
    multi_company_rules += pl_item_rule or env['ir.rule']
    multi_company_rules.write({'active': False})
    if menu:
        menu.unlink()


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    pl_rule = env.ref('base.res_users_rule', raise_if_not_found=False)
    pl_item_rule = env.ref('base.res_partner_rule', raise_if_not_found=False)
    multi_company_rules = pl_rule or env['ir.rule']
    multi_company_rules += pl_item_rule or env['ir.rule']
    multi_company_rules.write({'active': True})
