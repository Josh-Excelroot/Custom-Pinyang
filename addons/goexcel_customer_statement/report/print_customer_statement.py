from odoo import models, fields, api
import dateutil.relativedelta
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import calendar
from odoo.tools.misc import formatLang
import math
import logging
_logger = logging.getLogger(__name__)

# todo
# < -- All -->
# get_lines
# _lines_get_all_bf
# _lines_get_all_receivable_selected_date
# todo
# < -- Open invoice -->
# get_lines_open
# _lines_get_all_receivable_bf
# todo
# < -- Aging Group -->
# Group -->
# set_ageing_all
# get_balance_bf/get_lines
# _lines_get_receivable_end_date

receivable = [('account_id.user_type_id.type', '=', 'receivable'), ('move_id.state', '<>', 'draft')]
payabale = [('account_id.user_type_id.type', '=', 'payable'), ('move_id.state', '<>', 'draft')]
both = [('account_id.user_type_id.type', 'in', ['receivable', 'payable']), ('move_id.state', '<>', 'draft')]


class AttrDict(dict):
    """ Dictionary subclass that supports dot notation for accessing attributes. """

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError(f"'AttrDict' object has no attribute '{key}'")


class print_customer_statement(models.AbstractModel):
    _name = 'report.goexcel_customer_statement.cust_statement_template'

    @api.multi
    def get_company_info(self, o):
        if self.env.user.company_id:
            company_info = {
                'image': self.env.user.company_id,
                'name': self.env.user.company_id.name,
                'street': self.env.user.company_id.street,
                'city': str(self.env.user.company_id.city) + ' ' + str(self.env.user.company_id.zip),
                'state': self.env.user.company_id.state_id and self.env.user.company_id.state_id.name,
                'country': self.env.user.company_id.country_id and self.env.user.company_id.country_id.name,
            }
        return company_info

    @api.multi
    def set_amount(self, amount):
        amount = formatLang(self.env, amount)
        return amount

    def get_month_name(self, day, mon, year):
        year = str(year)
        day = str(day)
        if mon == 1:
            return day + ' - ' + 'JAN' + ' - ' + year
        elif mon == 2:
            return day + ' - ' + 'FEB' + ' - ' + year
        elif mon == 3:
            return day + ' - ' + 'MAR' + ' - ' + year
        elif mon == 4:
            return day + ' - ' + 'APR' + ' - ' + year
        elif mon == 5:
            return day + ' - ' + 'MAY' + ' - ' + year
        elif mon == 6:
            return day + ' - ' + 'JUN' + ' - ' + year
        elif mon == 7:
            return day + ' - ' + 'JUL' + ' - ' + year
        elif mon == 8:
            return day + ' - ' + 'AUG' + ' - ' + year
        elif mon == 9:
            return day + ' - ' + 'SEP' + ' - ' + year
        elif mon == 10:
            return day + ' - ' + 'OCT' + ' - ' + year
        elif mon == 11:
            return day + ' - ' + 'NOV' + ' - ' + year
        elif mon == 12:
            return day + ' - ' + 'DEC' + ' - ' + year

    def prepare_bucket_list(self, partner):
        periods = {}
        date_from = partner.overdue_date
        date_from = fields.Date.from_string(date_from)
        bucket_list = [30, 60, 90, 120, 180]
        start = False
        stop = date_from
        name = 'Not Due'
        periods[0] = {
            'bucket': 'As on',
            'name': name,
            'start': '',
            'stop': stop.strftime('%Y-%m-%d'),
        }

        stop = date_from
        final_date = False
        for i in range(5):
            start = stop - relativedelta(days=1)
            stop_day = bucket_list[i]
            if i != 0:
                stop_day = bucket_list[i] - bucket_list[i-1]
            stop = start - relativedelta(days=stop_day)
            name = '0 - ' + str(bucket_list[0]) if i == 0 else str(
                str(bucket_list[i-1] + 1)) + ' - ' + str(bucket_list[i])
            final_date = stop
            periods[i+1] = {
                'bucket': bucket_list[i],
                'name': name,
                'start': start.strftime('%Y-%m-%d'),
                'stop': stop.strftime('%Y-%m-%d'),
            }

        start = final_date - relativedelta(days=1)
        stop = ''
        name = str(180) + ' +'

        periods[6] = {
            'bucket': 'Above',
            'name': name,
            'start': start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return periods

    def set_ageing_all(self, obj):
        move_lines = self.get_balance_bf(obj)
        period_list = self.prepare_bucket_list(obj)
        over_date = obj.overdue_date
        aging_dates = []
        aging_dates_aliases = {}
        aging_table_keys = ['Not Due']
        if obj.aging_group == 'by_month':
            for timedelta_month, aging_key in zip(range(0, 6), ['Current Month', '1 Month', '2 Months', '3 Months', '4 Months', 'Above']):
                d = over_date - dateutil.relativedelta.relativedelta(months=timedelta_month)
                d = datetime(d.year, d.month, 1) + timedelta(days=calendar.monthrange(d.year, d.month)[1] - 1)
                d = d.date()
                aging_dates.append(d)
                aging_dates_aliases[d] = aging_key
                aging_table_keys.append(aging_key)
            # aging_table_keys = ['Not Due', 'Total']
        else:
            for timedelta_days, aging_key in zip(range(0, 151, 30), ['0-30', '31-60', '61-90', '91-120', '121-150', 'Above']):
                d = over_date - timedelta(days=timedelta_days)
                aging_dates.append(d)
                aging_dates_aliases[d] = aging_key
                aging_table_keys.append(aging_key)
            # aging_table_keys = ['Not Due', 'Total']
        aging_table_keys.append('Total')

        currency_dict = {currency: [] for currency in self.env['res.currency'].search([])}
        final_dict = {}
        for ml in move_lines:
            currency_dict[ml['currency_id']].append(ml)

        for currency, move_lines in currency_dict.items():
            currency_aging = dict.fromkeys(aging_dates, 0.0)
            currency_aging.update({'Not Due': 0.0, 'Total': 0.0})
            for move_line in move_lines:
                currency_aging['Total'] += move_line['total']
                not_due = True
                for aging_date in aging_dates[::-1]:
                    if move_line['date_maturity'] <= aging_date:
                        currency_aging[aging_date] += move_line['total']
                        not_due = False
                        break
                if not_due:
                    currency_aging['Not Due'] += move_line['total']

            final_dict[currency] = [{(aging_dates_aliases.get(k, k)): v for k,v in currency_aging.items()}, aging_table_keys]

        a=1
        return final_dict

    def set_ageing_all_v1(self, obj):
        # older version
        move_lines = self.get_balance_bf(obj)
        period_list = self.prepare_bucket_list(obj)
        over_date = obj.overdue_date
        d5 = con5 = False
        if obj.aging_group == 'by_month':
            d1 = over_date - dateutil.relativedelta.relativedelta(months=1)
            d1 = datetime(d1.year, d1.month, 1) + timedelta(days=calendar.monthrange(d1.year, d1.month)[1] - 1)
            d1 = d1.date()
            d2 = over_date - dateutil.relativedelta.relativedelta(months=2)
            d2 = datetime(d2.year, d2.month, 1) + timedelta(days=calendar.monthrange(d2.year, d2.month)[1] - 1)
            d2 = d2.date()
            d3 = over_date - dateutil.relativedelta.relativedelta(months=3)
            d3 = datetime(d3.year, d3.month, 1) + timedelta(days=calendar.monthrange(d3.year, d3.month)[1] - 1)
            d3 = d3.date()
            d4 = over_date - dateutil.relativedelta.relativedelta(months=4)
            d4 = datetime(d4.year, d4.month, 1) + timedelta(days=calendar.monthrange(d4.year, d4.month)[1] - 1)
            d4 = d4.date()
            d5 = over_date - dateutil.relativedelta.relativedelta(months=5)
            d5 = datetime(d5.year, d5.month, 1) + timedelta(days=calendar.monthrange(d5.year, d5.month)[1] - 1)
            d5 = d5.date()
        else:
            d1 = over_date - timedelta(days=30)
            d2 = over_date - timedelta(days=60)
            d3 = over_date - timedelta(days=90)
            d4 = over_date - timedelta(days=120)
            d5 = over_date - timedelta(days=150)
        con1 = 30
        con2 = 60
        con3 = 90
        con4 = 120
        con5 = 150
        f1 = self.get_month_name(over_date.day, over_date.month, over_date.year)
        not_due = 0.0
        f_pe = 0.0  # 0 -30
        s_pe = 0.0  # 31-60
        t_pe = 0.0  # 61-90
        fo_pe = 0.0  # 91-120
        fi_pe = 0.0  # 120 - 150
        l_pe = 0.0  # +150
        total = 0
        ag_date = False
        if obj.soa_type == 'all':
            currency_dict = {}
            final_dict = {}
            for ml in move_lines:
                currency_dict[ml['currency_id']] = currency_dict.get(ml['currency_id'], []) + [ml]

            for currency in self.env['res.currency'].search([]):
                if currency not in currency_dict:
                    currency_dict[currency] = []

            for key, move_lines in currency_dict.items():
                not_due = 0.0
                f_pe = 0.0  # 0 -30
                s_pe = 0.0  # 31-60
                t_pe = 0.0  # 61-90
                fo_pe = 0.0  # 91-120
                fi_pe = 0.0  # 120 - 150
                l_pe = 0.0  # +150
                total = 0
                for line in move_lines:
                    total += line.get('total')
                    if obj.aging_by == 'inv_date':
                        ag_date = line.get('invoice_date')
                    else:
                        ag_date = line.get('date_maturity')
                    if ag_date:
                        due_date = ag_date
                        over_date = obj.overdue_date
                        if over_date != due_date:
                            if not ag_date > obj.overdue_date:
                                days = over_date - due_date
                                days = int(str(days).split(' ')[0])
                            else:  # not due
                                days = -1
                        else:
                            days = 0
                        if obj.aging_group == 'by_month':
                            if line.get('total'):
                                if ag_date <= d5:
                                    l_pe += line.get('total')
                                elif ag_date <= d4:
                                    fi_pe += line.get('total')
                                elif ag_date <= d3:
                                    fo_pe += line.get('total')
                                elif ag_date <= d2:
                                    t_pe += line.get('total')
                                elif ag_date <= d1:
                                    s_pe += line.get('total')
                                else:
                                    f_pe += line.get('total')
                        else:  # by_day
                            if line.get('total'):
                                per = 0
                                for period in period_list:
                                    start_date = period_list[period].get('start')
                                    end_date = period_list[period].get('stop')
                                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else False
                                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else False
                                    if start_date and end_date:
                                        if end_date <= ag_date <= start_date:
                                            per = period
                                            break
                                    elif not start_date:
                                        if ag_date >= end_date:
                                            per = period
                                            break
                                    else:
                                        if ag_date <= start_date:
                                            per = period
                                            break
                                if per == 0:
                                    not_due += line.get('total')
                                elif per == 1:
                                    f_pe += line.get('total')
                                elif per == 2:
                                    s_pe += line.get('total')
                                elif per == 3:
                                    t_pe += line.get('total')
                                elif per == 4:
                                    fo_pe += line.get('total')
                                elif per == 5:
                                    fi_pe += line.get('total')
                                elif per == 6:
                                    l_pe += line.get('total')
                if obj.account_type != 'ap':
                    if l_pe < 0:
                        fi_pe += l_pe
                        l_pe = 0.0
                    if fi_pe < 0:
                        fo_pe += fi_pe
                        fi_pe = 0.0
                    if fo_pe < 0:
                        t_pe += fo_pe
                        fo_pe = 0.0
                    if t_pe < 0:
                        s_pe += t_pe
                        t_pe = 0.0
                    if s_pe < 0:
                        f_pe += s_pe
                        s_pe = 0.0
                    if f_pe < 0:
                        not_due += f_pe
                        f_pe = 0.0
                final_dict.update({
                key: [{
                    'not_due': not_due,
                    f1: f_pe,
                    d1: s_pe,
                    d2: t_pe,
                    d3: fo_pe,
                    d4: fi_pe,
                    d5: l_pe,
                    total: total
                }, ['not_due', f1, d1, d2, d3, d4, d5, total]]
            })
            return final_dict
        else:
            currency_dict = {}
            for ml in move_lines:
                currency_dict[ml['currency_id']] = currency_dict.get(ml['currency_id'], []) + [ml]

            for currency in self.env['res.currency'].search([]):
                if currency not in currency_dict:
                    currency_dict[currency] = []

            final_dict = {}
            for key, vals in currency_dict.items():
                not_due = 0.0
                f_pe = 0.0  # 0 -30
                s_pe = 0.0  # 31-60
                t_pe = 0.0  # 61-90
                fo_pe = 0.0  # 91-120
                fi_pe = 0.0  # 120 - 150
                l_pe = 0.0  # +150
                total = 0
                ag_date = False
                for v in vals:
                    total += v.get('total')
                    if obj.aging_by == 'inv_date':
                        ag_date = v.get('invoice_date')
                    else:
                        ag_date = v.get('date_maturity')
                    if ag_date:
                        due_date = ag_date
                        over_date = obj.overdue_date
                        if over_date != due_date:
                            if not ag_date > obj.overdue_date:
                                days = over_date - due_date
                                days = int(str(days).split(' ')[0])
                            else:  # not due
                                days = -1
                        else:
                            days = 0
                        if obj.aging_group == 'by_month':
                            if v.get('total'):
                                if ag_date <= d5:
                                    l_pe += v.get('total')
                                elif ag_date <= d4:
                                    fi_pe += v.get('total')
                                elif ag_date <= d3:
                                    fo_pe += v.get('total')
                                elif ag_date <= d2:
                                    t_pe += v.get('total')
                                elif ag_date <= d1:
                                    s_pe += v.get('total')
                                else:
                                    f_pe += v.get('total')
                        else:  # by_day
                            if v.get('total'):
                                if days < 0:
                                    not_due += v.get('total')
                                elif days <= con1:
                                    f_pe += v.get('total')
                                elif days <= con2:
                                    s_pe += v.get('total')
                                elif days <= con3:
                                    t_pe += v.get('total')
                                elif days <= con4:
                                    fo_pe += v.get('total')
                                elif days <= con5:
                                    fi_pe += v.get('total')
                                else:
                                    l_pe += v.get('total')

                if obj.account_type != 'ap':
                    if l_pe < 0:
                        fi_pe += l_pe
                        l_pe = 0.0
                    if fi_pe < 0:
                        fo_pe += fi_pe
                        fi_pe = 0.0
                    if fo_pe < 0:
                        t_pe += fo_pe
                        fo_pe = 0.0
                    if t_pe < 0:
                        s_pe += t_pe
                        t_pe = 0.0
                    if s_pe < 0:
                        f_pe += s_pe
                        s_pe = 0.0
                    if f_pe < 0:
                        not_due += f_pe
                        f_pe = 0.0
                final_dict.update({
                    key: [{
                        'not_due': not_due,
                        f1: f_pe,
                        d1: s_pe,
                        d2: t_pe,
                        d3: fo_pe,
                        d4: fi_pe,
                        d5: l_pe,
                        total: total
                    }, ['not_due', f1, d1, d2, d3, d4, d5, total]]
                })
            return final_dict

    # get the bring forward balance
    def _lines_get_all_bf(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + both)
        return move_lines

    # get the bring forward balance
    def _lines_get_all_receivable_bf(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + receivable)
        return move_lines

    # get the bring forward balance
    def _lines_get_all_payable_bf(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + payabale)
        return move_lines

    # get the bring forward balance
    def _lines_get_all_selected_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + both)
        return move_lines

    # get the bring forward balance
    def _lines_get_all_receivable_selected_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + receivable)

        return move_lines

    # get the bring forward balance
    def _lines_get_all_payable_selected_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + payabale)
        return move_lines

    def _lines_get_receivable_end_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + receivable)
        return move_lines

    def _lines_get_payable_end_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + payabale)
        return move_lines

    def _lines_get_all_end_date(self, partner):
        moveline_obj = self.env['account.move.line']
        move_lines = moveline_obj.sudo().search(partner + both)
        return move_lines

    # get the bring forward balance
    def get_balance_bf(self, partner):
        date_domain = [('date', '<=', partner.overdue_date), ('company_id', '=', self.env.user.company_id.id)]
        if partner.aging_by == 'due_date':
            date_domain = [('date_maturity', '<=', partner.overdue_date)]
        bf_domain = [('partner_id', '=', partner.id)] + date_domain
        if partner.account_type == 'ar':
            balance_move_lines = self._lines_get_receivable_end_date(bf_domain)
        if partner.account_type == 'ap':
            balance_move_lines = self._lines_get_payable_end_date(bf_domain)
        elif partner.account_type == 'both':
            balance_move_lines = self._lines_get_all_end_date(bf_domain)

        res = []
        partial_obj = self.env['account.partial.reconcile']
        if balance_move_lines:
            # should not include payment
            reversed_balance_move_lines = balance_move_lines.sorted(
                key=lambda x: x.date)
            if partner.soa_type == 'unpaid_invoices':
                for line in reversed_balance_move_lines:
                    invoice_paid = False
                    invoices = self.env['account.invoice'].sudo().search([
                        ('move_id', '=', line.move_id.id), ])
                    invoice_date = line.date
                    date_maturity = line.date_maturity
                    invoice = False
                    if invoices and not line.reconciled:
                        for inv in invoices:
                            if inv.residual == 0:
                                invoice_paid = True
                            invoice = inv
                            # for credit note
                            if line.credit and line.credit > 0:
                                invoice_paid = False
                            if not invoice_paid:
                                balance_inv_amt = 0
                                if line.debit and invoice:
                                    # get the amount due for partial payment
                                    balance_inv_amt = invoice.residual
                                elif line.credit and line.credit > 0:
                                    balance_inv_amt = line.amount_residual
                                if line.currency_id:
                                    balance_inv_amt = line.amount_currency
                                if balance_inv_amt > 0 or balance_inv_amt < 0:
                                    res.append({
                                        'ref': 'Balance b/f',
                                        'invoice_date': invoice_date,
                                        'date_maturity': date_maturity,
                                        'debit': 0.0,
                                        'credit': 0.0,
                                        'total': float(balance_inv_amt),
                                        'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                                    })
                    elif line.payment_id and not line.reconciled:  # if Payment ID
                        balance_inv_amt = 0.0
                        if line.debit:
                            balance_inv_amt = line.amount_residual
                        if line.credit:
                            balance_inv_amt = line.amount_residual
                        if line.currency_id:
                            balance_inv_amt = line.amount_currency
                        balance_amt = round(balance_inv_amt, 2)
                        #print ("balance_amt", balance_amt)
                        res.append({
                            'ref': 'Balance b/f',
                            'invoice_date': line.date,
                            'date_maturity': line.date_maturity,
                            'debit': 0.0,
                            'credit': 0.0,
                            'total': balance_amt,
                            'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                        })
                    else:  # if Open journal entry
                        if not line.payment_id and not line.reconciled:
                            balance_inv_amt = 0.0
                            if line.debit:
                                balance_inv_amt = line.amount_residual
                            if line.credit:
                                balance_inv_amt = line.amount_residual
                            if line.currency_id:
                                balance_inv_amt = line.amount_currency
                            balance_amt = round(balance_inv_amt, 2)
                            #print ("balance_amt", balance_amt)
                            res.append({
                                'ref': 'Balance b/f',
                                'invoice_date': line.date,
                                'date_maturity': line.date_maturity,
                                'debit': 0.0,
                                'credit': 0.0,
                                'total': balance_amt,
                                'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                            })
            else:
                domain = [('max_date', '<=', partner.overdue_date)]
                for line in reversed_balance_move_lines:
                    invoice_date = line.date
                    date_maturity = line.date_maturity
                    sum_debit = sum(de.amount for de in partial_obj.search([('credit_move_id', '=', line.id)] + domain))
                    sum_credit = sum(cr.amount for cr in partial_obj.search([('debit_move_id', '=', line.id)] + domain))
                    amount = line.balance + sum_debit - sum_credit
                    if amount > 0 or amount < 0:
                        res.append({
                            'ref': 'Balance b/f',
                            'invoice_date': invoice_date,
                            'date_maturity': date_maturity,
                            'debit': 0.0,
                            'credit': 0.0,
                            'total': float(amount),
                            'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                        })
        return res

    # get only the statements for the selected date
    # get All  (Details)
    def get_lines(self, partners):
        for partner in partners:
            # get bf balance only
            balance_move_lines=False
            move_lines=False
            #print('>>>>>>>>>>>>>>>get_lines >>>>>>>>>>>')
            bf_date_domain = [('date', '<', partner.invoice_start_date), ('company_id', '=', self.env.user.company_id.id)]
            sel_date_domain = [('date', '>=', partner.invoice_start_date), ('date', '<=', partner.overdue_date), ('company_id', '=', self.env.user.company_id.id)]
            if partner.aging_by == 'due_date':
                bf_date_domain = [('date_maturity', '<', partner.invoice_start_date)]
                sel_date_domain = [('date_maturity', '>=', partner.invoice_start_date), ('date_maturity', '<=', partner.overdue_date)]
            bf_domain = [('partner_id', '=', partner.id)] + bf_date_domain
            selected_domain = [('partner_id', '=', partner.id)] + sel_date_domain
            if partner.account_type == 'ar':
                balance_move_lines = self._lines_get_all_receivable_bf(bf_domain)
            if partner.account_type == 'ap':
                balance_move_lines = self._lines_get_all_payable_bf(bf_domain)
            elif partner.account_type == 'both':
                balance_move_lines = self._lines_get_all_bf(bf_domain)

            res = []
            total_inv_amt = 0.0
            total_paid_amt = 0.0
            balance_total = 0.0
            currency_dict = {}
            if balance_move_lines:
                reversed_balance_move_lines = balance_move_lines.sorted(
                    key=lambda x: x.date)
                for line in reversed_balance_move_lines:
                    balance_inv_amt = 0.0
                    balance_paid_amt = 0.0
                    if line.debit:
                        balance_inv_amt = line.debit
                    if line.credit:
                        balance_paid_amt = line.credit
                    total_inv_amt += round(balance_inv_amt, 2)
                    if balance_inv_amt < 0:  # for credit note
                        # balance_paid_amt = math.fabs(balance_paid_amt)
                        balance_paid_amt = round(math.fabs(balance_paid_amt), 2)
                        balance_inv_amt = 0
                    total_paid_amt += round(balance_paid_amt, 2)
                    balance_total += float(balance_inv_amt - balance_paid_amt)
                    if line.currency_id:
                        balance_total = line.amount_currency
                if balance_total > 0 or balance_total < 0:
                    dd = {
                        'date': False,
                        'desc': '',
                        'inv_ref': '',
                        'inv_original': '',
                        'nett_weight': '',
                        'unit_price': '',
                        'payment_ref': '',
                        'invoice_prod_cat': '',
                        'ref': 'Balance b/f',
                        'date_maturity': False,
                        'over_due': False,
                        'debit': 0.0,
                        'credit': 0.0,
                        'total': float(balance_total),
                    }
                    res.append(dd)
                    currency_id = line.currency_id or line.company_currency_id or line.company_id.currency_id
                    if currency_id not in currency_dict:
                        currency_dict.update({currency_id: [dd]})
                    else:
                        currency_dict[currency_id][0]['total'] += round(
                            balance_total, 2)
            if partner.account_type == 'ar':
                move_lines = self._lines_get_all_receivable_selected_date(selected_domain)
            if partner.account_type == 'ap':
                move_lines = self._lines_get_all_payable_selected_date(selected_domain)
            elif partner.account_type == 'both':
                move_lines = self._lines_get_all_selected_date(selected_domain)

            # get the selected date
            date_res = {}
            if move_lines:
                reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
                #print('>>>>>>>>>>>>>>>get_lines reversed_move_lines=', reversed_move_lines)
                for line in reversed_move_lines:
                    inv_amt = 0.0
                    paid_amt = 0.0
                    over_due = False
                    if line.debit:
                        inv_amt = line.debit
                    if line.credit:
                        paid_amt = line.credit
                        if inv_amt > 0:
                            if date.today() > line.date_maturity:
                                over_due = True
                    total = 0.0
                    inv_amt = round(inv_amt, 2)
                    if inv_amt < 0:   # for credit note
                        paid_amt = math.fabs(paid_amt)
                        paid_amt = round(paid_amt, 2)
                        inv_amt = 0

                    # Canon
                    if line.currency_id and line.debit != 0.0:
                        inv_amt = line.amount_currency
                        paid_amt = 0
                    if line.currency_id and line.credit != 0.0:
                        inv_amt = 0
                        paid_amt = line.amount_currency * -1

                    total = float(inv_amt - paid_amt)
                    invoices = self.env['account.invoice'].sudo().search(
                        [('move_id', '=', line.move_id.id)])
                    invoice_ref = ''
                    invoice_prod_cat = ''
                    invoice_original = ''
                    nett_weight = 0
                    unit_price = 0
                    payment_ref = ''
                    payment_term = ""
                    #print('>>>>>>>>>>>>>>>get_lines invoices=', invoices)
                    is_invoice = False
                    is_payment = False
                    for invoice in invoices:
                        payment_term = invoice.payment_term_id.name
                        invoice_ref = invoice.number
                        invoice_original = invoice.origin
                        if invoice.type == 'out_invoice':
                            payment_ref = invoice.origin
                        else:
                            payment_ref = invoice.reference
                        inv_lines = invoice.invoice_line_ids.filtered(
                            (lambda i: i.sequence == 1))
                        for inv_line in inv_lines:
                            nett_weight = inv_line.quantity
                            unit_price = inv_line.price_unit
                        is_invoice = True
                    if paid_amt > 0:
                        payments = self.env['account.payment'].search(
                            [('id', '=', line.payment_id.id)])
                        for payment in payments:
                            invoice_ref = payment.name
                            if payment.reference:
                                payment_ref = payment.reference
                            is_payment = True

                    #print('>>>>>>>>>>>> debit=', str(inv_amt), ' , cr=', str(paid_amt))
                    #TS Bug 2/12/2022 Suria - Do not display the exc.gain/loss
                    if is_invoice or is_payment:
                        res_data = {
                            'date': line.date,
                            'desc': line.ref or '/',
                            'inv_ref': invoice_ref or '',
                            'inv_original': invoice_original or '',
                            'nett_weight': nett_weight or '',
                            'unit_price': unit_price or '',
                            'payment_ref': payment_ref or '',
                            'invoice_prod_cat': invoice_prod_cat or '',
                            'ref': line.move_id.name or '',
                            'date_maturity': line.date_maturity,
                            'over_due': over_due,
                            'debit': float(inv_amt),
                            'credit': float(paid_amt),
                            'total': float(total),
                            'payment_term': payment_term,
                            'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                        }
                        if line.date not in date_res:
                            date_res.update({line.date: [res_data]})
                        else:
                            flag = False
                            for d_line in date_res[line.date]:
                                if d_line.get('inv_ref') and d_line.get('inv_ref') == invoice_ref:
                                    d_line['debit'] += float(inv_amt)
                                    d_line['credit'] += float(paid_amt)
                                    d_line['total'] += float(total)
                                    flag = True
                            if not flag:
                                date_res[line.date] = [res_data] + date_res[line.date]
        for key, vals in date_res.items():
            for v in sorted(vals, key=lambda d: d['inv_ref'] if d['inv_ref'] else d['ref']):
                res.append(v)
                if v['currency_id'] in currency_dict:
                    currency_dict[v['currency_id']].append(v)
                else:
                    currency_dict.update({v['currency_id']: [v]})
        return currency_dict

    # get only the statements for the selected date
    # get Open Invoices only (Details)
    #kashif 10nov12: make method to loop over partners
    def get_lines_open(self, partners):
        for partner in partners:
            #print('>>>>>>>>>>>> get_lines_open  >>>>>>>>>>>>')
            inv_obj_sudo = self.env['account.invoice'].sudo()
            # get open bf balance only
            bf_date_domain = [('date', '<', partner.invoice_start_date), ('company_id', '=', self.env.user.company_id.id)]
            sel_date_domain = [('date', '>=', partner.invoice_start_date), ('date', '<=', partner.overdue_date), ('company_id', '=', self.env.user.company_id.id)]
            if partner.aging_by == 'due_date':
                bf_date_domain = [('date_maturity', '<', partner.invoice_start_date)]
                sel_date_domain = [('date_maturity', '>=', partner.invoice_start_date), ('date_maturity', '<=', partner.overdue_date)]
            bf_domain = [('partner_id', '=', partner.id)] + bf_date_domain
            selected_domain = [('partner_id', '=', partner.id)] + sel_date_domain
            if partner.account_type == 'ar':
                balance_move_lines = self._lines_get_all_receivable_bf(bf_domain)
            if partner.account_type == 'ap':
                balance_move_lines = self._lines_get_all_payable_bf(bf_domain)
            elif partner.account_type == 'both':
                balance_move_lines = self._lines_get_all_bf(bf_domain)
            #print('>>>>>>>>>>>> get_lines_open balance_move_lines=', balance_move_lines)
            currency_dict = {}
            if balance_move_lines:
                # should not include payment
                reversed_balance_move_lines = balance_move_lines.sorted(
                    key=lambda x: x.date)
                #print('>>>>>>>>>>>> get_lines_open Vendor bill/VCN reversed_balance_move_lines=', reversed_balance_move_lines)
                for line in reversed_balance_move_lines:
                    invoice_paid = False
                    invoices = inv_obj_sudo.search([
                        ('move_id', '=', line.move_id.id), ])
                    invoice = False
                    for inv in invoices:
                        #print('>>>>>>>>>>>> get_lines_open invoice=', inv.name, ' , residual=', inv.residual)
                        if inv.residual == 0:
                            invoice_paid = True
                        invoice = inv
                    # for credit note
                    if line.credit and line.credit > 0:
                        #print('>>>>>>>>>>>> get_lines_open CN=', inv.name, ' , residual=', inv.residual)
                        invoice_paid = False
                    if not invoice_paid and not line.reconciled:
                        balance_inv_amt = 0
                        if line.debit and invoice:
                            # get the amount due for partial payment
                            balance_inv_amt = invoice.residual
                        elif (line.credit and line.credit > 0) or (line.debit and not invoice):
                            balance_inv_amt = line.amount_residual
                        if line.currency_id:
                            balance_inv_amt = line.amount_currency
                        dd = {
                            'date': False,
                            'desc': '',
                            'inv_ref': '',
                            'inv_original': '',
                            'nett_weight': '',
                            'unit_price': '',
                            'payment_ref': '',
                            'invoice_prod_cat': '',
                            'ref': 'Balance b/f',
                            'date_maturity': False,
                            'over_due': False,
                            'debit': 0.0,
                            'credit': 0.0,
                            'total': round(balance_inv_amt, 2),
                        }
                        currency_id = line.currency_id or line.company_currency_id or line.company_id.currency_id
                        if currency_id not in currency_dict:
                            currency_dict.update({currency_id: [dd]})
                        else:
                            currency_dict[currency_id][0]['total'] += round(
                                balance_inv_amt, 2)

            if partner.account_type == 'ar':
                move_lines = self._lines_get_all_receivable_selected_date(selected_domain)
            if partner.account_type == 'ap':
                move_lines = self._lines_get_all_payable_selected_date(selected_domain)
            elif partner.account_type == 'both':
                move_lines = self._lines_get_all_selected_date(selected_domain)

            #print('>>>>>>>>>>>> Invoice/CN get_lines_open move_lines=', move_lines)
            # get the selected date
            date_res = {}
            if move_lines:
                # should not include payment
                reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
                for line in reversed_move_lines:
                    invoices = inv_obj_sudo.search(
                        [('move_id', '=', line.move_id.id)])
                    invoice_paid = False
                    date = line.date
                    invoice_ref = ''
                    invoice_prod_cat = ''
                    invoice_original = ''
                    nett_weight = 0
                    unit_price = 0
                    payment_ref = ''
                    payment_term = ""
                    total_credit = 0.0

                    for invoice in invoices:
                        #print('>>>>>>>>>>>> get_lines_open invoice=', invoice.move_id.name, ' , residual=', invoice.residual,
                        #      ' , line.credit=', line.credit)
                        payment_term = invoice.payment_term_id.name
                        balance_inv_amt = 0
                        total_credit = 0
                        balance = 0.0
                        if invoice.residual == 0:
                            invoice_paid = True
                        if line.credit and line.credit > 0:
                            invoice_paid = False
                        if not invoice_paid:
                            if invoice:
                                invoice_original = invoice.origin
                                invoice_ref = invoice.number
                                #TODO BHL
                                if invoice.type == 'out_invoice':
                                    payment_ref = invoice.origin
                                else:
                                    payment_ref = invoice.reference
                                if line.debit:
                                    balance_inv_amt = invoice.residual
                                elif line.credit:
                                    total_credit = line.amount_residual
                                #print('>>>>>>>>>>>> get_lines_open invoice balance_inv_amt=', balance_inv_amt,
                                #      ' , total_credit=', total_credit)
                            elif line.payment_id:
                                invoice_original = line.payment_id.name
                                invoice_ref = line.payment_id.name
                                payment_ref = line.payment_id.reference
                                total_credit = line.amount_residual
                                #print('>>>>>>>>>>>> get_lines_open invoice line.amount_residual=', line.amount_residual,
                                #     ' , total_credit=', total_credit)
                            #TS - 11/10/2022 - Fixed when the USD CN has paid, but appear in SOA
                            if line.currency_id and line.amount_residual>0:
                                balance_inv_amt = line.amount_currency
                            balance = total_credit + balance_inv_amt
                            over_due = line.date
                            date_maturity = line.date_maturity
                            #print('>>>>>>>>>>>> get_lines_open invoice 3 balance_inv_amt=', round(balance_inv_amt, 2),
                            #      ' , balance=', balance)
                            res_data = {
                                'date': date,
                                'desc': line.ref or '/',
                                'inv_ref': invoice_ref or '',
                                'inv_original': invoice_original or '',
                                'nett_weight': nett_weight or '',
                                'unit_price': unit_price or '',
                                'payment_ref': payment_ref or '',
                                'invoice_prod_cat': invoice_prod_cat or '',
                                'ref': line.move_id.name or '',
                                'date_maturity': date_maturity,
                                'over_due': over_due,
                                'debit': round(balance_inv_amt, 2),
                                'credit': total_credit,
                                'total': balance,
                                'currency_id': invoice.currency_id,
                                'payment_term': payment_term
                            }
                            if line.date not in date_res:
                                date_res.update({line.date: [res_data]})
                            else:
                                flag = False
                                for d_line in date_res[line.date]:
                                    if d_line.get('inv_ref') == invoice_ref:
                                        d_line['debit'] += round(
                                            balance_inv_amt, 2)
                                        d_line['credit'] += total_credit
                                        d_line['total'] += balance
                                        flag = True
                                if not flag:
                                    date_res[line.date] = [
                                        res_data] + date_res[line.date]
                    if not invoices and not line.reconciled:
                        amount = line.amount_residual
                        if line.currency_id:
                            amount = line.amount_currency
                        # print('>>>>>>>>>>>> get_lines_open 22 invoice amt=', amount,
                        #       ' , ref=', line.ref)
                        res_data = {
                            'date': date,
                            'desc': line.ref or '/',
                            'inv_ref': invoice_ref or '',
                            'inv_original': invoice_original or '',
                            'nett_weight': nett_weight or '',
                            'unit_price': unit_price or '',
                            'payment_ref': payment_ref or '',
                            'invoice_prod_cat': invoice_prod_cat or '',
                            'ref': line.move_id.name or '',
                            'date_maturity': line.date_maturity,
                            'over_due': line.date,
                            'debit': round(amount, 2) if line.debit else 0.0,
                            'credit': round(amount, 2) if line.credit else 0.0,
                            'total': amount,
                            'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                        }
                        if line.date not in date_res:
                            date_res.update({line.date: [res_data]})
                        else:
                            flag = False
                            for d_line in date_res[line.date]:
                                if d_line.get('inv_ref') and d_line.get('inv_ref') == invoice_ref:
                                    d_line['debit'] += amount if line.debit else 0.0
                                    d_line['credit'] += amount if line.credit else 0.0
                                    d_line['total'] += amount
                                    flag = True
                            if not flag:
                                date_res[line.date] = [
                                    res_data] + date_res[line.date]
        for key, vals in date_res.items():
            for v in sorted(vals, key=lambda d: d['inv_ref']):
                if v['currency_id'] in currency_dict:
                    currency_dict[v['currency_id']].append(v)
                else:
                    currency_dict.update({v['currency_id']: [v]})
        #print(currency_dict)
        return currency_dict

    def extract_ageing_data_list(self, ageing, ageing_group):
        if type(ageing) == dict:
            ageing = list(ageing.values())[0]
        ageing_data_list = list(ageing[0].values())
        if ageing_group == 'by_months':
            ageing_data_list = ageing_data_list[1:]
        return ageing_data_list

    @api.multi
    def _get_report_values(self, docids, data=None):
        partner_id = self._context.get('default_res_id')
        if partner_id:
            partner_ids = self.env['res.partner'].sudo().browse(
                self._context.get('default_res_id'))
            return {
                'doc_ids': partner_id,
                'doc_model': 'res.partner',
                'docs': partner_ids,
                'print_partner_ref': True if  'print_partner_ref' in data else False,
                'get_lines': self.get_lines,
                'get_lines_open': self.get_lines_open,
                'set_ageing_all': self.set_ageing_all,
                'set_amount': self.set_amount,
                'get_company_info': self.get_company_info,
                'get_selected': self._lines_get_all_selected_date,
                'soa_note': self.env.user.company_id.soa_note,
                'extract_ageing_data_list': self.extract_ageing_data_list
            }

        else:
            docs = self.env['res.partner'].sudo().browse(data['form'])
            return {
                'doc_ids': data['ids'],
                'doc_model': 'res.partner',
                'docs': docs,
                'print_partner_ref': data['print_partner_ref'],
                'get_lines': self.get_lines,
                'get_lines_open': self.get_lines_open,
                'set_ageing_all': self.set_ageing_all,
                'set_amount': self.set_amount,
                'get_company_info': self.get_company_info,
                'get_selected': self._lines_get_all_selected_date,
                'soa_note': self.env.user.company_id.soa_note,
                'extract_ageing_data_list': self.extract_ageing_data_list
            }

    def query_fetch(self, query, params=None, fetchall=False, first_column=True, obj_format=False):
        self._cr.execute(query, params)
        if fetchall:
            if obj_format:
                return [AttrDict(d) for d in self._cr.dictfetchall()]
            else:
                res = self._cr.fetchall()
                if res:
                    if first_column:
                        return [r[0] for r in res]
                return res

        else:
            if obj_format:
                res = self._cr.dictfetchone()
                if not res:
                    res = {}
                return AttrDict(res)
            else:
                res = self._cr.fetchone()
                if res:
                    if first_column:
                        return res[0]
                return res
