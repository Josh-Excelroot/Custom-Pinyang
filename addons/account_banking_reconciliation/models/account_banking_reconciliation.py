# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
# Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp
from datetime import datetime
from operator import itemgetter
from odoo.tools.float_utils import float_round


class BankAccRecStatement(models.Model):
    _name = "bank.acc.rec.statement"
    _description = "Bank Acc Rec Statement"
    _order = "ending_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    def check_group(self):
        """Check if following security constraints are implemented for groups:
        Bank Statement Preparer– they can create, view and delete any of the
        Bank Statements provided the Bank Statement is not in the DONE state,
        or the Ready for Review state.
        Bank Statement Verifier – they can create, view, edit, and delete any
        of the Bank Statements information at any time.
        NOTE: DONE Bank Statements  are only allowed to be deleted by a
        Bank Statement Verifier."""
        model_data_obj = self.env['ir.model.data']
        res_groups_obj = self.env['res.groups']
        group_verifier_id = model_data_obj._get_id(
            'account_banking_reconciliation',
            'group_bank_stmt_verifier')
        # TS bug - bug when user is preparer and not verifier, but still cannot access
        # for statement in self:
        #     if group_verifier_id:
        #         res_id = model_data_obj.browse(group_verifier_id).res_id
        #         group_verifier = res_groups_obj.browse([res_id])
        #         group_user_ids = [user.id for user in group_verifier.users]
        #         if statement.state != 'draft' \
        #                 and self.env.uid not in group_user_ids:
        #             raise UserError(_("Only a member of '%s' "
        #                               "group may delete/edit "
        #                               "bank statements when not in draft "
        #                               "state!" % (group_verifier.name)))
        return True

    # add this method by Shivam-Laxicon Solution
    @api.model
    def create(self, vals):
        res = super(BankAccRecStatement, self).create(vals)
        cr_ids = []
        if vals.get('credit_move_line_ids'):
            for rec in vals.get('credit_move_line_ids'):
                if rec[2].get('cleared_bank_account'):
                    cr_ids.append(rec[2].get('move_line_id'))
        dr_ids = []
        if vals.get('debit_move_line_ids'):
            for rec in vals.get('debit_move_line_ids'):
                if rec[2].get('cleared_bank_account'):
                    dr_ids.append(rec[2].get('move_line_id'))
        res.create_move_account_id()
        for cr_id in res.credit_move_line_ids:
            if cr_id.move_line_id.id in cr_ids:
                cr_id.cleared_bank_account = True
        for dr_id in res.debit_move_line_ids:
            if dr_id.move_line_id.id in dr_ids:
                dr_id.cleared_bank_account = True
        return res

    @api.multi
    def write(self, vals):
        # Check if the user is allowed to perform the action
        self.check_group()
        res = super(BankAccRecStatement, self).write(vals)
        if 'account_id' in vals or 'ending_date' in vals or 'suppress_ending_date_filter' in vals:
            self.create_move_account_id()
        return res

    @api.multi
    def unlink(self):
        """Check if the user is allowed to perform the action"""
        self.check_group()
        return super(BankAccRecStatement, self).unlink()

    @api.multi
    def check_difference_balance(self):
        # Check if difference balance is zero or not.
        for statement in self:
            foreign_currency_account = False
            # print('>>>>>>>>> statement.cleared_balance_cur=', statement.cleared_balance_cur,
            #      ', statement.difference_cur=', statement.difference_cur)
            # if statement.account_id.currency_id.id != self.env.user.company_id.currency_id.id:
            #     foreign_currency_account = True
            if self.foreign_account:
                if not statement.bypass_cleared_balance_curr:
                    if statement.difference_cur != 0.0:
                        raise UserError(_("Prior to reconciling a statement, "
                                          "all differences in Foreign Currency must be accounted for "
                                          "and the Difference balance must be "
                                          "zero. Please review "
                                          "and make necessary changes."))
                # else:
                #     if statement.difference != 0.0:
                #         raise UserError(_("2Prior to reconciling a statement, "
                #                           "all differences must be accounted for "
                #                           "and the Difference balance must "
                #                           "be zero. Please review "
                #                           "and make necessary changes."))
            else:
                if statement.difference != 0.0:
                    raise UserError(_("Prior to reconciling a statement, "
                                      "all differences must be accounted for "
                                      "and the Difference balance must "
                                      "be zero. Please review "
                                      "and make necessary changes."))
            # in case the move_line_id is empty (journal items)
            for debit_line in self.debit_move_line_ids:
                if not debit_line.move_line_id:
                    raise UserError(
                        _("'%s' Journal Item is empty") % debit_line.name)
            for credit_line in self.credit_move_line_ids:
                if not credit_line.move_line_id:
                    raise UserError(
                        _("'%s' Journal Item is empty") % credit_line.name)
        return True

    @api.multi
    def action_cancel(self):
        """Cancel the the statement."""
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def action_review(self):
        """Change the status of statement from 'draft' to 'to_be_reviewed'."""
        # If difference balance not zero prevent further processing
        self.check_difference_balance()
        self.write({'state': 'to_be_reviewed'})
        return True

    @api.multi
    def action_process(self):
        """Set the account move lines as 'Cleared' and
        Assign 'Bank Acc Rec Statement ID'
        for the statement lines which are marked as 'Cleared'."""
        # If difference balance not zero prevent further processing
        self.check_difference_balance()
        for statement in self:
            statement_lines = statement.credit_move_line_ids + statement.debit_move_line_ids
            statement_line_recordset = statement_lines.filtered(
                lambda r: r.cleared_bank_account is True)
            # if statement_line_recordset:
            for statement_line in statement_line_recordset:
                # Mark the move lines as 'Cleared'mand assign
                # the 'Bank Acc Rec Statement ID'
                statement_id = statement_line.cleared_bank_account and statement.id or False
                # cleared_bank_account = statement_line.cleared_bank_account
                statement_line.move_line_id.write({
                    'cleared_bank_account': True,
                    'reconciled': True,
                    'bank_acc_rec_statement_id': statement_id})

            current_date = datetime.now().date()
            statement.write({'state': 'done',
                             'verified_by_user_id': self.env.uid,
                             'verified_date': current_date})
        return True

    @api.multi
    def action_cancel_draft(self):
        """Reset the statement to draft and perform resetting operations."""
        for statement in self:
            statement_lines = \
                statement.credit_move_line_ids + statement.debit_move_line_ids
            line_ids = []
            for statement_line in statement_lines:
                if statement_line.move_line_id and statement_line.cleared_bank_account:
                    # Find move lines related to statement lines
                    # TS bug - only remove those that is cleared (otherwise, next month recon may be unreconciled)
                    line_ids.append(statement_line.move_line_id.id)
            # Reset 'Cleared' and 'Bank Acc Rec Statement ID' to False
            self.env['account.move.line'].browse(line_ids).write(
                {'cleared_bank_account': False,
                 'reconciled': False,
                 'bank_acc_rec_statement_id': False})

            # Reset 'Cleared' in statement lines
            statement_lines.write(
                {'cleared_bank_account': False, 'research_required': False})
            # Reset statement
            statement.write(
                {'state': 'draft', 'verified_by_user_id': False, 'verified_date': False})
        return True

    @api.multi
    def action_select_all(self):
        """Mark all the statement lines as 'Cleared'."""
        # Bug - TS
        for statement in self:
            for credit_line in statement.credit_move_line_ids:
                credit_line.cleared_bank_account = True
            for debit_line in statement.debit_move_line_ids:
                debit_line.cleared_bank_account = True
        self.refresh_record()

    @api.multi
    def action_unselect_all(self):
        """Reset 'Cleared' in all the statement lines."""
        # Bug - TS
        for statement in self:
            for credit_line in statement.credit_move_line_ids:
                credit_line.cleared_bank_account = False
            for debit_line in statement.debit_move_line_ids:
                debit_line.cleared_bank_account = False
        self.refresh_record()

    # If the payment is redo, move_line_id will be deleted and empty.
    # Therefore need to show the error message and allow the user to fix it.
    # @api.depends('credit_move_line_ids.move_line_id', 'debit_move_line_ids..move_line_id')
    @api.multi
    def _compute_error_message(self):
        for record in self:
            missing_credit_journals = record.credit_move_line_ids.filtered(
                lambda r: not r.move_line_id and r.cleared_bank_account)
            error_message = 'Missing '
            for missing_credit_journal in missing_credit_journals:
                error_message += missing_credit_journal.name + ' '
            missing_debit_journals = record.debit_move_line_ids.filtered(
                lambda r: not r.move_line_id and r.cleared_bank_account)
            for missing_debit_journal in missing_debit_journals:
                error_message += missing_debit_journal.name + ' '
            if len(error_message) > 10:
                record.error_message = error_message
                record.write({'is_error': True})
            else:
                record.write({'is_error': False})

    @api.depends('credit_move_line_ids.reconciled', 'debit_move_line_ids.reconciled')
    def _compute_get_balance(self):
        """Computed as following:
        A) Deposits, Credits, and Interest Amount:
        Total SUM of Amts of lines with Cleared = True
        Deposits, Credits, and Interest # of Items:
        Total of number of lines with Cleared = True
        B) Checks, Withdrawals, Debits, and Service Charges Amount:
        Checks, Withdrawals, Debits, and Service Charges Amount # of Items:
        Cleared Balance (Total Sum of the Deposit Amount Cleared (A) –
        Total Sum of Checks Amount Cleared (B))
        Difference= (Ending Balance – Beginning Balance) - cleared balance =
        should be zero.
        """
        # TS bug when dealing with the Foreign currency and internal transfer from MYR to USD account.
        account_precision = self.env['decimal.precision'].precision_get(
            'Account')
        for statement in self:
            for line in statement.credit_move_line_ids:
                statement.sum_of_credits += line.cleared_bank_account and float_round(
                    line.amount, account_precision) or 0.0
                if line.currency_id and line.currency_id.id == statement.account_id.currency_id.id and line.currency_id.id != statement.company_id.currency_id.id:
                    statement.sum_of_credits_cur += line.cleared_bank_account and float_round(
                        line.amountcur, account_precision) or 0.0
                statement.sum_of_credits_lines += line.cleared_bank_account and 1 or 0
                statement.sum_of_ucredits += (not line.cleared_bank_account) and float_round(
                    line.amount, account_precision) or 0.0
                if line.currency_id and line.currency_id.id == statement.account_id.currency_id.id and line.currency_id.id != statement.company_id.currency_id.id:
                    statement.sum_of_ucredits_cur += (not line.cleared_bank_account) and float_round(
                        line.amountcur, account_precision) or 0.0
                statement.sum_of_ucredits_lines += (
                    not line.cleared_bank_account) and 1 or 0
        for line in statement.debit_move_line_ids:
            statement.sum_of_debits += line.cleared_bank_account and float_round(
                line.amount, account_precision) or 0.0
            if line.currency_id and line.currency_id.id == statement.account_id.currency_id.id and line.currency_id.id != statement.company_id.currency_id.id:
                statement.sum_of_debits_cur += line.cleared_bank_account and float_round(
                    line.amountcur, account_precision) or 0.0
            statement.sum_of_debits_lines += line.cleared_bank_account and 1 or 0
            statement.sum_of_udebits += (not line.cleared_bank_account) and float_round(
                line.amount, account_precision) or 0.0
            if line.currency_id and line.currency_id.id == statement.account_id.currency_id.id and line.currency_id.id != statement.company_id.currency_id.id:
                statement.sum_of_udebits_cur += (not line.cleared_bank_account) and float_round(
                    line.amountcur, account_precision) or 0.0
            statement.sum_of_udebits_lines += (
                not line.cleared_bank_account) and 1 or 0
            statement.cleared_balance = float_round(
                statement.sum_of_debits - statement.sum_of_credits, account_precision)
            statement.cleared_balance_cur = float_round(
                statement.sum_of_debits_cur - statement.sum_of_credits_cur, account_precision)
            statement.difference = float_round(
                (statement.ending_balance - statement.starting_balance) - statement.cleared_balance, account_precision)
            statement.difference_cur = float_round(
                (statement.ending_balance - statement.starting_balance) - statement.cleared_balance_cur, account_precision)
            statement.uncleared_balance = float_round(
                statement.sum_of_udebits - statement.sum_of_ucredits, account_precision)
            statement.uncleared_balance_cur = float_round(
                statement.sum_of_udebits_cur - statement.sum_of_ucredits_cur, account_precision)

    # refresh data
    # @api.multi
    # def refresh_new_record(self):

    def action_fix_error(self):
        self.refresh_record()
        account_move_line_obj = self.env['account.move.line']
        domain = [('account_id', '=', self.account_id.id),
                  ('move_id.state', '=', 'posted'),
                  ('date', '<=', self.ending_date),
                  ('cleared_bank_account', '=', False)]
        unrecon_move_lines = account_move_line_obj.search(domain)
        cr_move_line_ids = self.credit_move_line_ids.filtered(
            lambda r: not r.move_line_id and r.cleared_bank_account)
        dr_move_line_ids = self.debit_move_line_ids.filtered(
            lambda r: not r.move_line_id and r.cleared_bank_account)
        cflag = False
        inv_or = ''
        # bill_pv = ''
        # dflag = False
        name_lst1 = []
        name_lst2 = []
        for move_line_id in dr_move_line_ids:
            for line in unrecon_move_lines:
                name = (line.payment_id and line.payment_id.name) or (line.invoice_id and line.invoice_id.name) or line.name
                if move_line_id.name == name:
                    name_lst2.append(move_line_id.name)
                    if line.debit != move_line_id.amount:
                        cflag = True
                        inv_or += "There was change of amount in %s. Please reset to draft and re-confirm the current bank statement. \n" % (move_line_id.name)
                    else:
                        line.write({'cleared_bank_account': True, 'reconciled': True})
                        move_line_id.move_line_id = line.id
                else:
                    name_lst1.append(move_line_id.name)

        for move_line_id in cr_move_line_ids:
            for line in unrecon_move_lines:
                name = (line.payment_id and line.payment_id.name) or (line.invoice_id and line.invoice_id.name) or line.name
                if move_line_id.name == name:
                    name_lst2.append(move_line_id.name)
                    if line.credit != move_line_id.amount:
                        cflag = True
                        print ("EEEE", line.credit, move_line_id.amount, line, move_line_id.move_line_id)
                        inv_or += "There was change of amount in %s. Please reset to draft and re-confirm the current bank statement. \n" % (move_line_id.name)
                    else:
                        line.write({'cleared_bank_account': True, 'reconciled': True})
                        move_line_id.move_line_id = line.id
                else:
                    name_lst1.append(move_line_id.name)
        self._compute_error_message()
        name_lst = list(set(name_lst1) - set(name_lst2))
        if name_lst:
            cflag = True
            inv_or += "Please confirm %s to posted. \n" % (', '.join(na for na in name_lst))
        if cflag:
            raise ValidationError(_(inv_or))

    # @api.multi
    def refresh_record(self):
        retval = True
        refdict = {}
        # get current state of moves in the statement
        for statement in self:
            if statement.state == 'draft':
                for cr_item in statement.credit_move_line_ids:
                    if cr_item.move_line_id and cr_item.cleared_bank_account:
                        refdict[cr_item.move_line_id.id] = cr_item.cleared_bank_account
                for dr_item in statement.debit_move_line_ids:
                    if dr_item.move_line_id and dr_item.cleared_bank_account:
                        refdict[dr_item.move_line_id.id] = dr_item.cleared_bank_account
        # for the statement
        for statement in self:
            # process only if the statement is in draft state
            if statement.state == 'draft':
                vals = statement.onchange_account_id()
                # list of credit lines
                outlist = []
                for cr_item in vals['value']['credit_move_line_ids']:
                    cr_item['cleared_bank_account'] = refdict and refdict.get(
                        cr_item['move_line_id'], False) or False
                    cr_item['research_required'] = False
                    item = [0, False, cr_item]
                    outlist.append(item)
                # list of debit lines
                inlist = []
                for dr_item in vals['value']['debit_move_line_ids']:
                    dr_item['cleared_bank_account'] = refdict and refdict.get(
                        dr_item['move_line_id'], False) or False
                    dr_item['research_required'] = False
                    item = [0, False, dr_item]
                    inlist.append(item)
                # write it to the record so it is visible on the form
                retval = self.write(
                    {'last_ending_date': vals['value']['last_ending_date'],
                     'starting_balance': vals['value']['starting_balance'],
                     'credit_move_line_ids': outlist,
                     'debit_move_line_ids': inlist})
        return retval

    # get starting balance for the account
    @api.multi
    def get_starting_balance(self, account_id, ending_date):
        result = (False, 0.0)
        reslist = []
        statement_obj = self.env['bank.acc.rec.statement']
        domain = [('account_id', '=', account_id), ('state', '=', 'done')]
        # get all statements for this account in the past
        for statement in statement_obj.search(domain):
            if statement.ending_date < ending_date:
                reslist.append(
                    (statement.ending_date, statement.ending_balance))
        # get the latest statement value
        if len(reslist):
            reslist = sorted(reslist, key=itemgetter(0))
            result = reslist[len(reslist) - 1]
        return result

    def get_last_statement_end_date(self, account_id, ending_date):
        # Get the journal items that are not reconciled in the previous statement
        statements = self.env['bank.acc.rec.statement'].search([('account_id', '=', account_id), ('state', '=', 'done')],
                                                               order="ending_date desc")

        if statements:
            return statements[0]

    @api.onchange('account_id', 'ending_date', 'suppress_ending_date_filter')
    def onchange_account_id(self):
        account_move_line_obj = self.env['account.move.line']
        statement_line_obj = self.env['bank.acc.rec.statement.line']
        val = {
            'value': {'credit_move_line_ids': [], 'debit_move_line_ids': []}}
        # if self.account_id or self.ending_date:
        #     data = self.search([('account_id', '=', self.account_id.id), ('is_error', '=', True)])
        #     name_list = data.mapped('name')
        #     if data and self.name not in name_list:
        #         # self.account_id = False
        #         msg = ', '.join(data.mapped('name'))
        #         raise ValidationError(_("Please fix the error on the %s") % (msg))
        if self.ending_date and self.account_id:
            # Bug - TS
            self.credit_move_line_ids = False
            self.debit_move_line_ids = False
            # for statement in self:
            # statement_line_ids = statement_line_obj.search(
            #    [('statement_id', '=', statement.id)])
            # call unlink method to reset and
            # remove existing statement lines and
            # mark reset field values in related move lines
            # statement_line_ids.unlink()
            # Apply filter on move lines to allow
            # 1. credit and debit side journal items in posted state of
            # the selected GL account
            # 2. Journal items which are not cleared in
            # previous bank statements
            # 3. Date less than or equal to ending date provided the
            # 'Suppress Ending Date Filter' is not checkec
            domain = [('account_id', '=', self.account_id.id),
                      ('move_id.state', '=', 'posted'),
                      ('cleared_bank_account', '=', False)]
            # TS bug - reconciled will be missing for JV
            # domain = [('account_id', '=', self.account_id.id),
            #            ('move_id.state', '=', 'posted')]
            # ('reconciled', '=', False)]
            if not self.suppress_ending_date_filter:
                domain += [('date', '<=', self.ending_date)]
            # TS bug - user cancel and re-post the PV/OR/JE, therefore Journal item has been deleted.
            last_statement = self.get_last_statement_end_date(self.account_id.id,
                                                              self.ending_date)
            for line in account_move_line_obj.search(domain):
                skip = False
                old_id = statement_line_obj.search([('type', 'in', ['cr', 'dr']), ('move_line_id', '=', line.id), ('cleared_bank_account', '=', True)])
                if not old_id:
                    # Get the move lines that are in the previous months
                    if last_statement and line.date <= last_statement.ending_date:
                        # check if it is in the credit or debit move lines
                        if line.credit:
                            # 3.2 - add the cleared_bank_account
                            move_line_ids = last_statement.credit_move_line_ids.filtered(lambda r: not r.move_line_id and r.cleared_bank_account)
                            for move_line_id in move_line_ids:
                                if line.credit == move_line_id.amount and line.partner_id.id == move_line_id.partner_id.id:
                                    line.write({'cleared_bank_account': True,
                                                'reconciled': True})
                                    move_line_id.move_line_id = line.id
                                    skip = True
                        elif line.debit:
                            move_line_ids = last_statement.debit_move_line_ids.filtered(
                                lambda r: not r.move_line_id)
                            for move_line_id in move_line_ids:
                                if line.debit == move_line_id.amount and line.partner_id.id == move_line_id.partner_id.id:
                                    line.write({'cleared_bank_account': True,
                                                'reconciled': True})
                                    move_line_id.move_line_id = line.id
                                    skip = True
                    if not skip:
                        amount_currency = (line.amount_currency < 0) and (
                            -1 * line.amount_currency) or line.amount_currency
                        if line.name and line.name[0:24] == 'End of Fiscal Year Entry':
                            # do nothing
                            print('')
                        else:
                            name = line.move_id.name
                            if line.invoice_id:
                                name = line.invoice_id.number
                            if line.payment_id:
                                name = line.payment_id.name
                            res = {
                                'ref': line.ref,
                                'date': line.date,
                                'partner_id': line.partner_id.id,
                                'currency_id': line.currency_id.id,
                                'amount': line.credit or line.debit,
                                'amountcur': amount_currency,
                                'name': name,
                                'move_line_id': line.id,
                                'type': line.credit and 'cr' or 'dr'}
                            if res['type'] == 'cr':
                                val['value']['credit_move_line_ids'].append(res)
                            else:
                                val['value']['debit_move_line_ids'].append(res)

            # look for previous statement for the account to
            # pull ending balance as starting balance
            prev_stmt = self.get_starting_balance(self.account_id.id,
                                                  self.ending_date)
            val['value']['last_ending_date'] = prev_stmt[0]
            val['value']['starting_balance'] = prev_stmt[1]

        return val

    # add this method by Shivam-Laxicon Solution
    @api.multi
    def create_move_account_id(self):
        account_move_line_obj = self.env['account.move.line']
        statement_line_obj = self.env['bank.acc.rec.statement.line']
        domain = [('account_id', '=', self.account_id.id),
                  ('move_id.state', '=', 'posted'),
                  ('cleared_bank_account', '=', False)]
        if not self.suppress_ending_date_filter:
            domain.append(('date', '<=', self.ending_date))
        if self.ending_date and self.account_id:
            for line in account_move_line_obj.search(domain):
                amount_currency = (
                    line.amount_currency < 0) and (-1 * line.amount_currency) or line.amount_currency
                t_type = line.credit and 'cr' or 'dr'
                name = line.move_id.name
                if line.invoice_id:
                    name = line.invoice_id.number
                if line.payment_id:
                    name = line.payment_id.name
                if t_type == 'cr':
                    # credit_move_line_ids
                    old_id = statement_line_obj.search(
                        [('statement_id', '=', self.id), ('type', '=', 'cr'), ('move_line_id', '=', line.id)])
                    if not old_id:
                        res = {
                            'ref': line.ref,
                            'date': line.date,
                            'partner_id': line.partner_id.id,
                            'currency_id': line.currency_id.id,
                            'amount': line.credit or line.debit,
                            'amountcur': amount_currency,
                            'name': name,
                            'move_line_id': line.id,
                            'type': line.credit and 'cr' or 'dr',
                            'statement_id': self.id
                        }
                        self.credit_move_line_ids = [(0, 0, res)]
                else:
                    old_id = statement_line_obj.search(
                        [('statement_id', '=', self.id), ('type', '=', 'dr'), ('move_line_id', '=', line.id)])
                    if not old_id:
                        res = {
                            'ref': line.ref,
                            'date': line.date,
                            'partner_id': line.partner_id.id,
                            'currency_id': line.currency_id.id,
                            'amount': line.credit or line.debit,
                            'amountcur': amount_currency,
                            'name': name,
                            'move_line_id': line.id,
                            'type': line.credit and 'cr' or 'dr',
                            'statement_id': self.id
                        }
                        self.debit_move_line_ids = [(0, 0, res)]
        self.get_starting_balance(self.account_id.id, self.ending_date)
        self.refresh_record()

    # TS
    @api.one
    @api.depends('credit_move_line_ids.cleared_bank_account')
    def _onchange_credit_cleared_bank_account(self):
        self.refresh_record()

    # TS
    @api.one
    @api.depends('debit_move_line_ids.cleared_bank_account')
    def _onchange_debit_cleared_bank_account(self):
        self.refresh_record()

    def get_default_company_id(self):
        return self.env['res.users'].browse([self.env.uid]).company_id.id

    name = fields.Char('Name', required=True, size=64, states={'done': [(
        'readonly', True)]}, help="This is a unique name identifying the statement (e.g. Bank X January 2012).")
    account_id = fields.Many2one('account.account', 'Bank Account', required=True, states={'done': [('readonly', True)]}, domain="[('user_type_id.name', '=', 'Bank and Cash')]",
                                 default=lambda self: self.env.context.get('account_id'), help="The Bank/Gl Account that is being reconciled.")
    ending_date = fields.Date('Ending Date', required=True, states={'done': [('readonly', True)]}, default=time.strftime(
        '%Y-%m-%d'), help="The ending date of your bank statement.", track_visibility='always')
    last_ending_date = fields.Date(
        'Last Stmt Date', help="The previous statement date of your bank statement.", track_visibility='always')
    starting_balance = fields.Float('Starting Balance', required=True, digits=dp.get_precision(
        'Account'), help="The Starting Balance on your bank statement.", states={'done': [('readonly', True)]}, track_visibility='always')
    ending_balance = fields.Float('Ending Balance', required=True, digits=dp.get_precision(
        'Account'), help="The Ending Balance on your bank statement.", states={'done': [('readonly', True)]}, track_visibility='always')
    error_message = fields.Text(
        string='Error Message', track_visibility='always', compute='_compute_error_message')
    is_error = fields.Boolean(
        string='Is Error', track_visibility='always', default=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 default=get_default_company_id, help="The Company for which the deposit ticket is made to")
    notes = fields.Text('Notes')
    verified_date = fields.Date('Verified Date', states={'done': [(
        'readonly', True)]}, copy=False, help="Date in which Deposit Ticket was verified.")
    verified_by_user_id = fields.Many2one('res.users', 'Verified By', states={'done': [(
        'readonly', True)]}, copy=False, help="Entered automatically by the “last user” who saved it. System generated.")
    credit_move_line_ids = fields.One2many('bank.acc.rec.statement.line', 'statement_id', 'Credits', copy=False, domain=[
                                           ('type', '=', 'cr')], states={'done': [('readonly', True)]})
    debit_move_line_ids = fields.One2many('bank.acc.rec.statement.line', 'statement_id', 'Debits', copy=False, domain=[
                                          ('type', '=', 'dr')], states={'done': [('readonly', True)]})
    cleared_balance = fields.Float(compute='_compute_get_balance', string='Cleared Balance', digits=dp.get_precision(
        'Account'), help="Total Sum of the Deposit Amount Cleared – Total Sum of Cheques, Withdrawals, Debits Amount Cleared")
    difference = fields.Float(compute='_compute_get_balance', string='Difference', digits=dp.get_precision(
        'Account'), help="(Ending Balance – Beginning Balance) - Cleared Balance.")
    cleared_balance_cur = fields.Float(compute='_compute_get_balance', string='Cleared Balance (Cur)', digits=dp.get_precision(
        'Account'), help="Total Sum of the Deposit Amount Cleared – Total Sum of Cheques, Withdrawals and Debits Amount Cleared")
    difference_cur = fields.Float(compute='_compute_get_balance', string='Difference (Cur)', digits=dp.get_precision(
        'Account'), help="(Ending Balance – Beginning Balance) - Cleared Balance.")
    uncleared_balance = fields.Float(compute='_compute_get_balance', string='Uncleared Balance', digits=dp.get_precision(
        'Account'), help="Total Sum of the Deposit  Amount Uncleared – Total Sum of  Debits, Cheques and Withdrawals Amount Uncleared")
    uncleared_balance_cur = fields.Float(compute='_compute_get_balance', string='Uncleared Balance (Cur)', digits=dp.get_precision(
        'Account'), help="Total Sum of the Deposit Amount Uncleared – Total Sum of  Debits, Cheques and Withdrawals Amount Uncleared")
    sum_of_credits = fields.Float(compute='_compute_get_balance', string='Debits, Cheques, Withdrawals, etc Amount', digits=dp.get_precision(
        'Account'), type='float', help="Total SUM of Amts of lines with  Cleared = True")
    sum_of_debits = fields.Float(compute='_compute_get_balance', string='Credits, Deposits, and Interest Amount',
                                 digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = True")
    sum_of_credits_cur = fields.Float(compute='_compute_get_balance', string='Cheques, Withdrawals, Debits Amount (Cur)',
                                      digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = True")
    sum_of_debits_cur = fields.Float(compute='_compute_get_balance', string='Deposits, Credits, and Interest Amount (Cur)',
                                     digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = True")
    sum_of_credits_lines = fields.Integer(
        compute='_compute_get_balance', string='''Debits, Cheques, Withdrawals and # of Items''', help="Total of number of lines with Cleared = True")
    sum_of_debits_lines = fields.Integer(
        compute='_compute_get_balance', string='''Credit, Deposits, and Interest # of Items''', help="Total of number of lines with Cleared = True")
    sum_of_ucredits = fields.Float(compute='_compute_get_balance', string='Uncleared - Cheques, Withdrawals, Debits, Check Amount',
                                   digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = False")
    sum_of_udebits = fields.Float(compute='_compute_get_balance', string='Uncleared - Credits and Deposits Amount',
                                  digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = False")
    sum_of_ucredits_cur = fields.Float(compute='_compute_get_balance', string='Uncleared - Cheques, Withdrawals, Debits, and Amount (Cur)',
                                       digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = False")
    sum_of_udebits_cur = fields.Float(compute='_compute_get_balance', string='Uncleared - Deposits, Credits, nd Interest Amount (Cur)',
                                      digits=dp.get_precision('Account'), help="Total SUM of Amts of lines with Cleared = False")
    sum_of_ucredits_lines = fields.Integer(
        compute='_compute_get_balance', string='Uncleared - Cheques, Withdrawals, Debits # of Items', help="Total of number of lines with Cleared = False")
    sum_of_udebits_lines = fields.Integer(
        compute='_compute_get_balance', string='''Uncleared - Deposits, Credits, and Interest # of Items''', help="Total of number of lines with Cleared = False")
    suppress_ending_date_filter = fields.Boolean(
        'Remove Ending Date Filter', help="If this is checked then the Statement End Date filter on the transactions below will not occur. All transactions would come over.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_be_reviewed', 'Ready for Review'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'State', index=True, readonly=True, default='draft', track_visibility='always')
    bypass_cleared_balance_curr = fields.Boolean(
        'Bypass FC Balance Check', help="If this is checked will bypass the checking for the currency balance not cleared")

    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id, account_id)',
         'The name of the statement must be unique per '
         'company and G/L account!')
    ]
    # TS - bug - add to determine the foreign account or company currency account
    foreign_account = fields.Boolean(
        string='Foreign Account', compute='_compute_foreign_account')

    @api.depends('account_id')
    def _compute_foreign_account(self):
        if self.account_id:
            if self.account_id.currency_id and self.account_id.currency_id.id != self.env.user.company_id.currency_id.id:
                self.foreign_account = True
            else:
                self.foreign_account = False

    @api.multi
    def copy(self, default=None):
        for rec in self:
            if default is None:
                default = {}
            if 'name' not in default:
                default['name'] = _("%s (copy)") % rec.name
        return super(BankAccRecStatement, self).copy(default=default)


class BankAccRecStatementLine(models.Model):
    _name = "bank.acc.rec.statement.line"
    _description = "Statement Line"

    name = fields.Char(
        'Name', help="Derived from the related Journal Item.", required=True)
    ref = fields.Char('Reference', help="Derived from related Journal Item.")
    partner_id = fields.Many2one(
        'res.partner', string='Partner', help="Derived from related Journal Item.")
    amount = fields.Float('Amount', digits=dp.get_precision(
        'Account'), help="Derived from the 'debit' amount from related Journal Item.")
    amountcur = fields.Float('Amount in Currency', digits=dp.get_precision(
        'Account'), help="Derived from the 'amount currency' amount from related Journal Item.")
    date = fields.Date('Date', required=True,
                       help="Derived from related Journal Item.")
    statement_id = fields.Many2one(
        'bank.acc.rec.statement', 'Statement', required=True, ondelete='cascade')
    move_line_id = fields.Many2one(
        'account.move.line', 'Journal Item', help="Related Journal Item.")
    cleared_bank_account = fields.Boolean(
        'Cleared?', help='Check if the transaction has  cleared from the bank', copy=False)
    research_required = fields.Boolean(
        'Research Required? ', help='Check if the transaction should  be researched by Accounting personal')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry.")
    type = fields.Selection([('dr', 'Debit'), ('cr', 'Credit')], 'Cr/Dr')
    reconciled = fields.Boolean(
        'Reconciled? ', help='Check if the Payment has been reconciled against Bank Statement', copy=False)

    @api.model
    def create(self, vals):
        account_move_line_obj = self.env['account.move.line']
        # Prevent manually adding new statement line.
        # This would allow only onchange method to pre-populate statement lines
        # based on the filter rules.
        if not vals.get('move_line_id', False):
            raise UserError(
                _("You cannot add any new bank statement line manually as of this revision!"))
        account_move_line_obj.browse([vals['move_line_id']]).write(
            {'draft_assigned_to_statement': True})
        return super(BankAccRecStatementLine, self).create(vals)

    @api.multi
    def unlink(self):
        account_move_line_obj = self.env['account.move.line']
        move_line_ids = [x.move_line_id.id for x in self if x.move_line_id]
        # map(lambda x: x.move_line_id.id if x.move_line_id,
        # self.browse(cr, uid, ids, context=context))
        # Reset field values in move lines to be added later
        account_move_line_obj.browse(move_line_ids).write(
            {'draft_assigned_to_statement': False,
             'cleared_bank_account': False,
             'reconciled': False,
             'bank_acc_rec_statement_id': False})
        return super(BankAccRecStatementLine, self).unlink()
