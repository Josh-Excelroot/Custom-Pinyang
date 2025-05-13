# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models
from odoo.exceptions import UserError


class GenerateOpeningEntries(models.TransientModel):
    _name = 'generate.opening.entries'
    _description = "Generate Opening Entries"

    name = fields.Char("Name of new entries", required=True, default='End of Fiscal Year Entry')
    old_fiscal_year_id = fields.Many2one('account.fiscal.year', string="Fiscal Year to close", required=True)
    new_fiscal_year_id = fields.Many2one('account.fiscal.year', string="New Fiscal Year", required=True)
    journal_id = fields.Many2one('account.journal', string="Opening Entries Journal", required=True, domain=[('type', '=', 'opening')])
    period_id = fields.Many2one('account.period.part', string="Opening Entries Period", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    def data_save(self):
        """
        This function close account fiscalyear and create entries in new fiscalyear
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Account fiscalyear close state’s IDs

        """
        obj_acc_move = self.env['account.move']
        obj_acc_move_line = self.env['account.move.line']
        total_debit = 0.0
        total_credit = 0.0

        self._cr.execute("SELECT id FROM account_period_part WHERE date_to < (SELECT date_from FROM account_fiscal_year WHERE id = %s)", (str(self.new_fiscal_year_id.id),))
        fy_period_set = ','.join(map(lambda id: str(id[0]), self._cr.fetchall()))
        self._cr.execute("SELECT id FROM account_period_part WHERE date_from > (SELECT date_to FROM account_fiscal_year WHERE id = %s)", (str(self.old_fiscal_year_id.id),))
        fy2_period_set = ','.join(map(lambda id: str(id[0]), self._cr.fetchall()))

        if not fy_period_set or not fy2_period_set:
            raise UserError('The periods to generate opening entries cannot be found.')

        period = self.period_id
        new_fyear = self.new_fiscal_year_id
        old_fyear = self.old_fiscal_year_id

        new_journal = self.journal_id
        company_id = self.journal_id.company_id.id

        if not new_journal.default_credit_account_id or not new_journal.default_debit_account_id:
            raise UserError('The journal must have default credit and debit account.')

        # delete existing move and move lines if any
        move_ids = obj_acc_move.search([('journal_id', '=', new_journal.id), ('period_id', '=', period.id)])

        if move_ids:
            move_line_ids = obj_acc_move_line.search([('move_id', 'in', move_ids.ids)])
#             obj_acc_move_line._remove_move_reconcile(cr, uid, move_line_ids, opening_reconciliation=True, context=context)
            move_line_ids.unlink()
            move_ids.unlink()

        self._cr.execute("SELECT id FROM account_fiscal_year WHERE date_to < %s", (str(new_fyear.date_from),))
        result = self._cr.dictfetchall()
        fy_ids = [x['id'] for x in result]
        query_line = '''account_move_line.period_id IN (SELECT id FROM account_period_part WHERE fiscal_year_id = %s)''' % (fy_ids[-1])

#
        # create the opening move
        vals = {
            'name': '/',
            'ref': 'Opening Balance Entry',
            'period_id': period.id,
            'date': period.date_from,
            'journal_id': new_journal.id,
        }
        move_id = obj_acc_move.create(vals)

        # 1. report of the accounts with defferal method == 'unreconciled'
        self._cr.execute('''
            SELECT a.id
            FROM account_account a
            LEFT JOIN account_account_type t ON (a.user_type_id = t.id)
            WHERE a.company_id = %s
              AND a.reconcile = %s''', (company_id, True, ))
        account_ids = [res[0] for res in self._cr.fetchall()]

        if account_ids:
            try:
                # move_line = self.env['account.move.line'].search([('account_id', 'in', account_ids)])
                self._cr.execute('''
                    INSERT INTO account_move_line (
                         name, create_uid, create_date, write_uid, write_date,
                          journal_id, currency_id, date_maturity,
                         partner_id, blocked,credit,  debit,
                         ref, account_id, period_id, date, move_id, amount_currency,
                         quantity, product_id, company_id)
                      (SELECT name, create_uid, create_date, write_uid, write_date,
                         %s,currency_id, date_maturity, partner_id,blocked,
                         credit, debit, ref, account_id,
                         %s, (%s) AS date, %s, amount_currency, quantity, product_id, company_id
                       FROM account_move_line
                       WHERE account_id IN %s AND reconciled IS False
                         AND ''' + query_line + ''')''', (new_journal.id, period.id, period.date_from, move_id.id, tuple(account_ids),))
                move_line_list = []
                account_inv = self.env['account.invoice'].search([('date_invoice', '<', period.date_from), ('date_invoice', '>', old_fyear.date_from)])
                for inv in account_inv:
                    if inv.filtered(lambda z: z.payment_ids.filtered(lambda x: x.payment_date >= period.date_from)):
                        move_line_ids = inv.move_id.line_ids.filtered(lambda y: y.date < period.date_from and y.reconciled)
                        if move_line_ids:
                            move_line_list += move_line_ids.ids
                            self._cr.execute('''
                                INSERT INTO account_move_line (
                                     name, create_uid, create_date, write_uid, write_date,
                                      journal_id, currency_id, date_maturity,
                                     partner_id, blocked,credit,  debit,
                                     ref, account_id, period_id, date, move_id, amount_currency,
                                     quantity, product_id, company_id)
                                  (SELECT name, create_uid, create_date, write_uid, write_date,
                                     %s,currency_id, date_maturity, partner_id,blocked,
                                     credit, debit, ref, account_id,
                                     %s, (%s) AS date, %s, amount_currency, quantity, product_id, company_id
                                   FROM account_move_line
                                   WHERE account_id IN %s AND id IN %s)''', (new_journal.id, period.id, period.date_from, move_id.id, tuple(account_ids), tuple(move_line_ids.ids),))
                move_line_data = self.env['account.move.line'].search([('id', 'not in', move_line_list), ('date', '<', period.date_from), ('reconciled', '=', False)])
                if move_line_data:
                    self._cr.execute('''
                        INSERT INTO account_move_line (
                             name, create_uid, create_date, write_uid, write_date,
                              journal_id, currency_id, date_maturity,
                             partner_id, blocked,credit,  debit,
                             ref, account_id, period_id, date, move_id, amount_currency,
                             quantity, product_id, company_id)
                          (SELECT name, create_uid, create_date, write_uid, write_date,
                             %s,currency_id, date_maturity, partner_id,blocked,
                             credit, debit, ref, account_id,
                             %s, (%s) AS date, %s, amount_currency, quantity, product_id, company_id
                           FROM account_move_line
                           WHERE account_id IN %s AND id IN %s)''', (new_journal.id, period.id, period.date_from, move_id.id, tuple(account_ids), tuple(move_line_data.ids),))

            except:
                import traceback
                traceback.print_exc()
                return

        self._cr.execute('''
            SELECT a.id
            FROM account_account a
            LEFT JOIN account_account_type t ON (a.user_type_id = t.id)
            WHERE a.company_id = %s
              AND t.internal_group IN ('liability','asset')
              AND a.reconcile = %s''', (company_id, False))
        account_ids = map(lambda x: x[0], self._cr.fetchall())

        query_1st_part = """
                INSERT INTO account_move_line (
                     debit, credit, name, date,date_maturity, move_id, journal_id, period_id,
                     account_id, currency_id, amount_currency, company_id) VALUES
        """
        query_2nd_part = ""
        query_2nd_part_args = []

        for account in account_ids:
            account_balance = 0.0
            move_lines = obj_acc_move_line.sudo().search([('account_id', '=', account), ('period_id.fiscal_year_id', '=', fy_ids[-1])])
            if move_lines:
                for line in move_lines:
                    if line.debit > 0.0:
                        account_balance += line.debit
                    if line.credit > 0.0:
                        account_balance -= line.credit

            account = self.env['account.account'].browse(account)
            if account_balance != 0.0:
                if query_2nd_part:
                    query_2nd_part += ','
                query_2nd_part += "(%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s)"
                query_2nd_part_args += (account_balance > 0 and account_balance or 0.0,
                                        account_balance < 0 and -account_balance or 0.0,
                                        self.name, period.date_from,
                                        period.date_from, move_id.id,
                                        new_journal.id, period.id,
                                        account.id, account.currency_id and account.currency_id.id or None,
                                        account.foreign_balance if account.currency_id else 0.0,
                                        account.company_id.id)
        if query_2nd_part:
            self._cr.execute(query_1st_part + query_2nd_part, tuple(query_2nd_part_args))
        # Add centralized line to reconcile it
        query_1st_part = """
                INSERT INTO account_move_line (
                     debit, credit, name, date,date_maturity, move_id, journal_id, period_id,
                     account_id, currency_id, amount_currency, company_id) VALUES
        """
        # find all lines with this move
        move_lines = obj_acc_move_line.sudo().search([('move_id', '=', move_id.id)])
        for line in move_lines:
            total_credit += line.credit
            total_debit += line.debit
            line._store_balance()

        if total_credit < 0.0:
            total_credit = - total_credit
        if total_debit < 0.0:
            total_debit = - total_debit
        # Credit Line
        query_credit_part = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        account = new_journal.default_debit_account_id
        query_credit_part_args = (total_credit, 0.0, 'Credit Centralisation', period.date_from, period.date_from,
                                  move_id.id, new_journal.id, period.id, account.id, account.currency_id and account.currency_id.id or None,
                                  account.foreign_balance if account.currency_id else 0.0, account.company_id.id)
        self._cr.execute(query_1st_part + query_credit_part, tuple(query_credit_part_args))
        # Debit Line
        query_credit_part = "(%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s)"
        account = new_journal.default_credit_account_id
        query_credit_part_args = (0.0, total_debit, 'Debit Centralisation', period.date_from, period.date_from,
                                  move_id.id, new_journal.id, period.id, account.id, account.currency_id and account.currency_id.id or None,
                                  account.foreign_balance if account.currency_id else 0.0, account.company_id.id)
        self._cr.execute(query_1st_part + query_credit_part, tuple(query_credit_part_args))

        last_move_lines = obj_acc_move_line.sudo().search([('move_id', '=', move_id.id)], limit=2, order='id desc')
        for line in last_move_lines:
            line._store_balance()

        move_id._amount_compute()
        move_id.write({'amount': total_credit + total_debit})
        old_fyear.write({'move_id': move_id.id})
        return {'type': 'ir.actions.act_window_close'}
