# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round

class FAFPercent(models.TransientModel):
    _name = 'freight.faf.percent'
    _description = 'FAF Percent'

    faf_percent = fields.Float(string='New FAF Percent', digits=(12, 2), track_visibility='onchange')
    #Link to the main invoice
    #haulage_charge_id = fields.Many2one('freight.haulage.charge', string="Invoice")


    @api.multi
    def action_update_all(self):
        self.ensure_one()
        haulage_charges = self.env['freight.haulage.charge'].search([('is_faf_percent', '=', True)])
        for hc in haulage_charges:
            new_faf = float_round((hc.haulage_rates * self.faf_percent / 100), 2, rounding_method='HALF-UP')
            total = hc.haulage_rates + hc.road_tolls + new_faf + hc.depot_gate_charges
            hc.write({'faf_percent': self.faf_percent,
                      'faf': new_faf,
                      'total': total,
                      'state': 'active',
                      })

        # self.invoice_id.write({'state': 'draft'})
        # self.invoice_id.write({'reject_reason': self.reject_reason
        #                        })

        return True
