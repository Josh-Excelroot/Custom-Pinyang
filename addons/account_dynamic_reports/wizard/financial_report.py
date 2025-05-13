# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
try:
    import pandas as pd
except ImportError + ModuleNotFoundError:
    pd = None
from odoo.tools.safe_eval import safe_eval


def assign_year_to_months(month_year_comb, year_start_month):
    month_year_dict = {}
    calendar_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month_year in month_year_comb:
        month, year = month_year.split('-')
        year = int(year)

        if calendar_months.index(month) < calendar_months.index(year_start_month):
            month_year_dict[month_year] = str(year - 1)
        else:
            month_year_dict[month_year] = str(year)

    return month_year_dict


class InsFinancialReport(models.TransientModel):
    _name = "ins.financial.report"
    _inherit = ['dynamic.reports.mixin']
    _description = "Financial Reports"

    date_format = '%d/%m/%Y'

    def _default_account_report(self, values):
        financial_report_view = self._context.get('financial_report_view')
        financial_report_obj = self.env['ins.account.financial.report']
        account_report = financial_report_obj.search([
            ('type', '=', 'sum'),
            ('financial_report_menu', '=', financial_report_view),
            ('company_id', '=', values.get('company_id'))
        ])
        if not account_report:
            account_report = financial_report_obj.search([
                ('type', '=', 'sum'),
                ('financial_report_menu', '=', financial_report_view),
                ('company_id', '=', False)
            ])
        menu_name = dict(financial_report_obj._fields.get('financial_report_menu').selection).get(financial_report_view)
        if not account_report:
            to_update = {
                'profit_loss': 'ins_account_financial_report_profitandloss0',
                'balance_sheet': 'ins_account_financial_report_balancesheet0',
                'cash_flow': 'ins_account_financial_report_cash_flow0'
            }
            if financial_report_view in to_update:
                self.env.ref(f'account_dynamic_reports.{to_update[financial_report_view]}').financial_report_menu = financial_report_view
            # raise UserError(f'No view and configuration found for {menu_name} !\n'
            #                 f'Please create a view in Financial Reports and assign menu to {menu_name}\n'
            #                 f' - Accounting > Configuration > Accounting > Financial Reports > Search for {menu_name} '
            #                 f'> Assign {menu_name} as Financial Report Menu')
        if len(account_report) > 1:
            raise UserError(f'Multiple views and configurations found for {menu_name} !')
        return account_report

    def default_get_domain(self, values=None):
        dom = super(InsFinancialReport, self).default_get_domain()
        default_account_report = self._default_account_report(values)
        if default_account_report:
            dom.append(('account_report_id', '=', default_account_report.id))
        return dom

    @api.model
    def default_get(self, fields):
        res = super(InsFinancialReport, self).default_get(fields)
        company = self.company_id.browse(res.get('company_id'))
        if 'target_move' in fields and company.unposted_entries_dynamic_reports:
            res['target_move'] = 'all'
        financial_report_view = self._context.get('financial_report_view')
        if company and financial_report_view:
            default_account_report = self._default_account_report(res)
            if default_account_report:
                res['account_report_id'] = default_account_report.id
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    @api.constrains('date_from', 'date_to')
    def _validate_comparison_dates(self):
        if self.date_from_cmp and self.date_to_cmp and self.date_from_cmp > self.date_to_cmp:
            raise ValidationError(_('Comparison start date must be less than or equal to end date'))

    def _compute_account_balance(self, accounts, report):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        date_from = self.date_from
        date_to = self.date_to
        if self.env.context.get('date_from', False) and self.env.context.get('date_from', False) != date_from:
            date_from = self.date_from_cmp or False
        if self.env.context.get('date_to', False) and self.env.context.get('date_to', False) != date_to:
            date_to = self.date_to_cmp or False

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            if self.account_report_id != \
                    self.env.ref(
                        'account_dynamic_reports.ins_account_financial_report_cash_flow0') and self.strict_range:
                context = dict(self._context, strict_range=True)
                # Validation
                if report.type in ['accounts', 'account_type'] and not report.range_selection:
                    raise UserError(
                        _('Please choose "Custom Date Range" for the report head %s') % (report.name))
                if report.type in ['accounts', 'account_type'] and report.range_selection == 'from_the_beginning':
                    # FIXED: date filter issue 12 Aug'22
                    context.update({'strict_range': False, 'date_from': False,
                                        'date_to': date_to})
                # For equity
                if report.type in ['accounts', 'account_type'] and report.range_selection == 'current_date_range':
                    if date_to and date_from:
                        context.update({'strict_range': True, 'initial_bal': False, 'date_from': date_from,
                                        'date_to': date_to})
                    else:
                        raise UserError(
                            _('From date and To date are mandatory to generate this report'))
                if report.type in ['accounts', 'account_type'] and report.range_selection == 'initial_date_range':
                    if date_from:
                        context.update(
                            {'strict_range': True, 'initial_bal': True, 'date_from': date_from, 'date_to': False})
                    else:
                        raise UserError(
                            _('From date is mandatory to generate this report'))
                context.update({'include_period_13': self.include_period_13})
                tables, where_clause, where_params = self.env['account.move.line'].with_context(
                    context)._query_get()
            else:
                tables, where_clause, where_params = self.env['account.move.line']._query_get(
                )
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
            # print('>>>>>>>>> _compute_account_balance report request=', request)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            # print('>>>>>>>>> _compute_account_balance report=', report)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res[report.id]['account'] = self._compute_account_balance(
                        report.account_ids, report)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    res2 = self._compute_report_balance(report.parent_id)
                    for key, value in res2.items():
                        if report in [self.env.ref('account_dynamic_reports.ins_cash_in_operation_1'),
                                      self.env.ref(
                                          'account_dynamic_reports.ins_cash_in_investing_1'),
                                      self.env.ref('account_dynamic_reports.ins_cash_in_financial_1')]:
                            res[report.id]['debit'] += value['debit']
                            res[report.id]['balance'] += value['debit']
                        else:
                            res[report.id]['credit'] += value['credit']
                            res[report.id]['balance'] += -(value['credit'])
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    accounts = self.env['account.account'].search(
                        [('user_type_id', 'in', report.account_type_ids.ids), ('id', 'not in', report.exclude_account_ids.ids)])
                    res[report.id]['account'] = self._compute_account_balance(
                        accounts, report)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    accounts = self.env['account.account'].search(
                        [('user_type_id', 'in', report.account_type_ids.ids), ('id', 'not in', report.exclude_account_ids.ids)])
                    res[report.id]['account'] = self._compute_account_balance(
                        accounts, report)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res2 = self._compute_report_balance(
                        report.account_report_id)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
                else:
                    res[report.id]['account'] = self._compute_account_balance(
                        report.account_ids, report)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == 'sum' and not report.display_detail and not report.children_ids:
                res[report.id]['account'] = {}
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res2 = self._compute_report_balance(report.children_ids)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
                else:
                    accounts = report.account_ids
                    if report == self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                        accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id),
                                                                       ('cash_flow_category', 'not in', [0])])
                    res[report.id]['account'] = self._compute_account_balance(
                        accounts, report)
                    for values in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += values.get(field)
        # print('>>>>>>>>> _compute_report_balance res=', res)
        return res

    def get_account_lines(self, data, from_js):
        lines = []
        initial_balance = 0.0
        current_balance = 0.0
        ending_balance = 0.0
        account_report = self.account_report_id
        child_reports = account_report._get_children_by_order(
            strict_range=self.strict_range)
        res = self.with_context(data.get('used_context')
                                )._compute_report_balance(child_reports)
        # print('>>>>>>>>> get_account_lines res=', res)
        if self.account_report_id == \
                self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
            if not data.get('used_context').get('date_from', False):
                raise UserError(_('Start date is mandatory!'))
            cashflow_context = data.get('used_context')
            initial_to = fields.Date.from_string(
                data.get('used_context').get('date_from')) - timedelta(days=1)
            cashflow_context.update(
                {'date_from': False, 'date_to': fields.Date.to_string(initial_to)})
            initial_balance = self.with_context(cashflow_context)._compute_report_balance(child_reports). \
                get(self.account_report_id.id)['balance']
            current_balance = res.get(self.account_report_id.id)['balance']
            ending_balance = initial_balance + current_balance
        if data['enable_filter']:
            comparison_res = self.with_context(
                data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            if not from_js:
                report.display_detail_temp = report.display_detail
            display_detail = (from_js and report.display_detail_temp) or report.display_detail
            company_id = self.env.user.company_id
            currency_id = company_id.currency_id
            ####Canon#####Start#####
            bucket = {}
            vals = {}
            date_from = datetime(self.date_from.year, self.date_from.month, 1).date()
            a = pd.date_range(date_from, self.date_to, freq='MS').strftime("%b-%Y").tolist()
            for x in a:
                vals[x] = 0

            total_report_jan = 0
            total_report_feb = 0
            total_report_mar = 0
            total_report_apr = 0
            total_report_may = 0
            total_report_jun = 0
            total_report_jul = 0
            total_report_aug = 0
            total_report_sep = 0
            total_report_oct = 0
            total_report_nov = 0
            total_report_dec = 0
            if res and res[report.id].get("account"):
                res_temp = res[report.id]["account"]

                for account_id, value in res_temp.items():
                    domain = [
                        ("account_id", "=", account_id),
                        ("date", ">=", self.date_from),
                        ("date", "<=", self.date_to),
                        ('move_id.state', '=', 'posted')
                    ]
                    if self.journal_ids:
                        domain.append(('journal_id', 'in', self.journal_ids.ids))
                    if self.analytic_ids:
                        domain.append(('analytic_account_id', 'in', self.analytic_ids.ids))
                    if self.analytic_tag_ids:
                        domain.append(('analytic_tag_ids.id', 'in', self.analytic_tag_ids.ids))
                    if not self.include_period_13:
                        domain.append(('move_id.period_13', '=', False))
                    journal_items = self.env["account.move.line"].sudo().search(domain)
                    if journal_items:
                        journal_items_info = self.query_fetch(
                            f"SELECT date,credit,debit FROM account_move_line WHERE id in {journal_items._ids + (0,)}",
                            fetchall=True, obj_format=True)
                        for x in journal_items_info:
                            date_month = x.date.month
                            balance = x.debit - x.credit
                            datee = datetime.strptime(str(x.date), "%Y-%m-%d").strftime("%b-%Y")
                            vals[datee] = vals[datee] + balance
                            if date_month == 1:
                                total_report_jan = total_report_jan + balance
                            if date_month == 2:
                                total_report_feb = total_report_feb + balance
                            if date_month == 3:
                                total_report_mar = total_report_mar + balance
                            if date_month == 4:
                                total_report_apr = total_report_apr + balance
                            if date_month == 5:
                                total_report_may = total_report_may + balance
                            if date_month == 6:
                                total_report_jun = total_report_jun + balance
                            if date_month == 7:
                                total_report_jul = total_report_jul + balance
                            if date_month == 8:
                                total_report_aug = total_report_aug + balance
                            if date_month == 9:
                                total_report_sep = total_report_sep + balance
                            if date_month == 10:
                                total_report_oct = total_report_oct + balance
                            if date_month == 11:
                                total_report_nov = total_report_nov + balance
                            if date_month == 12:
                                total_report_dec = total_report_dec + balance
            for x in a:
                vals[x] = vals[x] * int(report.sign)
            vals['name'] = report.name
            vals['balance'] = res[report.id]['balance'] * int(report.sign)
            vals['parent'] = report.parent_id.id if report.parent_id.type in ['accounts', 'account_type'] else 0
            vals['self_id'] = report.id
            vals['type'] = 'report'
            vals['style_type'] = 'main'
            vals['precision'] = currency_id.decimal_places
            vals['symbol'] = currency_id.symbol
            vals['position'] = currency_id.position
            vals['list_len'] = [a for a in range(0, report.level)]
            vals['level'] = report.level
            vals['company_currency_id'] = company_id.currency_id.id
            vals['account_type'] = report.type or False
            vals['fin_report_type'] = report.type
            vals['display_detail'] = display_detail
            #### Expandable/Collapsible Balance Sheet and Profit & Loss Reports | Rajeel | 12/04/23 ####
            vals['row_classes'] = f"py-mline row-toggle a{vals['parent']} collapse show"
            #### END ####

            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * \
                    int(report.sign)

            lines.append(vals)

            #### Expandable/Collapsible Balance Sheet and Profit & Loss Reports | Rajeel | 12/04/23 ####
            if display_detail == 'no_detail' and \
                    ((report.level in [0, 1] and self.view_type == 'ui') or self.view_type != 'ui' or from_js):
                continue
            #### END ####

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    ####Canon#####Start#####
                    vals = {}
                    for x in a:
                        vals[x] = 0
                    total_jan = 0
                    total_feb = 0
                    total_mar = 0
                    total_apr = 0
                    total_may = 0
                    total_jun = 0
                    total_jul = 0
                    total_aug = 0
                    total_sep = 0
                    total_oct = 0
                    total_nov = 0
                    total_dec = 0
                    total_all_month = 0
                    domain = [
                        ("account_id", "=", account_id),
                        ("date", ">=", self.date_from),
                        ("date", "<=", self.date_to),
                        ('move_id.state', '=', 'posted')
                    ]
                    if self.journal_ids:
                        domain.append(('journal_id', 'in', self.journal_ids.ids))
                    if self.analytic_ids:
                        domain.append(('analytic_account_id', 'in', self.analytic_ids.ids))
                    if self.analytic_tag_ids:
                        domain.append(('analytic_tag_ids.id', 'in', self.analytic_tag_ids.ids))
                    if not self.include_period_13:
                        domain.append(('move_id.period_13', '=', False))
                    journal_items = self.env["account.move.line"].search(domain)
                    if journal_items:
                        journal_items_info = self.query_fetch(
                            f"SELECT date,credit,debit FROM account_move_line WHERE id in {journal_items._ids + (0,)}",
                            fetchall=True, obj_format=True)
                        for x in journal_items_info:
                            date_month = x.date.month
                            balance = x.debit - x.credit
                            datee = datetime.strptime(str(x.date), "%Y-%m-%d").strftime("%b-%Y")
                            vals[datee] = vals[datee] + balance
                            total_all_month = total_all_month + balance
                            if date_month == 1:
                                total_jan = total_jan + balance
                            if date_month == 2:
                                total_feb = total_feb + balance
                            if date_month == 3:
                                total_mar = total_mar + balance
                            if date_month == 4:
                                total_apr = total_apr + balance
                            if date_month == 5:
                                total_may = total_may + balance
                            if date_month == 6:
                                total_jun = total_jun + balance
                            if date_month == 7:
                                total_jul = total_jul + balance
                            if date_month == 8:
                                total_aug = total_aug + balance
                            if date_month == 9:
                                total_sep = total_sep + balance
                            if date_month == 10:
                                total_oct = total_oct + balance
                            if date_month == 11:
                                total_nov = total_nov + balance
                            if date_month == 12:
                                total_dec = total_dec + balance

                    ####Canon#####End#####
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    for x in a:
                        vals[x] = vals[x] * int(report.sign)
                    vals['account'] = account.id
                    vals['balance'] = res[report.id]['balance'] * int(report.sign)
                    vals['name'] = account.code + ' ' + account.name
                    vals['balance'] = value['balance'] * int(report.sign) or 0.0
                    vals['type'] = 'account'
                    vals['parent'] = report.id if report.type in ['accounts', 'account_type'] else 0
                    vals['self_id'] = 'a'
                    vals['style_type'] = 'sub'
                    vals['precision'] = currency_id.decimal_places
                    vals['symbol'] = currency_id.symbol
                    vals['position'] = currency_id.position
                    vals['list_len'] = [a for a in range(0, 4)]
                    vals['level'] = 4
                    vals['company_currency_id'] = company_id.currency_id.id
                    vals['account_type'] = account.internal_type
                    vals['fin_report_type'] = report.type
                    vals['display_detail'] = display_detail
                    #### Expandable/Collapsible Balance Sheet and Profit & Loss Reports | Rajeel | 12/04/23 ####
                    if display_detail == 'no_detail':
                        vals['row_classes'] = f"py-mline row-toggle a{vals['parent']} collapse"
                    else:
                        vals['row_classes'] = f"py-mline row-toggle a{vals['parent']} collapse show"
                    #### END ####

                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not currency_id.is_zero(vals['debit']) or not currency_id.is_zero(vals['credit']):
                            flag = True
                    if not currency_id.is_zero(vals['balance']):
                        flag = True
                    if self.group_by != 'no_grouping':
                        for x in a:
                            if vals[x]:
                                flag = True
                                break

                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * \
                            int(report.sign)
                        if not currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
                #print('>>>>>>>>> get_account_lines lines=', lines)
        return lines, initial_balance, current_balance, ending_balance

    def get_report_values(self, from_js=False):
        self.ensure_one()
        # self.onchange_date_range()
        company_domain = [('company_id', '=', self.env.user.company_id.id)]
        journal_ids = self.env['account.journal'].search(company_domain)
        analytics = self.env['account.analytic.account'].search(company_domain)
        analytic_tags = self.env['account.analytic.tag'].sudo().search(
            ['|', ('company_id', '=', self.env.user.company_id.id), ('company_id', '=', False)])

        data = dict()
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'enable_filter', 'debit_credit', 'date_to', 'date_range',
             'account_report_id', 'target_move', 'view_format', 'journal_ids',
             'analytic_ids', 'analytic_tag_ids', 'strict_range',
             'company_id', 'enable_filter', 'date_from_cmp', 'date_to_cmp', 'label_filter', 'filter_cmp', 'include_period_13'])[0]
        data['form'].update({'journals_list': self.create_query_and_fetch('account_journal', 'id,name', f'id in {journal_ids._ids + (0,0)}', fetchall=True, first_column=False)})
        data['form'].update({'analytics_list': self.create_query_and_fetch('account_analytic_account', 'id,name', f'id in {analytics._ids + (0,0)}', fetchall=True, first_column=False)})
        data['form'].update(
            {'analytic_tag_list': self.create_query_and_fetch('account_analytic_tag', 'id,name', f'id in {analytic_tags._ids + (0,0)}', fetchall=True, first_column=False)})
        self._add_report_heading(data)
        if self.enable_filter:
            data['form']['debit_credit'] = False

        used_context = {}
        used_context['date_from'] = self.date_from or False
        used_context['date_to'] = self.date_to or False

        used_context['strict_range'] = True
        used_context['company_id'] = self.env.user.company_id.id

        used_context['journal_ids'] = self.journal_ids.ids
        used_context['analytic_account_ids'] = self.analytic_ids
        used_context['analytic_tag_ids'] = self.analytic_tag_ids
        used_context['state'] = data['form'].get('target_move', '')
        data['form']['used_context'] = used_context

        comparison_context = {}
        comparison_context['strict_range'] = True
        comparison_context['company_id'] = self.env.user.company_id.id

        comparison_context['journal_ids'] = self.journal_ids.ids
        comparison_context['analytic_account_ids'] = self.analytic_ids
        comparison_context['analytic_tag_ids'] = self.analytic_tag_ids
        data['form']['date_from_formatted'] = self.date_from.strftime(self.date_format) or False
        data['form']['date_to_formatted'] = self.date_to.strftime(self.date_format) or False
        if self.filter_cmp == 'filter_date':
            comparison_context['date_to'] = self.date_to_cmp or ''
            comparison_context['date_from'] = self.date_from_cmp or ''
            comparison_context['date_to_formatted'] = self.date_to_cmp and self.date_to_cmp.strftime(self.date_format) or ''
            comparison_context['date_from_formatted'] = self.date_from_cmp and self.date_from_cmp.strftime(self.date_format) or ''
        else:
            comparison_context['date_to'] = False
            comparison_context['date_from'] = False
        comparison_context['state'] = self.target_move or ''
        data['form']['comparison_context'] = comparison_context

        report_lines, initial_balance, current_balance, ending_balance = self.get_account_lines(data.get('form'), from_js)
        company_id = self.env.user.company_id
        data['currency'] = company_id.currency_id.id
        data['report_lines'] = report_lines
        data['initial_balance'] = initial_balance or 0.0
        data['current_balance'] = current_balance or 0.0
        data['ending_balance'] = ending_balance or 0.0
        if self.account_report_id == \
                self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
            data['form']['rtype'] = 'CASH'
        elif self.account_report_id == \
                self.env.ref('account_dynamic_reports.ins_account_financial_report_profitandloss0'):
            data['form']['rtype'] = 'PANDL'
        else:
            if self.strict_range:
                data['form']['rtype'] = 'OTHER'
            else:
                data['form']['rtype'] = 'PANDL'
        #####Canon#####Start#####
        data['form']['group_by'] = self.group_by
        data['form']['month_list'] = False
        date_from = datetime(self.date_from.year, self.date_from.month, 1).date()
        a = pd.date_range(date_from, self.date_to, freq='MS').strftime("%b-%Y").tolist()
        data['form']['month_list'] = a

        #####Canon#####End#####

        pnl_or_bs_report = self.account_report_id in [
            self.env.ref('account_dynamic_reports.ins_account_financial_report_profitandloss0'),
            self.env.ref('account_dynamic_reports.ins_account_financial_report_balancesheet0')
        ]

        #### Expandable/Collapsible Balance Sheet and Profit & Loss Reports | Rajeel | 30/03/23 ####
        def set_children_grand_children(data):
            # create a dictionary to store each node's children
            children_dict = {0: []}
            for node in data:
                children_dict[node['self_id']] = []

            # fill the children dictionary with the children of each node
            for node in data:
                children_dict[node['parent']].append(node['self_id'])

            # iterate over the data again and add the flags
            for node in data:
                # check if the node has children
                node['has_children'] = True if children_dict[node['self_id']] else False

                # check if the node has grandchildren
                has_grand_children = False
                for child in children_dict[node['self_id']]:
                    if children_dict[child]:
                        has_grand_children = True
                        break
                node['has_grand_children'] = has_grand_children

            return data

        if pnl_or_bs_report:
            data['report_lines'] = set_children_grand_children(report_lines)
        #### END ####

        #### Hide Empty Lines in P&L and BS (CR-9 #16) | Rajeel | 17/03/2023 ####
        if pnl_or_bs_report and not self.enable_filter and self.hide_empty_line:
            parents = set(map(lambda x: x['parent'], data['report_lines'])) - {0}
            report_lines_after_remove_empty = []
            a = pd.date_range(date_from, self.date_to, freq='MS').strftime("%b-%Y").tolist()
            for idx, line in enumerate(report_lines):
                include_sub_line = False
                if self.group_by != 'no_grouping':
                    for x in a:
                        if line[x]:
                            include_sub_line = True
                            break
                if not(line['level'] != 1 and line['parent'] in parents and not line['balance'] and not include_sub_line) \
                        or (not line['display_detail'] and line['account_type'] == 'sum'):
                    report_lines_after_remove_empty.append(line)
            data['report_lines'] = report_lines_after_remove_empty
        #### END ####

        #### Margin % in P&L and BS (CR-9 Additional #A3) | Rajeel | 17/03/2023 ####
        data['form']['show_percent_margin'] = False
        if pnl_or_bs_report and self.show_percent_margin:
            percent_margin_divisor_id = self.account_report_id._get_percent_margin_divisor_record_id()
            if not percent_margin_divisor_id:
                raise UserError('Not Percent Margin Divisor Set')
            enable_filter = self.enable_filter
            data['form']['show_percent_margin'] = True
            for line in data['report_lines']:
                if line['self_id'] == percent_margin_divisor_id:
                    line['margin_divisor'] = True
                    percent_margin_divisor_record = line
                    break
            for idx, line in enumerate(data['report_lines']):
                data['report_lines'][idx]['balance_margin'] = '{:,.2f}'.format(line['balance'] / percent_margin_divisor_record['balance'] * 100)
                if enable_filter:
                    data['report_lines'][idx]['balance_cmp_margin'] = '{:,.2f}'.format(line['balance_cmp'] / percent_margin_divisor_record['balance_cmp'] * 100)
                if self.group_by in ['monthly', 'yearly']:
                    data['report_lines'][idx][f'balance_margin_month'] = {}
                    for month in a:
                        if percent_margin_divisor_record[month] and line[month]:
                            month_margin = line[month] / percent_margin_divisor_record[month] * 100
                        else:
                            month_margin = 0.00
                        if self.group_by == 'monthly':
                            month_margin = '{:,.2f}'.format(month_margin)
                        data['report_lines'][idx][f'balance_margin_month'][month] = month_margin


        for report_line in data['report_lines']:
            if report_line['account_type'] == 'sum' and not report_line['display_detail']:
                # hide amount when type=view and display_detail not set
                report_line.update({
                    'balance': 0, 'debit': 0, 'credit': 0
                })

        data['form']['report_type'] = self.account_report_id.financial_report_menu
        if data['form']['report_type'] == 'balance_sheet' and data['form']['group_by'] == 'monthly':
            valid_months = pd.date_range(self.date_from, datetime.now().date(), freq='MS').strftime("%b-%Y").to_list()
            for report_line in data['report_lines']:
                balance = report_line['balance']
                for month in a[::-1]:
                    if month in valid_months:
                        month_value = report_line[month]
                        report_line[month] = balance
                        balance = balance - month_value

        # yearly
        if data['form']['group_by'] == 'yearly':
            if self.group_by_yearly_type == 'financial':
                date_range = self.get_dates_from_date_range('this_financial_year')
                year_start_month = date_range[0].strftime('%b')
            else:
                year_start_month = 'Jan'
            month_year_dict = assign_year_to_months(a, year_start_month)
            years = sorted(list(set(month_year_dict.values())))
            for report_line in data['report_lines']:
                year_keys = dict.fromkeys(years, 0)
                report_line.update(year_keys)
                if 'balance_margin_month' in report_line:
                    report_line['balance_margin_month'].update(year_keys)
                    if 'margin_divisor' in report_line:
                        data['form']['margin_divisor_yearly'] = year_keys
                for month in a:
                    month_year = month_year_dict[month]
                    report_line[month_year] += report_line[month]
                    if 'balance_margin_month' in report_line:
                        month_margin = report_line['balance_margin_month'][month]
                        if 'margin_divisor' in report_line and month_margin == 100:
                            data['form']['margin_divisor_yearly'][month_year] += 1
                        report_line['balance_margin_month'][month_year] += month_margin


            data['form']['month_list'] = years

        # show percent performance % code
        data['form']['show_percent_performance'] = self.show_percent_performance

        for report_line in data['report_lines']:
            if self.show_percent_performance and data['form']['enable_filter']:
                report_line['performance_percent'] = self.func('calculate_performance',
                                                               before=report_line['balance_cmp'],
                                                               after=report_line['balance'])
                continue

            # code will run only when enable comparison is False
            last_month_balance = None
            report_line['performance_percent'] = {}
            for column in data['form']['month_list']:  # column can be year or month-year
                if self.show_percent_performance:
                    # performance %
                    report_line['performance_percent'][column] = self.func('calculate_performance',
                                                                           before=last_month_balance,
                                                                           after=report_line[column])
                    last_month_balance = report_line[column]

                if data['form']['group_by'] == 'yearly' and self.show_percent_margin:
                    # yearly margin %
                    margin_divisor_year = data['form']['margin_divisor_yearly'][column]
                    if margin_divisor_year:
                        report_line['balance_margin_month'][column] = '{:,.2f}'.format(
                            report_line['balance_margin_month'][column] /
                            margin_divisor_year
                        )
                    else:
                        report_line['balance_margin_month'][column] = '{:,.2f}'.format(
                            report_line['balance_margin_month'][column])


        return data

    @api.model
    def _get_default_report_id(self):
        if self.env.context.get('report_name', False):
            return self.env.context.get('report_name', False)
        return self.env.ref('account_dynamic_reports.ins_account_financial_report_profitandloss0').id

    @api.depends('account_report_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.account_report_id.name or 'Financial Report'
            res.append((record.id, name))
        return res

    def _add_report_heading(self, data):
        report_name = data['form']['account_report_id'][1]
        company_name = data['form']['company_id'][1]
        date_from = data['form']['date_from'].strftime('%d/%m/%Y')
        date_to = data['form']['date_to'].strftime('%d/%m/%Y')
        if 'profit and loss' in report_name.lower():
            report_name = 'INCOME STATEMENT'
        data['form']['report_heading'] = f'{company_name}: {report_name} FROM {date_from} TO {date_to}'
        data['report_name'] = f'{report_name} {date_from} _ {date_to}'

    view_format = fields.Selection([
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal')],
        default='vertical',
        string="Format")
    strict_range = fields.Boolean(
        string='Strict Range',
        default=lambda self: self.env.user.company_id.strict_range)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search(
                                       [('company_id', '=', self.company_id.id)]))
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    enable_filter = fields.Boolean(
        string='Enable Comparison',
        default=False)
    group_by = fields.Selection(
        [("no_grouping", "No Grouping"), ("monthly", "Monthly"), ("yearly", "Yearly")],
        "Group By",
        default="no_grouping",
    )
    group_by_yearly_type = fields.Selection(
        [("financial", "Financial"), ("calendar", "Calendar")],
        "Yearly Type",
        default="financial",
        help="""e.g. Date from = 01/05/2022, Date to = 31/01/2025
Financial: Assuming 01/04 - 31/03 is financial year, so years will be 2022 (01/05/2022 - 31/03/2023), 2023 (01/04/2023 - 31/03/2024), 2024 (01/04/2024 - 31/01/2025)
Calendar: Years will be 2022 (01/05/2022 - 31/12/2022), 2023 (01/01/2023 - 31/12/2023), 2024 (01/01/2024 - 31/12/2024), 2025 (01/01/2025 - 31/01/2025)"""
    )
    account_report_id = fields.Many2one(
        'ins.account.financial.report',
        string='Account Reports',
        required=True, default=_get_default_report_id)

    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=False,
        help="Help to identify debit and credit with balance line for better understanding.")
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags'
    )
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_date')
    label_filter = fields.Char(string='Column Label', default='Comparison Period',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    show_percent_margin = fields.Boolean(string='Margin %', default=False)
    show_percent_performance = fields.Boolean(string='Performance %', default=False)
    hide_empty_line = fields.Boolean(string='Hide Empty Line', default=True)
    view_type = fields.Selection([('xlsx', 'XLSX'), ('ui', 'UI'), ('pdf', 'PDF')])
    include_period_13 = fields.Boolean('Include Period 13 Entries?', default=True)

    @api.model
    def create(self, vals):
        ret = super(InsFinancialReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):
        if vals.get('date_from') or vals.get('date_to'):
            vals.update({'date_range': False})
        if vals.get('date_range'):
            date_from, date_to = self.get_dates_from_date_range(vals.get('date_range'))
            vals.update({'date_from': date_from, 'date_to': date_to})

        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'journal_ids') if type(j) is not list] + vals.get('journal_ids')})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'analytic_ids') if type(j) is not list] + vals.get('analytic_ids')})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})

        if vals.get('analytic_tag_ids'):
            vals.update({'analytic_tag_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'analytic_tag_ids') if type(j) is not list] + vals.get('analytic_tag_ids')})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})

        ret = super(InsFinancialReport, self).write(vals)
        return ret

    def action_pdf(self):
        ''' Button function for Pdf '''
        self.view_type = 'pdf'
        report = self.env.ref('account_dynamic_reports.ins_financial_report_pdf')
        # report.name = safe_eval("'%s - %s/%s' % (object.account_report_id.name,object.date_from,object.date_to)", {'object': self})
        data = self.get_report_values()
        return report.report_action(self, data)

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        self.view_type = 'ui'
        res = {
            'type': 'ir.actions.client',
            'name': 'FR View',
            'tag': 'dynamic.fr',
            'context': {'wizard_id': self.id,
                        'account_report_id': self.account_report_id.id,
                        'ui': True}
        }
        return res
