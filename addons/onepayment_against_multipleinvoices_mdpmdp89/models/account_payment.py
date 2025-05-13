# coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from odoo.tools import float_is_zero, float_compare
from odoo.tools import float_round


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_move_line_ids = fields.One2many(
        'payment.move.line', 'payment_id', string="Open Journal")
    bank_charge_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    bank_charge_amount = fields.Monetary('Extra Bank Charges Amount', currency_field='bank_charge_currency_id')
    bank_company_curr_amount = fields.Monetary('Bank Charges Converted Amount', readonly=True, digits=(12, 6), currency_field='company_currency_id')
    bank_charge_exch_rate_inv = fields.Float(digits=(8, 6), default=1.0)
    bank_charge_account_id = fields.Many2one('account.account', string='Bank Charge Account', domain=[
                                             ('user_type_id.name', '=', 'Expenses')])
    hide_bank_exch_rate_inv = fields.Boolean(compute='_compute_hide_bank_exch_rate_inv')
    payment_invoice_ids = fields.One2many(
        'account.payment.invoice', 'payment_id', string="Customer Invoices")

    open_move_line_ids = fields.One2many(
        'account.payment.move.line', 'payment_id', string='Open Journal Entries')  # From other

    # For Manual Converted Rate - Version 12.0.6 - 12.0.7
    is_manual_converted_amount = fields.Boolean('Manual Converted Amount')  # From other
    manual_converted_amount = fields.Float('Converted Amount')  # From other

    @api.depends('bank_charge_currency_id', 'currency_id')
    def _compute_hide_bank_exch_rate_inv(self):
        for rec in self:
            rec.hide_bank_exch_rate_inv = not rec.bank_charge_currency_id or rec.bank_charge_currency_id == rec.env.user.company_id.currency_id

    @api.constrains('bank_charge_exch_rate_inv', 'bank_charge_currency_id', 'bank_charge_amount')
    def _check_bank_charge_exch_rate(self):
        if not self.hide_bank_exch_rate_inv and self.bank_charge_exch_rate_inv in [1.0, 0.0]:
            raise ValidationError('Exchange rate can not be 0.0 or 1.0')

    @api.onchange('bank_charge_exch_rate_inv', 'bank_charge_currency_id', 'bank_charge_amount')
    def _update_bank_company_curr_amount(self):
        amt = self.bank_charge_amount
        if not self.hide_bank_exch_rate_inv:
            amt *= self.bank_charge_exch_rate_inv
        self.bank_company_curr_amount = amt

    # For Refresh Invoice Lines - Version 12.0.7 - 12.0.8
    def action_refresh(self):
        # From Other
        #kashif 5mar24: dont make inv id false if it has no data already
        if self.invoice_ids:
            self.sudo().update({
                'invoice_ids':False
            })
        self._onchange_to_get_vendor_invoices()
        self._get_open_journal_entries()

#kashif 2 august 23: added code to get company currency amount in payment
    @api.onchange('amount')
    def _get_amount_rate(self):
        if self.company_id.currency_id != self.currency_id:
            self.is_manual_converted_amount = True
            self.manual_converted_amount = float_round(self.amount * self.exchange_rate_inverse,
                                                       2, rounding_method='HALF-UP')
    @api.onchange('currency_id')
    def _get_current_rate(self):
        super(AccountPayment, self)._get_current_rate()
        if self.company_id.currency_id == self.currency_id:
            self.is_manual_converted_amount = False
        else:
           self.is_manual_converted_amount = True
           self.manual_converted_amount = float_round(self.amount * self.exchange_rate_inverse,
                        2, rounding_method='HALF-UP')
