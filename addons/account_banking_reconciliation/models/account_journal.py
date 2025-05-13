# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    #last_balance_date = fields.Date('Ending Date')

    @api.multi
    def create_bank_statement(self):
        """return action to create a bank statements. This button should be called only on journals with type =='bank'"""
        # action = self.env.ref('account_banking_reconciliation.view_bank_acc_rec_statement_form').read()[0]
        # action.update({
        #     'context': {'account_id': self.default_debit_account_id.id,}
        # })
        ctx = self._context.copy()
        model = 'bank.acc.rec.statement'
        ctx.update({'account_id': self.default_debit_account_id.id,})
        view_id = self.env.ref('account_banking_reconciliation.view_bank_acc_rec_statement_form').id
        return {
            'name': _('Create Bank Statement'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_id': view_id,
            'context': ctx,
        }

    @api.multi
    def get_journal_dashboard_datas(self):
        res = super(AccountJournal, self).get_journal_dashboard_datas()
        account_sum = 0.00
        difference = 0.00
        account_ids = tuple(ac for ac in [self.default_debit_account_id.id, self.default_credit_account_id.id] if ac)
        if account_ids:
            amount_field = 'aml.balance' if (
                        not self.currency_id or self.currency_id == self.company_id.currency_id) else 'aml.amount_currency'
            query = """SELECT sum(%s) FROM account_move_line aml
                                   LEFT JOIN account_move move ON aml.move_id = move.id
                                   WHERE aml.account_id in %%s
                                   AND move.date <= %%s AND move.state = 'posted';""" % (amount_field,)
            self.env.cr.execute(query, (account_ids, fields.Date.context_today(self),))
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('sum') != None:
                account_sum = query_results[0].get('sum')
                #print('>>>>>>>>> get_journal_dashboard_datas account sum=', account_sum, ' , account_ids=', account_ids)
        currency = self.currency_id or self.company_id.currency_id
        bank_statements = self.env['bank.acc.rec.statement'].search(
                        [('account_id', '=', self.default_debit_account_id.id)], order='ending_date desc')

        if bank_statements:
            #print('>>>>>>>>> get_journal_dashboard_datas res=', res)
            statement = bank_statements[0]
            last_balance_date = ''
            #print('>>>>>>>>> ending_date=', statement.ending_date)
            if statement.ending_date:
                last_balance_date = statement.ending_date.strftime('%d/%m/%Y')
            #print('>>>>>>>>> last_balance_date=', last_balance_date)
            #print('>>>>>>>>> Ending Balance=', statement.ending_balance)
            difference = currency.round(account_sum - statement.ending_balance) + 0.0
            #print('>>>>>>>>> Diff=', formatLang(self.env, currency.round(difference) + 0.0, currency_obj=currency))
            res.update({
                'last_balance': formatLang(self.env, currency.round(statement.ending_balance) + 0.0, currency_obj=currency),
                'difference': formatLang(self.env, currency.round(difference) + 0.0, currency_obj=currency),
                'last_balance_date': last_balance_date,
            })
            #print('>>>>>>>>> get_journal_dashboard_datas AFTER res=', res)

        return res
