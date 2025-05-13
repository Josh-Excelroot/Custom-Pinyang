
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    period_id = fields.Many2one('account.period.part', string="Period", compute='get_period', store=True)
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year", related="period_id.fiscal_year_id", store=True)

    @api.depends('date_invoice')
    def get_period(self):
        if self:
            for rec in self:
                rec.period_id = False
                if rec.date_invoice:
                    period = self.env['account.period.part'].sudo().search(
                        [('date_from', '<=', rec.date_invoice), ('date_to', '>=', rec.date_invoice)], limit=1)
                    if period:
                        rec.period_id = period.id

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if vals.get('date_invoice'):
            period = self.env['account.period.part'].sudo().search(
                [('date_from', '<=', vals.get('date_invoice')), ('date_to', '>=', vals.get('date_invoice'))], limit=1)

            if self.env.user.company_id.restrict_for_close_period and period.state == 'done':
                raise UserError(_(
                    "You can not Select Date from Closed Fiscal Period / Closed Fiscal Year."))
        return res

    @api.multi
    def _write(self, vals):
        res = super(AccountInvoice, self)._write(vals)
        if self:
            for rec in self:
                if rec.company_id.restrict_for_close_period and rec.period_id.state == 'done':
                    raise UserError(_(
                        "You can not Select Date from Closed Fiscal Period / Closed Fiscal Year."))
        return res


class AxxountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[('opening', 'Opening/Closing Situation')])
