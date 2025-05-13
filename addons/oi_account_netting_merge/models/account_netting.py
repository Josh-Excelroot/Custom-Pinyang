'''
Created on Oct 20, 2021

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError


def sorted_by_date(lines):
    return lines.sorted(key=lambda line: (line.date_maturity or line.date, line.id))


class AccountNetting(models.Model):
    _name = 'account.netting'
    _description = 'Account Netting'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _states = {'draft': [('readonly', False)]}

    name = fields.Char('Number', compute='_calc_name', store=True)
    journal_id = fields.Many2one('account.journal', required=True, readonly=True,
                                 states=_states, default=lambda self: self.env['account.move']._get_default_journal())
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', copy=False, readonly=True)
    contra_type = fields.Selection([('same_partner', 'Same Partner'), ('different_partner', 'Different Partner')],
                                   readonly=True, states=_states, string='Contra Type')

    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.user.company_id, readonly=True, states=_states)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, readonly=True,
                                  states=_states)

    receivable_partner_id = fields.Many2one('res.partner', required=True, domain=[
        '|', ('is_company', '=', True), ('parent_id', '=', False), ('customer', '=', True)], readonly=True,
                                            states=_states)
    payable_partner_id = fields.Many2one('res.partner', required=True, domain=[
        '|', ('is_company', '=', True), ('parent_id', '=', False), ('supplier', '=', True)], readonly=True,
                                         states=_states)

    ref = fields.Char(string='Reference', copy=False,
                      readonly=True, states=_states, default="AR/AP netting")
    date = fields.Date(string='Date', required=True,
                       default=fields.Date.today(), readonly=True, states=_states)

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='Status', required=True, readonly=True, copy=False, track_visibility=True,
        default='draft', compute='_calc_state', store=True)

    receivable_line_ids = fields.Many2many('account.move.line', string='Receivable Items',
                                           relation='account_netting_receivable_lines_rel', copy=False, readonly=True,
                                           states=_states)
    payable_line_ids = fields.Many2many('account.move.line', string='Payable Items',
                                        relation='account_netting_payable_lines_rel', copy=False, readonly=True,
                                        states=_states)

    receivable_balance = fields.Monetary(
        compute='_calc_receivable_balance', store=True)
    payable_balance = fields.Monetary(
        compute='_calc_payable_balance', store=True)

    balance = fields.Monetary(compute='_calc_balance', store=True)
    balance_type = fields.Selection(
        [("pay", "To pay"), ("receive", "To receive")], compute='_calc_balance', store=True)

    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')],
        string='Payment', store=True, readonly=True, copy=False, track_visibility=True,
        compute='_calc_payment_state')

    amount_residual = fields.Monetary(
        compute='_calc_amount_residual', store=True)

    payment_ids = fields.One2many('account.payment', 'account_netting_id')
    payment_count = fields.Integer(compute='_calc_payment_count')
    temp_payment_id = fields.Many2one('account.payment', 'Payment')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags',
                                        )
    # @api.onchange('receivable_line_ids', 'payable_line_ids')
    # def _onchange_line_ids(self):
    #     if not self.receivable_line_ids and not self.payable_line_ids:
    #         self.analytic_tag_ids = False
    #         self.analytic_tag_ids = self.default_get(['analytic_tag_ids']).get('analytic_tag_ids', False)
    #     else:
    #         self.analytic_tag_ids = (self.receivable_line_ids + self.payable_line_ids).mapped('analytic_tag_ids')

    @api.onchange('contra_receivable_ids', 'contra_payable_ids')
    def _onchange_line_ids(self):
        if not self.contra_receivable_ids and not self.contra_payable_ids:
            self.analytic_tag_ids = False
            self.analytic_tag_ids = self.default_get(['analytic_tag_ids']).get('analytic_tag_ids', False)
        else:
            self.analytic_tag_ids = (self.contra_receivable_ids + self.contra_payable_ids)\
                .filter_lines().mapped('line').mapped('analytic_tag_ids')

    @api.depends('payment_ids')
    def _calc_payment_count(self):
        for record in self:
            record.payment_count = len(record.payment_ids.filtered(lambda p: p.state != 'cancelled'))

    @api.depends('move_id.name')
    def _calc_name(self):
        for record in self:
            record.name = record.move_id.name or '/'

    @api.depends('move_id.state')
    def _calc_state(self):
        for record in self:
            record.state = record.move_id.state or 'draft'

    @api.onchange('contra_type')
    def _onchange_contra_type(self):
        self.receivable_partner_id = False
        self.payable_partner_id = False

    @api.onchange('receivable_partner_id', 'payable_partner_id')
    def _onchange_receivable_partner(self):
        print("self.contra_type", self.contra_type)
        if (self.receivable_partner_id or self.payable_partner_id) and not self.contra_type:
            raise ValidationError(_("Please select Contra Type."))
        if self.receivable_partner_id.supplier and self.contra_type == 'same_partner':
            self.payable_partner_id = self.receivable_partner_id.id
        if self.receivable_partner_id and self.payable_partner_id:
            if self.contra_type == 'different_partner' and self.receivable_partner_id == self.payable_partner_id:
                raise ValidationError(_("Please select different partner"))
            elif self.contra_type == 'same_partner' and self.receivable_partner_id != self.payable_partner_id:
                raise ValidationError(_("Please select same partner"))

    def _compute_balance(self, line_ids, company_currency=False):
        balance = 0
        is_company_currency = company_currency or self.currency_id == self.env.user.company_id.currency_id
        for line in line_ids:
            if line.amount_currency and not is_company_currency:
                balance += line.currency_id._convert(
                    line.amount_residual_currency, self.currency_id, self.company_id, self.date)
            else:
                balance += line.company_currency_id._convert(
                    line.amount_residual, self.currency_id, self.company_id, self.date)
        return self.currency_id.round(balance)

    @api.depends('contra_receivable_ids.reconcile', 'contra_receivable_ids.contra_amount', 'contra_receivable_ids.payment_amount')
    def _calc_receivable_balance(self):
        for rec in self:
            rec.receivable_balance = rec.contra_receivable_ids._compute_reconcile_total()

    @api.depends('contra_payable_ids.reconcile', 'contra_payable_ids.contra_amount', 'contra_payable_ids.payment_amount')
    def _calc_payable_balance(self):
        for rec in self:
            rec.payable_balance = rec.contra_payable_ids._compute_reconcile_total()

    @api.depends('contra_receivable_ids.reconcile', 'contra_receivable_ids.contra_amount', 'contra_receivable_ids.payment_amount',
                 'contra_payable_ids.reconcile', 'contra_payable_ids.contra_amount', 'contra_payable_ids.payment_amount',
                 'payment_ids')
    def _calc_amount_residual(self):
        for rec in self:
            amount_residual = rec.receivable_balance - rec.payable_balance
            if rec.balance_type == 'pay':
                amount_residual *= -1
            for payment in rec.payment_ids:
                if payment.state not in ['draft', 'cancelled']:
                    if self.currency_id != payment.currency_id and payment.currency_id != self.company_id.currency_id:
                        amount_residual -= payment.amount * payment.exchange_rate_inverse
                    else:
                        amount_residual -= payment.amount
            if amount_residual < 0:
                amount_residual = 0
            rec.amount_residual = amount_residual

    @api.depends('receivable_balance', 'payable_balance')
    def _calc_balance(self):
        for record in self:
            balance = record.receivable_balance - record.payable_balance
            record.balance_type = balance > 0 and 'receive' or 'pay'
            record.balance = abs(balance)

    @api.depends('move_id', 'amount_residual', 'balance', 'state')
    def _calc_payment_state(self):
        for record in self:
            if not record.move_id or record.state != 'posted':
                record.payment_state = False
                continue

            if not record.amount_residual:
                record.payment_state = 'paid'
            elif record.amount_residual == record.balance:
                record.payment_state = 'not_paid'
            else:
                record.payment_state = 'partial'

    def _get_move_vals(self):
        return {
            'journal_id': self.journal_id.id,
            'ref': self.ref,
            'date': self.date,
            'line_ids': [],
            'netting_id': self.id
        }

    def get_exch_rate(self, ttype=False):
        if not ttype:
            ttype = self.balance_type
        if ttype == 'receive':
            ttype = 'receivable'
        else:
            ttype = 'payable'
        if self.is_company_currency_contra():
            return 1
        move_lines = getattr(self, f'contra_{ttype}_ids').filter_lines().mapped('line')
        # Ahmad Zaman - Changed Contra Exchange Rate Calculation
        lines_with_exchange_rate = 0
        total_exch = 0
        for line in move_lines:
            if line.invoice_id and line.invoice_id.exchange_rate_inverse not in [0,1]:
                lines_with_exchange_rate += 1
                total_exch += line.invoice_id.exchange_rate_inverse
        return round(total_exch/lines_with_exchange_rate, 6)
        # return self._compute_balance(move_lines, company_currency=True) / self._compute_balance(move_lines)

    def action_post(self):
        contra_receivables = self.contra_receivable_ids.filter_lines()
        contra_payables = self.contra_payable_ids.filter_lines()
        if not contra_receivables:
            raise UserError(_('Please select receivable items'))
        if not contra_payables:
            raise UserError(_('Please select payable items'))
        if not self._context.get('no_check_balance') and self.receivable_balance != self.payable_balance:
            raise UserError('Please make sure receivable balance is equal to payable balance\n'
                            'or Register Payment')

        move_vals = self._get_move_vals()
        exch_rate = self.get_exch_rate(self.balance_type)

        is_company_currency_contra = self.is_company_currency_contra()
        settlement_difference, credit_line, debit_line = 0, None, None
        for contra_line in (contra_receivables + contra_payables):
            if not contra_line.contra_amount:
                continue
            ttype = contra_line.ttype
            line_val = {
                'name': 'CONTRA FOR ' + contra_line.line.display_name,
                'account_id': contra_line.account_id.id,
                'partner_id': getattr(self, f'{ttype}_partner_id').id,
                'currency_id': contra_line.currency_id.id or self.company_id.currency_id.id,
                'analytic_tag_ids': self.analytic_tag_ids.ids,
                'netting_id': self.id,
                'date_maturity': self.date,
                'credit': contra_line.debit and round(contra_line.contra_amount * exch_rate, 2),
                'debit': contra_line.credit and round(contra_line.contra_amount * exch_rate, 2),
                'journal_currency_rate': exch_rate,
            }
            if not is_company_currency_contra:
                line_val['amount_currency'] = contra_line.contra_amount * ((contra_line.debit and -1) or 1)
                if line_val['credit']:
                    settlement_difference -= line_val['credit']
                    credit_line = line_val
                else:
                    settlement_difference += line_val['debit']
                    debit_line = line_val
            move_vals['line_ids'].append((0, 0, line_val))

        if not is_company_currency_contra:
            if settlement_difference > 0:
                credit_line['credit'] += settlement_difference
            elif settlement_difference < 0:
                debit_line['debit'] -= settlement_difference

        if self.move_id and self.move_id.journal_id != self.journal_id:
            self.move_id = False

        if self.move_id:
            move_vals['line_ids'].insert(0, (5,))
            self.move_id.write(move_vals)
        else:
            self.move_id = self.env['account.move'].create(move_vals)

        self.move_id.action_post()

        for contra_line in (contra_receivables + contra_payables):
            move_line = self.move_id.line_ids.filtered(lambda l: l.name == 'CONTRA FOR ' + contra_line.line.display_name)
            if move_line:
                if self.is_company_currency_contra():
                    (move_line[0] + contra_line.line).reconcile()
                else:
                    (move_line[0] + contra_line.line).with_context(create_contra_exch_entry=True).reconcile()

        self.with_context(lines_no_update=True).reload_data()

    def button_cancel(self):
        contra_move_line_ids = self.move_id.line_ids.ids
        payment_move_line_ids = self.payment_ids.mapped('move_line_ids').ids
        for contra_line in (self.contra_receivable_ids + self.contra_payable_ids):
            if contra_line.payment_amount:
                contra_line.write({
                    'contra_amount': contra_line.contra_amount + contra_line.payment_amount,
                    'payment_amount': 0
                })
        exchange_rate_entries = self.env['account.move'].search([
            ('journal_id.name', 'in', ['Exchange Difference']),
            '|',
            ('rate_diff_partial_rec_id.credit_move_id', 'in', contra_move_line_ids + payment_move_line_ids),
            ('rate_diff_partial_rec_id.debit_move_id', 'in', contra_move_line_ids + payment_move_line_ids)
        ])
        for exchange_rate_entry in exchange_rate_entries:
            exchange_rate_entry.button_cancel()
            exchange_rate_entry.unlink()
        recon = self.env['account.partial.reconcile'].search([
            '|',
             ('credit_move_id', 'in', contra_move_line_ids + payment_move_line_ids),
             ('debit_move_id', 'in', contra_move_line_ids + payment_move_line_ids)
        ])
        if recon:
            recon.unlink()
        if self.move_id:
            self.move_id.button_cancel()
        for payment in self.payment_ids:
            payment.cancel()
        self.with_context(lines_no_update=True).reload_data()

    def unlink(self):
        self.mapped('move_id').unlink()
        return super(AccountNetting, self).unlink()

    def _get_payment_context(self):
        context = {
            'active_ids': self.ids,
            'active_model': self._name,
            'active_id': self.id,
            'default_amount': self.amount_residual,
            'default_currency_id': self.currency_id.id,
            'default_communication': self.ref,
            'default_account_netting_id': self.id,
            'default_netting': True
        }

        if self.balance_type == 'pay':
            context.update({
                'default_partner_id': self.payable_partner_id.id,
                'default_payment_type': self.amount_residual > 0 and 'outbound' or 'inbound',
                'default_partner_type': 'supplier',
            })
        else:
            context.update({
                'default_partner_id': self.receivable_partner_id.id,
                'default_payment_type': self.amount_residual > 0 and 'inbound' or 'outbound',
                'default_partner_type': 'customer',
            })
        return context

    def action_register_payment(self):
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref("oi_account_netting_merge.view_account_payment_account_netting_form").id,
            'context': self._get_payment_context()
        }

    def action_view_payments(self):
        action, = self.env.ref("account.action_account_payments").read([])
        action.update({
            'context': self._get_payment_context(),
            'domain': [('account_netting_id', '=', self.id), ('state', '!=', 'cancelled')]
        })
        if len(self.payment_ids) == 1:
            action.update({
                'views': [(False, 'form')],
                'res_id': self.payment_ids.id
            })
        return action

    def customer_detail_print(self):
        self.ensure_one()
        data = {}
        final_data = {}
        line_ids = []
        total_amount = 0.0
        for rec in self.receivable_line_ids.filtered(lambda x: x.account_id.reconcile):
            line_ids = [(r.debit_move_id, r.amount) for r in rec.matched_debit_ids if
                        r.debit_move_id.move_id == self.move_id] if rec.credit > 0 else [(r.credit_move_id, r.amount)
                                                                                         for r in rec.matched_credit_ids
                                                                                         if
                                                                                         r.credit_move_id.move_id == self.move_id]
            line_ids += [('pay', r.amount) for r in rec.matched_debit_ids if
                         r.debit_move_id.payment_id == self.temp_payment_id] if rec.credit > 0 else [('pay', r.amount)
                                                                                                     for r in
                                                                                                     rec.matched_credit_ids
                                                                                                     if
                                                                                                     r.credit_move_id.payment_id == self.temp_payment_id]
            data.update({rec: line_ids})
        for key in data:
            for val in data[key]:
                if key.move_id.name not in final_data:
                    final_data.update({key.move_id.name: {
                        'date': key.date,
                        'invoice_number': key.move_id.name,
                        'original_amount': key.debit,
                        'paid_amount': val[1] if val[0] != 'pay' else 0.0,
                        'currency': key.currency_id.name if key.currency_id else key.company_currency_id.name,
                        'amount_residual': key.amount_residual,
                        'payment_amount': val[1] if val[0] == 'pay' else 0.0
                    }})
                else:
                    final_data[key.move_id.name]['original_amount'] += val[1] if val[0] != 'pay' else 0.0
                    final_data[key.move_id.name]['payment_amount'] += val[1] if val[0] == 'pay' else 0.0
                total_amount += val[1] if val[0] != 'pay' else 0.0
        f_list = list(final_data.values())
        return f_list, total_amount

    def supplier_detail_print(self):
        self.ensure_one()
        data = {}
        final_data = {}
        line_ids = []
        for rec in self.payable_line_ids.filtered(lambda x: x.account_id.reconcile):
            line_ids = [(r.debit_move_id, r.amount) for r in rec.matched_debit_ids if
                        r.debit_move_id.move_id == self.move_id] if rec.credit > 0 else [(r.credit_move_id, r.amount)
                                                                                         for r in rec.matched_credit_ids
                                                                                         if
                                                                                         r.credit_move_id.move_id == self.move_id]
            line_ids += [('pay', r.amount) for r in rec.matched_debit_ids if
                         r.debit_move_id.payment_id == self.temp_payment_id] if rec.credit > 0 else [('pay', r.amount)
                                                                                                     for r in
                                                                                                     rec.matched_credit_ids
                                                                                                     if
                                                                                                     r.credit_move_id.payment_id == self.temp_payment_id]
            data.update({rec: line_ids})
        for key in data:
            for val in data[key]:
                if key.move_id.name not in final_data:
                    final_data.update({key.move_id.name: {
                        'date': key.date,
                        'invoice_number': key.move_id.name,
                        'original_amount': key.credit,
                        'paid_amount': val[1] if val[0] != 'pay' else 0.0,
                        'currency': key.currency_id.name if key.currency_id else key.company_currency_id.name,
                        'amount_residual': key.amount_residual,
                        'payment_amount': val[1] if val[0] == 'pay' else 0.0
                    }})
                else:
                    final_data[key.move_id.name]['original_amount'] += val[1] if val[0] != 'pay' else 0.0
                    final_data[key.move_id.name]['payment_amount'] += val[1] if val[0] == 'pay' else 0.0
        f_list = list(final_data.values())
        return f_list

    @api.onchange('currency_id')
    def reload_data2(self):
        self._calc_receivable_balance()
        self._calc_payable_balance()
        self._calc_balance()
        self._calc_amount_residual()
        if not isinstance(self.id, models.NewId) and not self._context.get('lines_no_update'):
            self.with_context(ttype='receivable', update_only=True).action_refresh_lines()
            self.with_context(ttype='payable', update_only=True).action_refresh_lines()

    def reload_data(self):
        self.reload_data2()
        self._calc_name()
        self._calc_state()
        self._calc_payment_count()
        self._calc_payment_state()

    @api.constrains('receivable_line_ids', 'payable_line_ids', 'currency_id')
    def validate_currency_in_lines(self):
        company_currency = self.company_id.currency_id or self.env.user.company_id.currency_id
        contra_currency = self.currency_id or company_currency

        def get_invalid_lines_err_message(lines, type_, error_msg=''):
            invalid_lines = []
            for line in lines:
                if (not line.currency_id and contra_currency != company_currency) or (line.currency_id and line.currency_id != contra_currency):
                    invalid_lines.append(line.move_id.name + (f'({line.ref})' if line.ref else f'({line.name})'))
            if invalid_lines:
                error_msg += f'{type_} Lines:\n{", ".join(invalid_lines)}\nare from different currency.\n\n'
            return error_msg

        error_msg = get_invalid_lines_err_message(self.receivable_line_ids, 'Receivable')
        error_msg = get_invalid_lines_err_message(self.payable_line_ids, 'Payable', error_msg)
        if error_msg:
            raise ValidationError(error_msg + f'And contra currency is different ({contra_currency.name})\n'
                                              f'Select {contra_currency.name} lines or different contra currency')

    @api.constrains('receivable_partner_id', 'currency_id')
    def reset_receivable_lines(self):
        self.with_context(ttype='receivable').action_refresh_lines()

    @api.constrains('payable_partner_id', 'currency_id')
    def reset_payable_lines(self):
        self.with_context(ttype='payable').action_refresh_lines()

    @api.multi
    def write(self, values):
        return super(AccountNetting, self).write(values)

    contra_receivable_ids = fields.One2many('account.netting.line', 'receivable_line_netting_id')
    contra_payable_ids = fields.One2many('account.netting.line', 'payable_line_netting_id')

    def is_company_currency_contra(self):
        return self.currency_id == self.company_id.currency_id

    def get_search_aml_domain(self, ttype):
        sign = '>' if ttype == 'receivable' else '<'
        domain = [
            ('reconciled', '=', False), ('parent_state', '=', 'posted'),
            ('partner_id', '=', getattr(self, f'{ttype}_partner_id').id),
            ('account_id.internal_type', '=', ttype),
            '|', ('amount_residual', sign, 0), ('amount_residual_currency', sign, 0)
        ]
        if self.currency_id and not self.is_company_currency_contra():
            domain += [('currency_id', '=', self.currency_id.id)]
        else:
            domain += ['|', ('currency_id', '=', False), ('currency_id', '=', self.currency_id.id)]
        return domain

    def action_refresh_lines(self):
        ttype = self._context.get('ttype')
        domain = self.get_search_aml_domain(ttype)

        move_lines = self.env['account.move.line'].search(domain)
        update_only = self._context.get('update_only')
        contra_line_ids = getattr(self, f'contra_{ttype}_ids')

        if update_only:
            move_lines_to_add = move_lines.filtered(lambda aml: aml not in contra_line_ids.mapped('line'))
            contra_line_ids.filtered(lambda cl: cl.line not in move_lines).unlink()
        else:
            setattr(self, f'contra_{ttype}_ids', False)
            move_lines_to_add = move_lines

        if move_lines_to_add:
            values = ', '.join([f"({self.id}, {line_id.id}, '{ttype}', '{line_id.date}')" for line_id in move_lines_to_add])
            query = f"INSERT INTO account_netting_line ({ttype}_line_netting_id, line, ttype, date) VALUES " + values
            self._cr.execute(query)
            self._cr.commit()

    def lines_to_reconcile_with_payment(self):
        if self.receivable_balance > self.payable_balance:
            ttype = 'receivable'
        elif self.receivable_balance < self.payable_balance:
            ttype = 'payable'
        else:
            raise UserError('Payment could not create because there is no amount due')
        line_values = []
        # exch_rate = self.get_exch_rate()
        exch_rate = 1

        contra_lines = getattr(self, f'contra_{ttype}_ids').filter_lines(reverse=True)
        amount_residual = self.amount_residual
        for contra_line in contra_lines:
            if not amount_residual:
                break
            if amount_residual < contra_line.contra_amount:
                if exch_rate:
                    payment_reconcile_amount = amount_residual * exch_rate
                else:
                    payment_reconcile_amount = amount_residual

                contra_line.write({
                    'contra_amount': contra_line.contra_amount - amount_residual,
                    'payment_amount': amount_residual
                })
                amount_residual = 0
            else:
                if exch_rate:
                    payment_reconcile_amount = contra_line.contra_amount * exch_rate
                else:
                    payment_reconcile_amount = contra_line.contra_amount
                amount_residual -= contra_line.contra_amount
                contra_line.write({
                    'contra_amount': 0,
                    'payment_amount': contra_line.contra_amount
                })

            line_values.append({
                'move_line_id': contra_line.line.id,
                'allocate': True,
                'allocate_amount': payment_reconcile_amount,
            })

        return line_values


class AccountNettingLines(models.Model):
    _name = 'account.netting.line'
    _order = 'reconcile desc,date asc,contra_amount asc'

    receivable_line_netting_id = fields.Many2one('account.netting')
    payable_line_netting_id = fields.Many2one('account.netting')
    line = fields.Many2one('account.move.line', readonly=True)
    ttype = fields.Selection([('receivable', 'receivable'), ('payable', 'payable')])
    reconcile = fields.Boolean()
    contra_amount = fields.Float()
    payment_amount = fields.Float(readonly=True)
    move_id = fields.Many2one(related='line.move_id')
    name = fields.Char(related='line.name')
    date = fields.Date(related='line.date', store=True)
    account_id = fields.Many2one(related='line.account_id')
    currency_id = fields.Many2one(related='line.currency_id')
    company_currency_id = fields.Many2one(related='line.company_currency_id')
    debit = fields.Monetary(related='line.debit', currency_field='company_currency_id')
    credit = fields.Monetary(related='line.credit', currency_field='company_currency_id')
    amount_currency = fields.Monetary(related='line.amount_currency', currency_field='currency_id')
    amount_residual = fields.Monetary(related='line.amount_residual', currency_field='company_currency_id')
    amount_residual_currency = fields.Monetary(related='line.amount_residual_currency', currency_field='currency_id')

    @api.onchange('reconcile')
    def onchange_reconcile(self):
        if self.reconcile:
            if (self.receivable_line_netting_id + self.payable_line_netting_id).is_company_currency_contra():
                self.contra_amount = abs(self.amount_residual)
            else:
                self.contra_amount = abs(self.amount_residual_currency)
        else:
            self.contra_amount = 0.00

    @api.onchange('contra_amount')
    def onchange_contra_amount(self):
        if (self.receivable_line_netting_id + self.payable_line_netting_id).is_company_currency_contra():
            residual = abs(self.amount_residual)
        else:
            residual = abs(self.amount_residual_currency)
        if self.contra_amount > residual:
            self.contra_amount = residual
            return {'warning': {
                'title': _('Amount Exceeded!'),
                'message': _('Contra amount can not be higher than residual amount')
            }}
        if self.contra_amount < 0:
            self.contra_amount = 0
            return {'warning': {
                'title': _('Amount Negative!'),
                'message': _('Contra amount can not be in negative')
            }}

    def filter_lines(self, reverse=False):
        return self.filtered(
            lambda line: line.date and line.reconcile and (line.contra_amount > 0 or line.payment_amount > 0)).sorted(
            key=lambda cl: (cl.date, cl.line.id), reverse=reverse)

    def _compute_reconcile_total(self):
        contra_lines = self.filter_lines()
        return sum([cl.contra_amount + cl.payment_amount for cl in contra_lines])
