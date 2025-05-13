# -*- coding: utf-8 -*-
# Copyright (C) Laxicon Solution.


from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Move(models.Model):
    _inherit = 'account.move'

    period_id = fields.Many2one('account.period.part', string="Period", compute='get_period', store=True)
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year", related="period_id.fiscal_year_id", store=True)

    @api.depends('date')
    def get_period(self):
        if self:
            for rec in self:
                rec.period_id = False
                if rec.date:
                    period = self.env['account.period.part'].sudo().search(
                        [('date_from', '<=', rec.date), ('date_to', '>=', rec.date)], limit=1)
                    if period:
                        rec.period_id = period.id

    @api.model
    def create(self, vals):
        # OVERRIDE
        res = super(Move, self).create(vals)
        for val in vals:

            if vals.get('date'):
                period = self.env['account.period.part'].sudo().search(
                    [('date_from', '<=', vals.get('date')), ('date_to', '>=', vals.get('date'))], limit=1)

                if self.env.user.company_id.restrict_for_close_period and period.state == 'done':
                    raise UserError(_(
                        "You can not Select Date from Closed Fiscal Period / Closed Fiscal Year."))
        return res

    @api.multi
    def write(self, vals):
        rslt = super(Move, self).write(vals)
        if self:
            for rec in self:
                if rec.company_id.restrict_for_close_period and rec.period_id.state == 'done':
                    raise UserError(_(
                        "You can not Select Date from Closed Fiscal Period / Closed Fiscal Year."))
        return rslt


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one('account.period.part', string="Period", related="move_id.period_id", store=True)
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year", related="period_id.fiscal_year_id", store=True)
