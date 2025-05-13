# # -*- coding: utf-8 -*-
from . import models
from odoo.api import Environment, SUPERUSER_ID
def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    country = env['res.country'].sudo().search([('name', 'ilike', 'Malaysia')])
    # if country:
    #     states = env['res.country.state'].sudo().search([('country_id', '=', country.id)])
    #     for state in states:
    #         if state.name.lower() == 'Johor'.lower():
    #             state.code = '01'
    #         if state.name.lower() == 'Kedah'.lower():
    #             state.code = '02'
    #         if state.name.lower() == 'Kelantan'.lower():
    #             state.code = '03'
    #         if state.name.lower() == 'Melaka'.lower():
    #             state.code = '04'
    #         if state.name.lower() == 'Negeri Sembilan'.lower():
    #             state.code = '05'
    #         if state.name.lower() == 'Pahang'.lower():
    #             state.code = '06'
    #         if state.name.lower() == 'Pulau Pinang'.lower():
    #             state.code = '07'
    #         if state.name.lower() == 'Perak'.lower():
    #             state.code = '08'
    #         if state.name.lower() == 'Perlis'.lower():
    #             state.code = '09'
    #         if state.name.lower() == 'Selangor'.lower():
    #             state.code = '10'
    #         if state.name.lower() == 'Terengganu'.lower():
    #             state.code = '11'
    #         if state.name.lower() == 'Sabah'.lower():
    #             state.code = '12'
    #         if state.name.lower() == 'Sarawak'.lower():
    #             state.code = '13'
    #         if state.name.lower() == 'Kuala Lumpur'.lower():
    #             state.code = '14'
    #         if state.name.lower() == 'Labuan'.lower():
    #             state.code = '15'
    #         if state.name.lower() == 'Putrajaya'.lower():
    #             state.code = '16'
