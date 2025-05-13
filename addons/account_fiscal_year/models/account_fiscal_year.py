from odoo import fields, models, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    @api.depends('period_ids')
    def get_period_list(self):
        for res in self:
            if len(res.period_ids) > 0:
                res.period_created = True
            else:
                res.period_created = False

    code = fields.Char("Code", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    period_ids = fields.One2many('account.period.part', 'fiscal_year_id', string="Periods", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Open'), ('waiting', 'Waiting for Approval'), ('done', 'Closed'), ('reopen', 'Waiting for Re-Open Approval')], string="State", default="draft")
    move_id = fields.Many2one('account.move', string="End of Year Entries Journal", readonly=True, states={'draft': [('readonly', False)]})
    period_created = fields.Boolean("Is period Creted?", compute="get_period_list", store=True)

    @api.multi
    def create_period(self):
        for res in self:
            if not res.company_id.period_type:
                raise UserError(_('Please define an period type for this company in configuration.'))
            if res.company_id.period_type and res.company_id.period_type == "1":
                res.create_period_monthly()
            if res.company_id.period_type and res.company_id.period_type == "3":
                res.create_period_3_monthly()
            if res.company_id.period_type and res.company_id.period_type == '6':
                res.create_period_6_monthly()
            if res.company_id.period_type and res.company_id.period_type == "12":
                res.create_period_yearly()

    @api.multi
    def create_period_yearly(self):
        period_obj = self.env['account.period.part']
        for rec in self:
            ds = rec.date_from
            period_obj.create({
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscal_year_id': rec.id,
            })
            while ds < rec.date_to:
                de = ds + relativedelta(years=1, days=-1)

                if de > rec.date_to:
                    de = rec.date_to

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscal_year_id': rec.id,
                })
                ds = ds + relativedelta(years=1)
        return True

    @api.multi
    def create_period_6_monthly(self):
        period_obj = self.env['account.period.part']
        for rec in self:
            ds = rec.date_from
            period_obj.create({
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscal_year_id': rec.id,
            })
            while ds < rec.date_to:
                de = ds + relativedelta(months=6, days=-1)

                if de > rec.date_to:
                    de = rec.date_to

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscal_year_id': rec.id,
                })
                ds = ds + relativedelta(months=6)
        return True

    @api.multi
    def create_period_3_monthly(self):
        period_obj = self.env['account.period.part']
        for rec in self:
            ds = rec.date_from
            period_obj.create({
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscal_year_id': rec.id,
            })
            while ds < rec.date_to:
                de = ds + relativedelta(months=3, days=-1)

                if de > rec.date_to:
                    de = rec.date_to

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscal_year_id': rec.id,
                })
                ds = ds + relativedelta(months=3)
        return True

    @api.multi
    def create_period_monthly(self):
        period_obj = self.env['account.period.part']
        for rec in self:
            ds = rec.date_from
            period_obj.create({
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscal_year_id': rec.id,
            })
            while ds < rec.date_to:
                de = ds + relativedelta(months=1, days=-1)

                if de > rec.date_to:
                    de = rec.date_to

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscal_year_id': rec.id,
                })
                ds = ds + relativedelta(months=1)
        return True

    def close_fiscal_year_approve(self):
        if self.move_id.state != 'posted':
            raise UserError(_(
                'In order to close a fiscalyear, you must first post related journal entries.'))

        self._cr.execute('UPDATE account_period_part SET state = %s '
                         'WHERE fiscal_year_id = %s', ('done', self.id))
        self._cr.execute('UPDATE account_fiscal_year '
                         'SET state = %s WHERE id = %s', ('done', self.id))

        return {'type': 'ir.actions.act_window_close'}

    def re_open_fiscal_year_approve(self):

        if self.state == 'reopen':

            self._cr.execute('UPDATE account_fiscal_year '
                             'SET state = %s WHERE id = %s', ('draft', self.id))
            self._cr.execute('UPDATE account_period_part SET state = %s '
                             'WHERE fiscal_year_id = %s', ('draft', self.id))

    def re_open_fiscal_year(self):
        for rec in self:
            if rec.env.user.company_id.enable_approval:
                rec.write({'state': 'reopen'})
                rec.period_ids.write({'state': 'reopen'})
            else:
                rec.write({'state': 'draft'})
                self.period_ids.write({'state': 'draft'})


class AccountPeriodPart(models.Model):
    _name = 'account.period.part'
    _description = "Fiscal Period"

    name = fields.Char("Period Name", required="1", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char("Code", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Date("Start of Period", required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date("End of Period", required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]})
    fiscal_year_id = fields.Many2one('account.fiscal.year', string="Fiscal Year", readonly=True, states={'draft': [('readonly', False)]})
    special = fields.Boolean("Opening/Closing Period", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Open'), ('waiting', 'Waiting for Approval'), ('done', 'Closed'), ('reopen', 'Waiting for Re-Open Approval')], string="State", default="draft")
    company_id = fields.Many2one(related="fiscal_year_id.company_id", string='Company', required=True, default=lambda self: self.env.user.company_id, store=True)

    def close_period(self):
        for rec in self:
            if rec.env.user.company_id.enable_approval:
                rec.write({'state': 'waiting'})
            else:
                rec.write({'state': 'done'})

    def reopen_period(self):
        if self.env.user.company_id.enable_approval:
            self.write({'state': 'reopen'})
        else:
            self.write({'state': 'draft'})

    def close_period_approve(self):
        for rec in self:

            rec.write({'state': 'done'})

    def reopen_period_approve(self):

        self.write({'state': 'draft'})
