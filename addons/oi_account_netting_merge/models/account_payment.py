from odoo import api, models, fields, _
from odoo.exceptions import Warning, ValidationError, UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    account_netting_id = fields.Many2one('account.netting', readonly=True, string="Contra")

    @api.model
    def default_get(self, fields):
        res = super(AccountPayment, self).default_get(fields)
        if self._context.get('default_account_netting_id'):
            contra = self.env['account.netting'].browse(
                self._context.get('default_account_netting_id'))
            if not contra.is_company_currency_contra() and 'exchange_rate_inverse' in fields:
                res.update({'exchange_rate_inverse': contra.get_exch_rate()})
        return res

    @api.model
    def _compute_payment_amount(self, invoices=None, currency=None):
        if self._context.get('default_account_netting_id'):
            doc = self.env['account.netting'].browse(
                self._context.get('default_account_netting_id'))
            payment_currency = currency
            if not payment_currency:
                payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id
            return doc.currency_id._convert(abs(doc.amount_residual), payment_currency, doc.company_id, self.payment_date or fields.Date.today())

        return super(AccountPayment, self)._compute_payment_amount(invoices=invoices, currency=currency)

    def post(self):
        res = super(AccountPayment, self).post()
        for record in self:
            if record.account_netting_id:
                if record.account_netting_id.state == 'draft':
                    record.account_netting_id.with_context(no_check_balance=True).action_post()
                record.account_netting_id.with_context(lines_no_update=True).reload_data()
        return res

    @api.onchange('amount')
    def _onchange_amount(self):
        res = super(AccountPayment, self)._onchange_amount()
        return res

    @api.model
    def create(self, vals):
        if 'default_account_netting_id' in self._context:
            contra = self.env['account.netting'].browse(self._context.get('default_account_netting_id'))
            if vals.get('currency_id') == contra.currency_id.id:
                total_amount = vals.get('amount')
            elif vals.get('currency_id') != self.company_id.currency_id and self.company_id.currency_id == contra.currency_id:
                total_amount = vals.get('amount') * (vals.get('exchange_rate_inverse') or 1)
            else:
                raise UserError('Can\'t reconcile MYR payment to USD invoices/bills')
            if total_amount < contra.amount_residual:
                raise UserError(f'Payment amount should be greater or equal to amount residual ({contra.amount_residual} {contra.currency_id.name})')

        if not vals.get('name') and ('netting' in vals and vals.get('netting')):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('cotra.payment.receipts') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'cotra.payment.receipts') or _('New')
        res = super(AccountPayment, self).create(vals)

        if 'default_account_netting_id' in self._context:
            res.payment_move_line_ids = [(5, 0, 0)] + \
                                        [(0, 0, line_vals)
                                         for line_vals in contra.lines_to_reconcile_with_payment()]
        return res

    def action_print_contra(self):
        self.ensure_one()
        self.account_netting_id.write({'temp_payment_id': self.id})
        return self.env.ref('oi_account_netting_merge.action_report_contra').report_action(self.account_netting_id.id)


class AccountAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

    netting = fields.Boolean(
        string='Netting', help="Technical field, as user select invoice that are both AR and AP")


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    @api.multi
    def _prepare_payment_vals(self, invoices):
        values = super()._prepare_payment_vals(invoices)
        if self.netting:
            values['netting'] = self.netting
        return values
