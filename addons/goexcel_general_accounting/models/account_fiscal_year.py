from odoo import fields, models, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime , date


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    def fiscal_year_renew(self):
        # self.compute_generated_entries(datetime.today())
        #search by desc end date
        for company in self.env['res.company'].search([]):
            company_id = company.id
            fiscal_years = self.env['account.fiscal.year'].search([('company_id', '=', company_id)], order='date_to desc')
            # current_date = date.today()
            current_date = date.today()
            # current_date = datetime.today().strftime('%d/%m/%Y')
            # print(current_date)
            # renew = self.env['fiscal_year_renew']
            if fiscal_years[0].date_to < current_date:
                #Add 12 months to the last fiscal year
                new_date_from = fiscal_years[0].date_from + relativedelta(months=12)
                new_date_to = fiscal_years[0].date_to + relativedelta(months=12)
                vals = {
                    'name': 'Fiscal Year ' + str(new_date_to.year),
                    'date_from': new_date_from,
                    'date_to': new_date_to,
                    }
                fiscal_year = self.env['account.fiscal.year'].create(vals)
                self.create_fiscal_year_closing_entry(company_id, fiscal_year)

    def create_fiscal_year_closing_entry(self, company_id, fiscal_year):
        # GATHERING NEEDED RECORDS
        account_type_names = ['Other Income', 'Income', 'Depreciation', 'Expenses', 'Cost of Revenue']
        accounts = self.env['account.account'].search([
            ('user_type_id.name', 'in', account_type_names),
            ('company_id', '=', company_id)
        ])
        journal_ids = self.env['account.journal'].search([('company_id', '=', company_id)]).ids
        retained_earning_account = self.env['account.account'].search([
            ('name', '=', 'RETAINED EARNING'),
            ('user_type_id.name', '=', 'Equity'),
            ('company_id', '=', company_id)
        ])
        if not retained_earning_account:
            raise UserError('RETAINED EARNING (Equity) CoA is not set in company ' + company_id.name)
        undestributed_pnl_account = self.env['account.account'].search([
            ('name', '=', 'UNDISTRIBUTED PROFITS/LOSS'),
            ('user_type_id.name', '=', 'Current Year Earnings'),
            ('company_id', '=', company_id)
        ])
        if not undestributed_pnl_account:
            raise UserError(
                'UNDISTRIBUTED PROFITS/LOSS (Current Year Earnings) CoA is not set in company ' + company_id.name)
        journal = self.env['account.journal'].search([
            ('name', '=', 'Miscellaneous Operations'),
            ('company_id', '=', company_id)
        ])
        if not journal:
            raise UserError(
                'Miscellaneous Operations Journal is not set in company ' + company_id.name)

        # CALCULATING BALANCE
        context = {
            'date_from': fiscal_year.date_from,
            'date_to': fiscal_year.date_to,
            'strict_range': True,
            'journal_ids': journal_ids,
            'initial_bal': False,
            'company_id': company_id,
            'state': 'posted'
        }
        current_date = datetime.today()

        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get()
        tables = tables.replace('"', '') if tables else "account_move_line"
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                  " FROM " + tables + \
                  " WHERE account_id IN %s " \
                  + filters + \
                  " GROUP BY account_id"
        params = (tuple(accounts._ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        entries = self.env.cr.dictfetchall()
        balance = -sum(entry.get('balance', 0) for entry in entries)

        # CREATING JOURNAL ENTRY
        entry_label = f'RETAINED EARNINGS {fiscal_year.date_from.year}'
        fiscal_year_pnl_move = self.env['account.move'].create({
            'ref': entry_label,
            'journal_id': journal.id,
            'date': current_date,
            'company_id': company_id,
            'line_ids': [
                (0, 0, {
                    'account_id': retained_earning_account.id,
                    'name': entry_label,
                    'credit': 0 if balance < 0 else balance,
                    'debit': 0 if balance > 0 else balance,
                    'date': current_date,
                    'date_maturity': current_date,
                }),
                (0, 0, {
                    'account_id': undestributed_pnl_account.id,
                    'name': entry_label,
                    'credit': 0 if balance > 0 else balance,
                    'debit': 0 if balance < 0 else balance,
                    'date': current_date,
                    'date_maturity': current_date,
                })
            ],
        })
        fiscal_year_pnl_move.post()

