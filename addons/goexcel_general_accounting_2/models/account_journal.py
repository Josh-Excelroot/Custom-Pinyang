from odoo import api, fields, models, exceptions, _
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # Ahmad Zaman - 12/01/24 - Passing bank_account_id to fix Journal Duplication issue
    def copy(self, default=None):
        default = dict(default or {})
        if self.type == 'bank':
            default.update({
                'bank_account_id': self.bank_account_id.id,
            })
        return super(AccountJournal, self).copy(default)

    # Ahmad Zaman - 3/1/25 - Added dashboard codes for aging and overdue invoices
    def get_journal_dashboard_datas(self):
        res = super(AccountJournal, self).get_journal_dashboard_datas()
        currency = self.currency_id or self.company_id.currency_id
        (query, query_args) = ("""SELECT id,state, residual_company_signed as amount_total, currency_id AS currency, type, date_invoice, company_id
                          FROM account_invoice
                          WHERE journal_id = %(journal_id)s AND state = 'open';""", {'journal_id': self.id})
        self.env.cr.execute(query, query_args)
        query_results_to_pay = self.env.cr.dictfetchall()
        (query, query_args) = ("""SELECT state,
                            (CASE WHEN inv.type in ('out_invoice', 'in_invoice')
                                THEN inv.residual_company_signed
                                ELSE (-1 * inv.residual_company_signed)
                            END) AS amount_total,
                            inv.currency_id AS currency,
                            inv.type,
                            inv.date_invoice,
                            inv.company_id
                          FROM account_invoice inv
                          WHERE journal_id = %(journal_id)s AND state = 'draft';""", {'journal_id': self.id})
        self.env.cr.execute(query, query_args)
        query_results_drafts = self.env.cr.dictfetchall()

        today = fields.Date.today()
        query = """SELECT residual_company_signed as amount_total, currency_id AS currency,id AS record_id, type, date_invoice, company_id FROM account_invoice WHERE journal_id = %s AND date <= %s AND state = 'open';"""
        self.env.cr.execute(query, (self.id, today))
        late_query_results = self.env.cr.dictfetchall()
        curr_cache = {}
        (number_waiting, sum_waiting) = self._count_results_and_sum_amounts(query_results_to_pay, currency,
                                                                            curr_cache=curr_cache)
        (number_draft, sum_draft) = self._count_results_and_sum_amounts(query_results_drafts, currency,
                                                                        curr_cache=curr_cache)
        (number_late, sum_late) = self._count_results_and_sum_amounts(late_query_results, currency,
                                                                      curr_cache=curr_cache)
        res.update({
            'sum_waiting': formatLang(self.env, currency.round(sum_waiting) + 0.0, currency_obj=currency),
            'sum_draft': formatLang(self.env, currency.round(sum_draft) + 0.0, currency_obj=currency),
            'sum_late': formatLang(self.env, currency.round(sum_late) + 0.0, currency_obj=currency),
        })
        query = """SELECT residual_company_signed as amount_total, currency_id AS currency, id AS record_id, type, date_invoice, company_id
                               FROM account_invoice
                               WHERE journal_id = %s AND date_due <= %s AND state = 'open';"""
        self.env.cr.execute(query, (self.id, today))
        overdue_query_results = self.env.cr.dictfetchall()
        curr_cache = {}
        (number_overdue, sum_overdue) = self._count_results_and_sum_amounts(overdue_query_results, currency,
                                                                            curr_cache=curr_cache)

        res.update({
            'number_overdue': number_overdue,
            'sum_overdue': formatLang(self.env, currency.round(sum_overdue) + 0.0, currency_obj=currency),
        })
        return res