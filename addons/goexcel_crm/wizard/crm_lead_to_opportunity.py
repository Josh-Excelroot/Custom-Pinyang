# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Lead2OpportunityMassConvert(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner.mass'

    @api.model
    def default_get(self, fields):
        res = super(Lead2OpportunityMassConvert, self).default_get(fields)
        if 'partner_id' in fields:  # avoid forcing the partner of the first lead as default
            res['partner_id'] = False
        if 'action' in fields:
            res['action'] = 'nothing'
        if 'name' in fields:
            res['name'] = 'convert'
        if 'opportunity_ids' in fields:
            res['opportunity_ids'] = False
        return res

    action = fields.Selection([('each_exist_or_create', 'Use existing partner or create'), ('nothing', 'Do not link to a customer')], 'Related Customer', required=True, default="nothing")