#end
    @api.onchange('journal_id')
    def _get_default_bank_charge_account(self):
        journal = self.env['account.journal'].search(
            [('id', '=', self.journal_id.id)], limit=1)
        self.bank_charge_account_id = journal.bank_charge_account_id.id

    @api.onchange('partner_id', 'partner_type')
    def _get_open_journal_entries(self):
        try:
            self = self._origin
        except AttributeError:
            pass
        if not self:
            return
        for rec in self:
            self._cr.execute("ALTER TABLE account_payment_move_line DISABLE TRIGGER ALL;")
            self._cr.execute("DELETE FROM account_payment_move_line WHERE payment_id = " + str(rec.id))
            self._cr.execute("ALTER TABLE account_payment_move_line ENABLE TRIGGER ALL;")
            self._cr.execute("ALTER TABLE payment_move_line DISABLE TRIGGER ALL;")
            self._cr.execute("DELETE FROM payment_move_line WHERE payment_id = " + str(rec.id))
            self._cr.execute("ALTER TABLE payment_move_line ENABLE TRIGGER ALL;")
            if rec.partner_id and not rec.move_line_ids and (
                    rec.partner_id.property_account_receivable_id or rec.partner_id.property_account_payable_id):
                account_id = rec.partner_id.property_account_receivable_id.id if rec.partner_type == 'customer' \
                    else rec.partner_id.property_account_payable_id.id
                columns = 'date, move_id, journal_id, name, ref, partner_id, account_id, analytic_account_id, debit, credit, amount_currency, date_maturity, currency_id'
                columns2 = 'aml.date, aml.move_id, aml.journal_id, aml.name, aml.ref, aml.partner_id, aml.account_id, aml.analytic_account_id, aml.debit, aml.credit, aml.amount_currency, aml.date_maturity, aml.currency_id'
                query = f"""INSERT INTO account_payment_move_line (payment_id, {columns}) 
                    SELECT {rec.id} as x_payment_id, {columns2} FROM account_move_line aml
                    JOIN account_move am ON aml.move_id = am.id
                    JOIN account_journal aj ON aml.journal_id = aj.id
                    WHERE am.state = 'posted'
                    AND aml.amount_residual != 0
                    AND aml.partner_id = {rec.partner_id.id}
                    AND aml.account_id = {account_id}
                    AND aj.type NOT IN ('bank', 'cash')
                    """
                self._cr.execute(query)
            if rec.partner_id and rec.destination_account_id:
                query = f"""INSERT INTO payment_move_line (payment_id, move_line_id)
                                SELECT {rec.id} as x_payment_id, id FROM account_move_line
                                WHERE account_id = {rec.destination_account_id.id}
                                AND reconciled = FALSE
                                AND company_id = {rec.company_id.id}
                                AND partner_id = {rec.partner_id.id}
                                AND invoice_id IS NULL
                                AND payment_id IS NULL;"""
                self._cr.execute(query)
            self._cr.commit()
            for payment_move_line in rec.payment_move_line_ids:
                payment_move_line._calc_allocate_amount()

    @api.onchange('payment_type', 'partner_type', 'partner_id', 'currency_id')
    def _onchange_to_get_vendor_invoices(self):
        if self._context.get('no_insert_line'):
            # no need to insert any line when comes from register payment of invoice/CN
            return
        try:
            self = self._origin
        except AttributeError:
            pass
        if not self:
            return
        payment_id = self.id
        self._cr.execute("ALTER TABLE account_payment_invoice DISABLE TRIGGER ALL;")
        self._cr.execute(f"DELETE FROM account_payment_invoice WHERE payment_id = " + str(payment_id))
        self._cr.execute("ALTER TABLE account_payment_invoice ENABLE TRIGGER ALL;")
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id:
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
                'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])

            values = ', '.join([f'({payment_id}, {inv_id})' for inv_id in invoice_recs.ids])
            if invoice_recs.ids:
                query = "INSERT INTO account_payment_invoice (payment_id, invoice_id) VALUES " + values
                self._cr.execute(query)
        self._cr.commit()

    # kashif 26may23: added this method to update new invoice in lines
    def get_latest_invoices(self):
        self.update_invoice_lines()

        # kashif 26may23: added this method to update new invoice in lines
        # def update_invoice_lines(self):
        #     if self.payment_type in ['inbound',
        #                              'outbound'] and self.partner_type and self.partner_id and self.currency_id:
        #         if self.payment_type == 'inbound' and self.partner_type == 'customer':
        #             invoice_type = 'out_invoice'
        #         elif self.payment_type == 'outbound' and self.partner_type == 'customer':
        #             invoice_type = 'out_refund'
        #         elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
        #             invoice_type = 'in_invoice'
        #         else:
        #             invoice_type = 'in_refund'
        #         invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
        #             'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])
        #         # payment_invoice_values = [(5, 0, 0)]
        #         payment_invoice_values = []
        #         new_invoices = False
        #         if invoice_recs:
        #             new_invoices = invoice_recs.filtered(
        #                 lambda r: r.id not in self.payment_invoice_ids.mapped('invoice_id').ids)
        #             for invoice_rec in new_invoices:
        #                 payment_invoice_values.append(
        #                     [0, 0, {'invoice_id': invoice_rec.id}])
        #             if payment_invoice_values:
        #                 self.payment_invoice_ids = payment_invoice_values

        # end

    # kashif 26may23: added this method to update new invoice in lines
    def update_invoice_lines(self):
        #     return 0
        try:
            self = self._origin
        except AttributeError:
            pass
        if not self:
            return
        payment_id = self.id
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id:
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
                'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = []
            if invoice_recs:
                new_invoices = invoice_recs.filtered(
                    lambda r: r.id not in self.payment_invoice_ids.mapped('invoice_id').ids)
                if new_invoices:
                    values = ', '.join([f'({payment_id}, {inv_id})' for inv_id in new_invoices.ids])
                    query = "INSERT INTO account_payment_invoice (payment_id, invoice_id) VALUES " + values
                    self._cr.execute(query)
        self._cr.commit()

    # def update_invoice_lines(self):
    #     if self.payment_type in ['inbound',
    #                              'outbound'] and self.partner_type and self.partner_id and self.currency_id:
    #         if self.payment_type == 'inbound' and self.partner_type == 'customer':
    #             invoice_type = 'out_invoice'
    #         elif self.payment_type == 'outbound' and self.partner_type == 'customer':
    #             invoice_type = 'out_refund'
    #         elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
    #             invoice_type = 'in_invoice'
    #         else:
    #             invoice_type = 'in_refund'
    #         invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
    #             'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])
    #         # payment_invoice_values = [(5, 0, 0)]
    #         payment_invoice_values = []
    #         new_invoices = False
    #         if invoice_recs:
    #             new_invoices = invoice_recs.filtered(
    #                 lambda r: r.id not in self.payment_invoice_ids.mapped('invoice_id').ids)
    #             for invoice_rec in new_invoices:
    #                 payment_invoice_values.append(
    #                     [0, 0, {'invoice_id': invoice_rec.id}])
    #             if payment_invoice_values:
    #                 self.payment_invoice_ids = payment_invoice_values

    # end

    @api.depends('payment_move_line_ids.allocate_amount')
    def _calc_balance(self):
        for record in self:
            balance = 0
            for line in record.payment_move_line_ids:
                balance += line.allocate_amount * line.sign
            record.balance = balance

    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        res._onchange_to_get_vendor_invoices()
        res._get_open_journal_entries()
        return res

    # Kinjal's Update ---
    @api.multi
    def cancel(self):
        rec = super(AccountPayment, self).cancel()
        self.invoice_ids = False
        return rec

    # For Other
    def check_amount_for_other(self):
        for rec in self:
            # For Refresh Invoice Lines - Version 12.0.7 - 12.0.8
            invoice_name = ', '.join(str(iv.number) for iv in rec.invoice_ids.filtered(lambda x: x.state != 'open'))
            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoices %s is not open!") % (invoice_name))
            paym_inv = ', '.join(str(iv.invoice_id.number) for iv in rec.payment_invoice_ids.filtered(lambda x: x.residual < x.reconcile_amount))
            #if any(inv.residual < inv.reconcile_amount for inv in rec.payment_invoice_ids):
            for inv in rec.payment_invoice_ids:
                if inv.residual < inv.reconcile_amount:
                    #print('>>>>>>>>>>>check_amount_for_other residual=', inv.residual, ' , rec. amount=', inv.reconcile_amount)
                    raise ValidationError(_("There is reconcile amount is greater than amount due in Invoice Line -> %s!") % (inv.reconcile_amount))

    def check_amount_for_molicc(self):
        amount = 0.000
        recon_amount = 0.0
        if self.payment_invoice_ids:
            for payment_invoice_id in self.payment_invoice_ids:
                amount += payment_invoice_id.reconcile_amount
        if self.payment_move_line_ids:
            for payment_move_id in self.payment_move_line_ids:
                amount += payment_move_id.allocate_amount
        recon_amount += float_round(amount, 3, rounding_method='HALF-UP')
        #print('>>>>>>>>>>> check_amount_for_molicc=', recon_amount)
        #TS 28/9 - opening balance received extra payment
        # if self.amount < recon_amount:
        #     raise UserError(
        #         _("The sum of the reconcile amount of listed invoices are greater than payment's amount."))
        # Kinjal's Update ---
        if 'confirm' not in self._context:
            move_line_ids = False
            if self.payment_type == 'outbound':
                move_line_ids = self.move_line_ids.filtered(
                    lambda line: line.debit).ids
                for pay_inv in self.payment_invoice_ids.filtered(lambda y: y.invoice_id.move_id.line_ids.filtered(lambda x: x.credit)):
                    move_line_ids += pay_inv.invoice_id.move_id.line_ids.filtered(
                        lambda x: x.credit).ids
                move_line_ids += self.payment_move_line_ids.filtered(
                    lambda x: x.allocate_amount).mapped('move_line_id').ids
            if self.payment_type == 'inbound':
                move_line_ids = self.move_line_ids.filtered(
                    lambda line: line.credit).ids
                for pay_inv in self.payment_invoice_ids.filtered(lambda y: y.invoice_id.move_id.line_ids.filtered(lambda x: x.debit)):
                    move_line_ids += pay_inv.invoice_id.move_id.line_ids.filtered(
                        lambda x: x.debit).ids
                move_line_ids += self.payment_move_line_ids.filtered(
                    lambda x: x.allocate_amount).mapped('move_line_id').ids
            #print('>>>>>>>>>>> check_amount_for_molicc move_line_ids=', move_line_ids)
            move_line_ids = self.env['account.move.line'].browse(move_line_ids)
            debit_line_ids = move_line_ids.filtered(lambda line: line.debit)
            credit_line_ids = move_line_ids.filtered(lambda line: line.credit)
            if not debit_line_ids and not credit_line_ids:
                ctx = dict(
                    self._context,
                )
                return {
                    'name': 'Confirmation',
                    'type': 'ir.actions.act_window',
                    'res_model': 'confirmation.wiz',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': ctx
                }

    @api.multi
    def post(self):
        #print('>>>>>>>>>>>>>>>>> onepayment3 post')
        if self.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
            self.check_amount_for_molicc()
            #print('>>>>>>>>>>>>>>>>> onepayment3 post molicc')
        else:
            self.check_amount_for_other()
            #print('>>>>>>>>>>>>>>>>> onepayment3 post other')
        res = super(AccountPayment, self).post()
        if self.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
            # Kinjal's Update ---
            invoice_ids = self.payment_invoice_ids.filtered(
                lambda x: x.reconcile_amount).mapped('invoice_id')
            self.invoice_ids = [(6, 0, invoice_ids.ids or [])]
            #print('>>>>>>>>>>>>>>>>> onepayment3 post invoice_ids')
        return res

    # From Other
    @api.onchange('reference')
    def _onchange_reference(self):
        if self.reference:
            self.communication = self.reference

    def _create_payment_entry(self, amount):
        #print('>>>>>>>>>>>>>>>>> onepayment3 _create_payment_entry')
        if self.payment_move_line_ids.filtered(lambda x: x.allocate_amount):
            #print('>>>>>>>>>>>>>>>>> onepayment3 _create_payment_entry molicc')
            return self._create_payment_entry_for_molicc(amount)
        else:
            #print('>>>>>>>>>>>>>>>>> onepayment3 _create_payment_entry other')
            return self._create_payment_entry_for_other(amount)

    def _create_payment_entry_for_molicc(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
                    Return the journal entry.
                """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        # custom code by sitaram solutions start
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date,
                                                                           manual_rate=self.manual_currency_exchange_rate,
                                                                           active_manual_currency=self.apply_manual_currency_exchange, )._compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id)
        # For Manual Converted Rate - Version 12.0.6 - 12.0.7
        if self.is_manual_converted_amount:
            if amount < 0:
                credit = self.manual_converted_amount
            else:
                debit = self.manual_converted_amount

        # custom code by sitaram solutions end
        move = self.env['account.move'].create(self._get_move_vals())
        counterpart_aml_list = {}
        # Write line corresponding to invoice payment
        if self.payment_invoice_ids and self.payment_type == 'inbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and credit:
                        if self.currency_id and self.currency_id != self.company_currency_id and self.currency_id != payment_invoice_id.currency_id:
                            separate_amount_currency = -payment_invoice_id.reconcile_amount / self.exchange_rate_inverse
                            reconcile_amount = -payment_invoice_id.reconcile_amount
                        else:
                            reconcile_amount = (payment_invoice_id.reconcile_amount * credit) / amount_currency
                            separate_amount_currency = -payment_invoice_id.reconcile_amount
                        reconcile_amount = -reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, reconcile_amount,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if credit > float_round(total_reconcile_amount, 5, rounding_method='HALF-UP')\
                    and credit - total_reconcile_amount >= 0.1:  # to deny entry item creation of small calculation difference
                remaining_reconcile_amount = credit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and credit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, remaining_reconcile_amount,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        elif self.payment_invoice_ids and self.payment_type == 'outbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and debit:
                        if self.currency_id and self.currency_id != self.company_currency_id and self.currency_id != payment_invoice_id.currency_id:
                            separate_amount_currency = payment_invoice_id.reconcile_amount / self.exchange_rate_inverse
                            reconcile_amount = payment_invoice_id.reconcile_amount
                        else:
                            reconcile_amount = (payment_invoice_id.reconcile_amount * debit) / amount_currency
                            separate_amount_currency = payment_invoice_id.reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(reconcile_amount, credit,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if debit > float_round(total_reconcile_amount, 5, rounding_method='HALF-UP')\
                    and debit - total_reconcile_amount >= 0.1:
                remaining_reconcile_amount = debit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and debit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(remaining_reconcile_amount, credit,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        else:
            counterpart_aml_dict = self._get_shared_move_line_vals(
                debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(
                self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference and not self.payment_invoice_ids:
            writeoff_line = self._get_shared_move_line_vals(
                0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id,
                                                               self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        # Write counterpart lines
        # For Manual Converted Rate - Version 12.0.6 - 12.0.7
        amt = self.amount
        if self.is_manual_converted_amount:
            amt = self.manual_converted_amount
        if not self.currency_id.is_zero(amt):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0

            # if self.bank_charge_amount and self.bank_charge_account_id:
            #     debit_bc, credit_bc, amount_currency_bc, currency_id_bc = aml_obj.with_context(
            #         date=self.payment_date, manual_rate=self.manual_currency_exchange_rate, active_manual_currency=self.apply_manual_currency_exchange)._compute_amount_fields(self.bank_charge_amount, self.currency_id, self.company_id.currency_id)
            #     if credit:
            #         if debit_bc:
            #             credit -= debit_bc or credit_bc
            #         if credit_bc:
            #             credit += credit_bc or debit_bc
            #     if debit:
            #         if debit_bc:
            #             debit += debit_bc or credit_bc
            #         if credit_bc:
            #             debit -= credit_bc or debit_bc
            #     if amount_currency:
            #         amount_currency += amount_currency_bc or 0.0
            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit, debit, -amount_currency, move.id, False)
            # if amount:
            #     amount -= self.bank_charge_amount
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        if self.bank_charge_amount:
            if not self.bank_charge_account_id:
                raise UserError(_('Please select bank charge account!'))
            debit_bc, credit_bc, amount_currency_bc, currency_id_bc = aml_obj.with_context(
                date=self.payment_date,
                manual_rate=1 / (self.bank_charge_exch_rate_inv or 1),
                active_manual_currency=not self.hide_bank_exch_rate_inv
            )._compute_amount_fields(
                self.bank_charge_amount, self.bank_charge_currency_id, self.company_id.currency_id)

            self._prepare_bank_charge_gain_loss_entry_molicc(
                move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc)

            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit_bc, debit_bc, -amount_currency_bc, move.id, False)
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            if self.bank_charge_currency_id != self.company_currency_id:
                liquidity_aml_dict.update({
                    'amount_currency': -self.bank_charge_amount,
                    'currency_id': self.bank_charge_currency_id.id,
                    'journal_currency_rate': self.bank_charge_exch_rate_inv
                })
            else:
                liquidity_aml_dict.update({
                    'amount_currency': False,
                    'currency_id': False,
                    'journal_currency_rate': 1
                })
            aml_obj.create(liquidity_aml_dict)

        # validate the payment


        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            m_credit = float_round(
                sum(m_line.credit for m_line in move.line_ids.filtered(lambda x: x.credit)), 5, rounding_method='HALF-UP')
            m_debit = float_round(
                sum(m_line.debit for m_line in move.line_ids.filtered(lambda x: x.debit)), 5, rounding_method='HALF-UP')
            line_credit = move.line_ids.filtered(lambda x: x.credit)
            line_debit = move.line_ids.filtered(lambda x: x.debit)
            if self.payment_type == 'inbound' and line_credit:
                if m_credit > m_debit:
                    line_credit[0].credit -= m_credit - m_debit
                elif m_debit > m_credit:
                    line_credit[0].credit += m_debit - m_credit
            if self.payment_type == 'outbound' and line_debit:
                if m_credit > m_debit:
                    line_debit[0].debit += m_credit - m_debit
                elif m_debit > m_credit:
                    line_debit[0].debit -= m_debit - m_credit
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        if self.payment_invoice_ids and self.payment_type in ['inbound', 'outbound']:
            invoice_ids = []
            for counterpart_aml_list_itr in counterpart_aml_list.keys():
                invoice_obj = self.env['account.invoice'].browse(
                    [counterpart_aml_list_itr])
                invoice_ids.append(counterpart_aml_list_itr)
                invoice_obj.register_payment(
                    counterpart_aml_list[counterpart_aml_list_itr])
            self.invoice_ids = [(6, 0, invoice_ids)]
        else:
            self.invoice_ids.register_payment(counterpart_aml)
        self.check_invoice_line()
        return move

    def _create_payment_entry_for_other(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
                    Return the journal entry.
                """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        # debit, credit, amount_currency, currency_id = aml_obj.with_context(
        #     date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        # custom code by sitaram solutions start
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date,
                                                                           manual_rate=self.manual_currency_exchange_rate,
                                                                           active_manual_currency=self.apply_manual_currency_exchange, )._compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id)
        # For Manual Converted Rate - Version 12.0.6 - 12.0.7
        if self.is_manual_converted_amount:
            if amount < 0:
                credit = self.manual_converted_amount
            else:
                debit = self.manual_converted_amount

        # custom code by sitaram solutions end
        move = self.env['account.move'].create(self._get_move_vals())
        counterpart_aml_list = {}
        # Write line corresponding to invoice payment
        if self.payment_invoice_ids and self.payment_type == 'inbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and credit:
                        if self.currency_id and self.currency_id != self.company_currency_id and self.currency_id != payment_invoice_id.currency_id:
                            separate_amount_currency = -payment_invoice_id.reconcile_amount / self.exchange_rate_inverse
                            reconcile_amount = -payment_invoice_id.reconcile_amount
                        else:
                            reconcile_amount = (payment_invoice_id.reconcile_amount * credit) / amount_currency
                            separate_amount_currency = -payment_invoice_id.reconcile_amount
                        reconcile_amount = -reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, reconcile_amount,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if credit > float_round(total_reconcile_amount, 5, rounding_method='HALF-UP')\
                    and credit - total_reconcile_amount >= 0.1:  # to deny entry item creation of small calculation difference
                remaining_reconcile_amount = credit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and credit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, remaining_reconcile_amount,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        elif self.payment_invoice_ids and self.payment_type == 'outbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and debit:
                        if self.currency_id and self.currency_id != self.company_currency_id and self.currency_id != payment_invoice_id.currency_id:
                            separate_amount_currency = payment_invoice_id.reconcile_amount / self.exchange_rate_inverse
                            reconcile_amount = payment_invoice_id.reconcile_amount
                        else:
                            reconcile_amount = (payment_invoice_id.reconcile_amount * debit) / amount_currency
                            separate_amount_currency = payment_invoice_id.reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(reconcile_amount, credit,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if debit > float_round(total_reconcile_amount, 5, rounding_method='HALF-UP')\
                    and debit - total_reconcile_amount >= 0.1:
                remaining_reconcile_amount = debit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and debit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(remaining_reconcile_amount, credit,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        else:
            counterpart_aml_dict = self._get_shared_move_line_vals(
                debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(
                self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference and not self.payment_invoice_ids:
            writeoff_line = self._get_shared_move_line_vals(
                0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id,
                                                               self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        # Write counterpart lines
        # For Manual Converted Rate - Version 12.0.6 - 12.0.7
        amt = self.amount
        if self.is_manual_converted_amount:
            amt = self.manual_converted_amount
        if not self.currency_id.is_zero(amt):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0

            # if self.bank_charge_amount and self.bank_charge_account_id:
            #     debit_bc, credit_bc, amount_currency_bc, currency_id_bc = aml_obj.with_context(
            #         date=self.payment_date, manual_rate=self.manual_currency_exchange_rate, active_manual_currency=self.apply_manual_currency_exchange)._compute_amount_fields(self.bank_charge_amount, self.currency_id, self.company_id.currency_id)
            #
            #     if credit:
            #         if debit_bc:
            #             credit -= debit_bc or credit_bc
            #         if credit_bc:
            #             credit += credit_bc or debit_bc
            #     if debit:
            #         if debit_bc:
            #             debit += debit_bc or credit_bc
            #         if credit_bc:
            #             debit -= credit_bc or debit_bc
            #     if amount_currency:
            #         amount_currency += amount_currency_bc or 0.0
            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit, debit, -amount_currency, move.id, False)
            # if amount:
            #     amount -= self.bank_charge_amount
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        if self.bank_charge_amount:
            if not self.bank_charge_account_id:
                raise UserError(_('Please select bank charge account!'))
            debit_bc, credit_bc, amount_currency_bc, currency_id_bc = aml_obj.with_context(
                date=self.payment_date,
                manual_rate=1 / (self.bank_charge_exch_rate_inv or 1),
                active_manual_currency=not self.hide_bank_exch_rate_inv
            )._compute_amount_fields(
                self.bank_charge_amount, self.bank_charge_currency_id, self.company_id.currency_id)

            self._prepare_bank_charge_gain_loss_entry_other(
                move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc)

            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit_bc, debit_bc, -amount_currency_bc, move.id, False)
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            if self.bank_charge_currency_id != self.company_currency_id:
                liquidity_aml_dict.update({
                    'amount_currency': -self.bank_charge_amount,
                    'currency_id': self.bank_charge_currency_id.id,
                    'journal_currency_rate': self.bank_charge_exch_rate_inv
                })
            else:
                liquidity_aml_dict.update({
                    'amount_currency': False,
                    'currency_id': False,
                    'journal_currency_rate': 1
                })
            aml_obj.create(liquidity_aml_dict)

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            m_credit = float_round(
                sum(m_line.credit for m_line in move.line_ids.filtered(lambda x: x.credit)), 5, rounding_method='HALF-UP')
            m_debit = float_round(
                sum(m_line.debit for m_line in move.line_ids.filtered(lambda x: x.debit)), 5, rounding_method='HALF-UP')
            line_credit = move.line_ids.filtered(lambda x: x.credit)
            line_debit = move.line_ids.filtered(lambda x: x.debit)
            if self.payment_type == 'inbound' and line_credit:
                if m_credit > m_debit:
                    line_credit[0].credit -= m_credit - m_debit
                elif m_debit > m_credit:
                    line_credit[0].credit += m_debit - m_credit
            if self.payment_type == 'outbound' and line_debit:
                if m_credit > m_debit:
                    line_debit[0].debit += m_credit - m_debit
                elif m_debit > m_credit:
                    line_debit[0].debit -= m_debit - m_credit
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        if self.payment_invoice_ids and self.payment_type in ['inbound', 'outbound']:
            invoice_ids = []
            for counterpart_aml_list_itr in counterpart_aml_list.keys():
                invoice_obj = self.env['account.invoice'].browse(
                    [counterpart_aml_list_itr])
                invoice_ids.append(counterpart_aml_list_itr)
                invoice_obj.register_payment(
                    counterpart_aml_list[counterpart_aml_list_itr])
            self.invoice_ids = [(6, 0, invoice_ids)]
        else:
            self.invoice_ids.register_payment(counterpart_aml)

        return move

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        res = super(AccountPayment, self)._get_shared_move_line_vals(debit, credit, amount_currency, move_id, invoice_id)
        res['journal_currency_rate'] = self.exchange_rate_inverse
        return res

    # Kinjal's Update ---
    def check_invoice_line(self):
        move_line_ids = False
        if self.payment_type == 'outbound':
            move_line_ids = self.move_line_ids.filtered(
                lambda line: line.debit and not line.full_reconcile_id and not line.payment_invoice_id).ids
            move_line_ids += self.payment_move_line_ids.filtered(
                lambda x: x.allocate_amount).mapped('move_line_id').ids
        if self.payment_type == 'inbound':
            move_line_ids = self.move_line_ids.filtered(
                lambda line: line.credit and not line.full_reconcile_id and not line.payment_invoice_id).ids
            move_line_ids += self.payment_move_line_ids.filtered(
                lambda x: x.allocate_amount).mapped('move_line_id').ids
        move_line_ids = self.env['account.move.line'].browse(move_line_ids)
        #print ("move_line_idsmove_line_ids", move_line_ids)
        debit_line_ids = move_line_ids.filtered(lambda line: line.debit)
        credit_line_ids = move_line_ids.filtered(lambda line: line.credit)
        #print ("debit_line_ids", debit_line_ids)
        #print ("credit_line_ids", credit_line_ids)
        if debit_line_ids and credit_line_ids:
            max_date = self.payment_date or max(move_line_ids.mapped(
                'date') or [fields.Date.today()])
            partner_ids = move_line_ids.mapped('partner_id')
            partner_balance = False
            if len(partner_ids) > 1:
                partner_balance = dict.fromkeys(partner_ids.ids, 0)
            partial_reconcile_ids = self.env["account.partial.reconcile"]
            line_currency_diff = {}
            if self.payment_type == 'outbound':
                for debit_line in debit_line_ids:
                    for credit_line in credit_line_ids:
                        credit_allocate_amount = self.payment_move_line_ids.filtered(
                            lambda x: x.move_line_id.id == credit_line.id).allocate_amount
                        if debit_line.currency_id != credit_line.currency_id:
                            debit_allocate_amount = self.amount * self.exchange_rate_inverse
                        else:
                            debit_allocate_amount = self.amount

                        allocate_amount = min(
                            abs(debit_allocate_amount), abs(credit_allocate_amount))
                        if not allocate_amount:
                            continue
                        vals = {
                            'debit_move_id': debit_line.id,
                            'credit_move_id': credit_line.id,
                        }

                        if self.currency_id != self.company_id.currency_id:
                            vals.update({
                                'currency_id': self.currency_id.id,
                                'amount_currency': allocate_amount,
                                'amount': self.currency_id._convert(allocate_amount, self.company_id.currency_id, self.company_id, max_date)
                            })

                            if self._context.get('active_model') == 'account.netting':
                                if debit_line.payment_id and debit_line.currency_id != credit_line.currency_id:
                                    vals['amount_currency'] = allocate_amount / self.exchange_rate_inverse
                                else:
                                    vals['amount'] = allocate_amount * self.exchange_rate_inverse

                            for line, sign in [(debit_line, 1), (credit_line, -1)]:
                                if allocate_amount == line.amount_residual:
                                    amount = line.amount_residual * sign
                                    if abs(amount - vals['amount']) < 1:
                                        vals['amount'] = amount
                                        break
                            for line, sign in [(debit_line, 1), (credit_line, -1)]:
                                if line.amount_currency:
                                    rate = line.amount_currency / line.balance
                                    old_amount = vals['amount_currency'] / rate
                                    diff_amount = self.company_id.currency_id.round(
                                        (old_amount - vals['amount']) * sign)
                                    line_currency_diff[line] = diff_amount
                        else:
                            vals.update({
                                'amount': allocate_amount
                            })

                        if debit_line.amount_currency and credit_line.amount_currency and debit_line.currency_id == credit_line.currency_id and 'amount_currency' not in vals:
                            company_id = debit_line.company_id
                            vals.update({
                                'currency_id': debit_line.currency_id.id,
                                'amount_currency': company_id.currency_id._convert(allocate_amount, debit_line.currency_id, company_id, max_date)
                            })

                        if self._context.get('active_model') == 'account.netting':
                            partial_reconcile_ids += self.env["account.partial.reconcile"].with_context(stop_forex_entry_creation=True).create(vals)
                        else:
                            partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)
                        if partner_balance:
                            partner_balance[debit_line.partner_id.id] += allocate_amount
                            partner_balance[credit_line.partner_id.id] -= allocate_amount

                        debit_allocate_amount -= allocate_amount * \
                            (debit_allocate_amount < 0 and -1 or 1)
                        credit_allocate_amount -= allocate_amount * \
                            (credit_allocate_amount < 0 and -1 or 1)

            if self.payment_type == 'inbound':
                for credit_line in credit_line_ids:
                    for debit_line in debit_line_ids:
                        debit_allocate_amount = self.payment_move_line_ids.filtered(
                            lambda x: x.move_line_id.id == debit_line.id).allocate_amount
                        if debit_line.currency_id != credit_line.currency_id:
                            credit_allocate_amount = self.amount * self.exchange_rate_inverse
                        else:
                            credit_allocate_amount = self.amount
                        allocate_amount = min(
                            abs(debit_allocate_amount), abs(credit_allocate_amount))
                        if not allocate_amount:
                            continue
                        vals = {
                            'debit_move_id': debit_line.id,
                            'credit_move_id': credit_line.id,
                        }

                        if self.currency_id != self.company_id.currency_id:
                            vals.update({
                                'currency_id': self.currency_id.id,
                                'amount_currency': allocate_amount,
                                'amount': self.company_id.currency_id._convert(allocate_amount, self.currency_id, self.company_id, max_date)
                                # 'amount': self.currency_id._convert(allocate_amount, self.company_id.currency_id, self.company_id, max_date)
                            })
                            if self._context.get('active_model') == 'account.netting':
                                if credit_line.payment_id and credit_line.currency_id != debit_line.currency_id:
                                    vals['amount_currency'] = allocate_amount / self.exchange_rate_inverse
                                else:
                                    vals['amount'] = allocate_amount * self.exchange_rate_inverse

                            for line, sign in [(debit_line, 1), (credit_line, -1)]:
                                if allocate_amount == line.amount_residual:
                                    amount = line.amount_residual * sign
                                    if abs(amount - vals['amount']) < 1:
                                        vals['amount'] = amount
                                        break
                            for line, sign in [(debit_line, 1), (credit_line, -1)]:
                                if line.amount_currency:
                                    rate = line.amount_currency / line.balance
                                    old_amount = vals['amount_currency'] / rate
                                    diff_amount = self.company_id.currency_id.round(
                                        (old_amount - vals['amount']) * sign)
                                    line_currency_diff[line] = diff_amount
                        else:
                            vals.update({
                                'amount': allocate_amount
                            })

                        if debit_line.amount_currency and credit_line.amount_currency and debit_line.currency_id == credit_line.currency_id and 'amount_currency' not in vals:
                            company_id = debit_line.company_id
                            vals.update({
                                'currency_id': debit_line.currency_id.id,
                                'amount_currency': company_id.currency_id._convert(allocate_amount, debit_line.currency_id, company_id, max_date)
                            })
                        if self._context.get('active_model') == 'account.netting':
                            partial_reconcile_ids += self.env["account.partial.reconcile"].with_context(stop_forex_entry_creation=True).create(vals)
                        else:
                            partial_reconcile_ids += self.env["account.partial.reconcile"].create(vals)
                        if partner_balance:
                            partner_balance[debit_line.partner_id.id] += allocate_amount
                            partner_balance[credit_line.partner_id.id] -= allocate_amount

                        debit_allocate_amount -= allocate_amount * \
                            (debit_allocate_amount < 0 and -1 or 1)
                        credit_allocate_amount -= allocate_amount * \
                            (credit_allocate_amount < 0 and -1 or 1)
            exchange_lines = []
            exchange_move = self.env['account.move']
            exchange_partial_reconcile = self.env["account.partial.reconcile"]
            exchange_lines_to_rec = self.env['account.move.line']
            for move_line in move_line_ids:
                if not move_line.amount_currency:
                    continue
                if not move_line.amount_residual_currency and not move_line.amount_residual:
                    continue
                if not move_line.amount_residual_currency and move_line.amount_residual:
                    amount = move_line.amount_residual
                elif move_line in line_currency_diff:
                    amount = line_currency_diff[move_line]
                else:
                    amount = move_line.amount_residual - move_line.currency_id._convert(
                        move_line.amount_residual_currency, self.company_id.currency_id, self.company_id, max_date)
                amount = self.company_id.currency_id.round(amount)
                if amount:
                    exchange_lines.append((move_line, amount))
            if exchange_lines:
                exchange_move = self.env['account.move'].create(
                    self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=max_date, company=self.company_id))
                exchange_journal = exchange_move.journal_id
                for move_line, amount in exchange_lines:
                    line_to_rec = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'name': _('Currency exchange rate difference'),
                        'debit': -amount if amount < 0 else 0,
                        'credit': amount if amount > 0 else 0,
                        'date': self.payment_date,  # 3.0.0.3
                        'account_id': move_line.account_id.id,
                        'move_id': exchange_move.id,
                        'partner_id': move_line.partner_id.id,
                        'amount_currency': 0,
                        'currency_id': move_line.currency_id.id
                    })
                    account_id = amount > 0 and exchange_journal.default_debit_account_id.id or exchange_journal.default_credit_account_id.id
                    if "currency.exchange.account" in self.env:
                        curency_exchange_account_id = self.env['currency.exchange.account'].search(
                            [('currency_id', '=', move_line.currency_id.id), ('journal_id', '=', exchange_journal.id)])
                        if curency_exchange_account_id.account_id:
                            account_id = curency_exchange_account_id.account_id.id

                    exchange_lines_to_rec += line_to_rec
                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'name': _('Currency exchange rate difference'),
                        'debit': amount if amount > 0 else 0,
                        'credit': -amount if amount < 0 else 0,
                        'account_id': account_id,
                        'date': self.payment_date,  # 3.0.0.3
                        'move_id': exchange_move.id,
                        'partner_id': move_line.partner_id.id,
                        'amount_currency': 0,
                        'currency_id': move_line.currency_id.id
                    })
                    exchange_partial_vals = {
                        'debit_move_id': line_to_rec.id if line_to_rec.debit else move_line.id,
                        'credit_move_id': line_to_rec.id if line_to_rec.credit else move_line.id,
                        'amount': abs(amount),
                        'amount_currency': 0,
                        'currency_id': move_line.currency_id.id
                    }
                    if (move_line.id == exchange_partial_vals['debit_move_id'] and move_line.credit) or (move_line.id == exchange_partial_vals['credit_move_id'] and move_line.debit):
                        exchange_partial_vals.update({
                            'amount': -exchange_partial_vals['amount'],
                            'debit_move_id': exchange_partial_vals['credit_move_id'],
                            'credit_move_id': exchange_partial_vals['debit_move_id']
                        })

                    exchange_partial_reconcile += self.env["account.partial.reconcile"].create(
                        exchange_partial_vals)
                exchange_move.post()
            reconciled_move_line_ids = move_line_ids.filtered(
                'reconciled') + exchange_lines_to_rec
            if reconciled_move_line_ids:
                partial_reconcile_ids = partial_reconcile_ids.filtered(
                    lambda record: record.debit_move_id in reconciled_move_line_ids or record.credit_move_id in reconciled_move_line_ids) + exchange_partial_reconcile
                self.env["account.full.reconcile"].create({
                    'partial_reconcile_ids': [(6, 0, partial_reconcile_ids.ids)],
                    'reconciled_line_ids': [(6, 0, reconciled_move_line_ids.ids)],
                    'exchange_move_id': exchange_move.id
                })

            if partner_balance:
                move_vals = {
                    'journal_id': self.journal_id.id,
                    'ref': self.reference,
                    'date': max_date,
                    'line_ids': []
                }
                for partner_id, balance in partner_balance.items():
                    if not balance:
                        continue

                    if self.currency_id != self.company_id.currency_id:
                        currency_id = self.currency_id.id
                        amount_currency = balance
                        balance = self.currency_id._convert(
                            amount_currency, self.company_id.currency_id, self.company_id, max_date)
                    else:
                        currency_id = False
                        amount_currency = False
                    move_vals['line_ids'].append((0, 0, {
                        'account_id': self.account_id.id,
                        'name': '',
                        'partner_id': partner_id,
                        'credit': balance > 0 and balance or 0,
                        'debit': balance < 0 and -balance or 0,
                        'currency_id': currency_id,
                        'amount_currency': amount_currency
                    }))
                move_id = self.env['account.move'].create(move_vals)
                move_id.post()
                move_id.line_ids.reconcile()
                move_line_ids += move_id.line_ids

    def _prepare_bank_charge_gain_loss_entry_molicc(self, move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc):
        partner_id = False
        if self.payment_type in ('inbound', 'outbound'):
            partner_id = self.env['res.partner']._find_accounting_partner(
                self.partner_id).id
        account_id = self.bank_charge_account_id.id
        bank_entry_dict = {
            'account_id': account_id,
            'partner_id': partner_id or False,
            'date': self.payment_date,  # 3.0.0.3
            'company_id': self.company_id.id,
            'amount_currency': amount_currency_bc or False,
            'currency_id': currency_id_bc,
            'name': self._get_counterpart_move_line_vals(self.invoice_ids).get('name'),
            'payment_id': self.id,
            'journal_currency_rate': self.bank_charge_exch_rate_inv
        }
        if debit_bc:
            bank_entry_dict['debit'] = debit_bc
        if credit_bc:
            bank_entry_dict['credit'] = credit_bc
        move.line_ids = [(0, 0, bank_entry_dict)]

    def _prepare_bank_charge_gain_loss_entry_other(self, move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc):
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        partner_id = False
        if self.payment_type in ('inbound', 'outbound'):
            partner_id = self.env['res.partner']._find_accounting_partner(
                self.partner_id).id
        account_id = self.bank_charge_account_id.id
        bank_entry_dict = {
            'account_id': account_id,
            'partner_id': partner_id or False,
            'date': self.payment_date,  # 3.0.0.3
            'company_id': self.company_id.id,
            'amount_currency': amount_currency_bc or False,
            'currency_id': currency_id_bc,
            'name': self._get_counterpart_move_line_vals(self.invoice_ids).get('name'),
            'payment_id': self.id,
            'move_id': move.id,
            'journal_currency_rate': self.bank_charge_exch_rate_inv
        }
        if debit_bc:
            bank_entry_dict['debit'] = debit_bc
        if credit_bc:
            bank_entry_dict['credit'] = credit_bc
        aml_obj.create(bank_entry_dict)
        # move.line_ids = [(0, 0, bank_entry_dict)]

    # Ahmad Zaman - 28/05/24 - Added validation if exchange rate's 0 or 1
    @api.multi
    def post_vendor_payment(self):
        exchange_rate = self.exchange_rate_inverse
        foreign_currency = False
        if self.currency_id != self.company_id.currency_id:
            foreign_currency = True
        if foreign_currency and (exchange_rate == 0 or exchange_rate == 1):
            raise ValidationError(f"The Exchange Rate cannot be 0.00 or 1.00.")
        return super(AccountPayment, self).post_vendor_payment()
    # end


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    last_payment_date = fields.Date(string="Payment Date", readonly=True)

    def action_register_payment(self):
        if (self.type or '').startswith('in_'):
            act_ref = 'account.action_account_payments_payable'
        else:
            act_ref = 'account.action_account_payments'
        [action] = self.env.ref(act_ref).read(['context'])
        ctx = eval(action['context'])
        ctx.update({
            'no_insert_line': True,
            'default_partner_id': self.partner_id.id,
            'default_currency_id': self.currency_id.id,
            'default_amount': self.residual,
            'default_payment_invoice_ids': [[0, 0, {
                'invoice_id': self.id,
                'reconcile_amount': self.residual,
                'fully_reconcile': True,
                'origin': self.origin,
                'date_invoice': self.date_invoice,
                'date_due': self.date_due,
                'amount_total': self.amount_total,
                'residual': self.residual,
                'reference': self.reference,
            }]]
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'res_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'current',
            'context': ctx
        }




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payment_invoice_id = fields.Many2one('account.payment.invoice')

    @api.multi
    def _update_check(self):
        """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
        move_ids = set()
        for line in self:
            err_msg = _('Move name (id): %s (%s)') % (
                line.move_id.name, str(line.move_id.id))
            if line.move_id.state != 'draft':
                raise UserError(
                    _('You cannot do this modification on a posted journal entry, you can just change some non legal fields. You must revert the journal entry to cancel it.\n%s.') % err_msg)
            if line.reconciled and not (line.debit == 0 and line.credit == 0):
                if line.invoice_id:
                    raise UserError(
                        _('You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
                else:
                    line.remove_move_reconcile()
            if line.move_id.id not in move_ids:
                move_ids.add(line.move_id.id)
        self.env['account.move'].browse(list(move_ids))._check_lock_date()
        return True

    @api.multi
    def unlink(self):
        self._update_check()
        move_ids = set()
        for line in self:
            if line.move_id.id not in move_ids:
                move_ids.add(line.move_id.id)
        recon = self.env['account.partial.reconcile'].search(
            ['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)])
        if recon:
            recon.unlink()
        result = super(AccountMoveLine, self).unlink()
        if self._context.get('check_move_validity', True) and move_ids:
            self.env['account.move'].browse(list(move_ids))._post_validate()
        return result

    #  Version - 12.3.0.0.4 - Exchange rate Entry Date Should be Payment Date 
    @api.multi
    def check_full_reconcile(self):
        """
        This method check if a move is totally reconciled and if we need to create exchange rate entries for the move.
        In case exchange rate entries needs to be created, one will be created per currency present.
        In case of full reconciliation, all moves belonging to the reconciliation will belong to the same account_full_reconcile object.
        """
        # Get first all aml involved
        todo = self.env['account.partial.reconcile'].search_read(['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)], ['debit_move_id', 'credit_move_id'])
        amls = set(self.ids)
        #print('>>>>> check_full_reconcile 1 amls=', amls)
        seen = set()
        while todo:
            aml_ids = [rec['debit_move_id'][0] for rec in todo if rec['debit_move_id']] + [rec['credit_move_id'][0] for rec in todo if rec['credit_move_id']]
            amls |= set(aml_ids)
            seen |= set([rec['id'] for rec in todo])
            todo = self.env['account.partial.reconcile'].search_read(['&', '|', ('credit_move_id', 'in', aml_ids), ('debit_move_id', 'in', aml_ids), '!', ('id', 'in', list(seen))], ['debit_move_id', 'credit_move_id'])

        partial_rec_ids = list(seen)
        if not amls:
            return
        else:
            amls = self.browse(list(amls))
        #print('>>>>> check_full_reconcile 2 amls=', amls)
        # If we have multiple currency, we can only base ourselve on debit-credit to see if it is fully reconciled
        currency = set([a.currency_id for a in amls if a.currency_id.id != False])
        multiple_currency = False
        if len(currency) != 1:
            currency = False
            multiple_currency = True
        else:
            currency = list(currency)[0]
        # Get the sum(debit, credit, amount_currency) of all amls involved
        total_debit = 0
        total_credit = 0
        total_amount_currency = 0
        maxdate = date.min
        to_balance = {}
        cash_basis_partial = self.env['account.partial.reconcile']
        #Added by kinjal
        payment_ml_id = amls.filtered(lambda x: x.payment_id)
        payment_id = payment_ml_id[0].payment_id if payment_ml_id else False
        ### -- end ##
        for aml in amls:
            cash_basis_partial |= aml.move_id.tax_cash_basis_rec_id
            total_debit += aml.debit
            total_credit += aml.credit
            maxdate = max(aml.date, maxdate)
            #print('>>>>> check_full_reconcile 1 maxdate=', maxdate, '   VS aml.date=', aml.date)
            total_amount_currency += aml.amount_currency
            # Convert in currency if we only have one currency and no amount_currency
            if not aml.amount_currency and currency:
                multiple_currency = True
                total_amount_currency += aml.company_id.currency_id._convert(aml.balance, currency, aml.company_id, aml.date)
            # If we still have residual value, it means that this move might need to be balanced using an exchange rate entry
            if aml.amount_residual != 0 or aml.amount_residual_currency != 0:
                if not to_balance.get(aml.currency_id):
                    to_balance[aml.currency_id] = [self.env['account.move.line'], 0]
                to_balance[aml.currency_id][0] += aml
                to_balance[aml.currency_id][1] += aml.amount_residual != 0 and aml.amount_residual or aml.amount_residual_currency

        # Check if reconciliation is total
        # To check if reconciliation is total we have 3 differents use case:
        # 1) There are multiple currency different than company currency, in that case we check using debit-credit
        # 2) We only have one currency which is different than company currency, in that case we check using amount_currency
        # 3) We have only one currency and some entries that don't have a secundary currency, in that case we check debit-credit
        #   or amount_currency.
        # 4) Cash basis full reconciliation
        #     - either none of the moves are cash basis reconciled, and we proceed
        #     - or some moves are cash basis reconciled and we make sure they are all fully reconciled

        digits_rounding_precision = amls[0].company_id.currency_id.rounding
        #Added by kinjal
        caba_reconciled_amls = cash_basis_partial.mapped('debit_move_id') + cash_basis_partial.mapped('credit_move_id')
        caba_connected_amls = amls.filtered(lambda x: x.move_id.tax_cash_basis_rec_id) + caba_reconciled_amls
        matched_percentages = caba_connected_amls._get_matched_percentage()
        #####
        if (
                (all(amls.mapped('tax_exigible')) or all(matched_percentages[aml.move_id.id] >= 1.0 for aml in caba_connected_amls))
                and
                (
                    currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding) or
                    multiple_currency and float_compare(total_debit, total_credit, precision_rounding=digits_rounding_precision) == 0
                )
        ):

            exchange_move_id = False
            # Eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
            if to_balance and any([not float_is_zero(residual, precision_rounding=digits_rounding_precision) for aml, residual in to_balance.values()]):
                #Added by kinjal
                maxdate = payment_id.payment_date if payment_id else maxdate
                #print('>>>>> check_full_reconcile 2 maxdate=', maxdate)
                #####
                exchange_move = self.env['account.move'].create(
                    self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=maxdate, company=amls[0].company_id))
                part_reconcile = self.env['account.partial.reconcile']
                for aml_to_balance, total in to_balance.values():
                    if total:
                        rate_diff_amls, rate_diff_partial_rec = part_reconcile.create_exchange_rate_entry(aml_to_balance, exchange_move)
                        amls += rate_diff_amls
                        partial_rec_ids += rate_diff_partial_rec.ids
                    else:
                        aml_to_balance.reconcile()
                exchange_move.post()
                exchange_move_id = exchange_move.id
            #mark the reference of the full reconciliation on the exchange rate entries and on the entries
            self.env['account.full.reconcile'].create({
                'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
                'reconciled_line_ids': [(6, 0, amls.ids)],
                'exchange_move_id': exchange_move_id,
            })
