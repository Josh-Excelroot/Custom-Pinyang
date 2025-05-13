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


class print_customer_statement(models.AbstractModel):
    _inherit = 'report.goexcel_customer_statement.cust_statement_template'

    def get_balance_bf(self, partner):
        curr_company = self.env.user.company_id
        company_currency = curr_company.currency_id
        company_currency_id = company_currency.id
        date_domain = [('date', '<=', partner.overdue_date), ('company_id', '=', curr_company.id)]
        exch_journal = curr_company.currency_exchange_journal_id
        if partner.aging_by == 'due_date':
            date_domain = [('date_maturity', '<=', partner.overdue_date),('company_id', '=', curr_company.id)]
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
            # reversed_balance_move_lines = balance_move_lines.sorted(
            #         key=lambda x: x.date or x.move_id.date)

            query = f""" SELECT json_agg(sub.id) FROM (     
            SELECT id FROM account_move_line WHERE id IN {balance_move_lines._ids + (0,0)} ORDER BY date 
            ) sub; """
            self._cr.execute(query)
            reversed_balance_move_lines = self.env['account.move.line'].browse(self._cr.fetchone()[0])
            if partner.soa_type == 'unpaid_invoices':
                for line in reversed_balance_move_lines:
                    line_info = self.query_fetch(
                        f"select credit,debit,reconciled,amount_residual,amount_residual_currency,currency_id,ref,date,date_maturity from account_move_line where id={line.id}",
                        obj_format=True)
                    if line.is_forex_trade_line(exch_journal): continue
                    invoice_paid = False
                    invoices = self.env['account.invoice'].sudo().search([
                        ('move_id', '=', line.move_id.id), ])
                    invoice_date = line_info.date
                    date_maturity = line_info.date_maturity
                    invoice = False
                    if invoices and not line_info.reconciled:
                        for inv in invoices:
                            inv_residual = self.query_fetch(
                                f'select residual from account_invoice where id={inv.id}',
                                first_column=True)
                            if inv_residual == 0:
                                invoice_paid = True
                            invoice = inv
                            # for credit note
                            if line_info.credit and line_info.credit > 0:
                                invoice_paid = False
                            if not invoice_paid:
                                balance_inv_amt = 0
                                if line_info.debit and invoice:
                                    # get the amount due for partial payment
                                    balance_inv_amt = inv_residual
                                elif line_info and line.credit > 0:
                                    balance_inv_amt = line_info.amount_residual
                                if line.credit and line_info.credit > 0 and line_info.currency_id and line_info.currency_id != company_currency_id:
                                    balance_inv_amt = line_info.amount_residual_currency
                                balance_inv_amt = round(balance_inv_amt, 2)
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
                        if line_info.debit:
                            balance_inv_amt = line_info.amount_residual
                        if line_info.credit:
                            balance_inv_amt = line_info.amount_residual
                        if line_info.currency_id and line_info.currency_id != company_currency_id:
                            balance_inv_amt = line_info.amount_residual_currency
                        balance_amt = round(balance_inv_amt, 2)
                        if balance_amt > 0 or balance_amt < 0:
                            res.append({
                                'ref': 'Balance b/f',
                                'invoice_date': line_info.date,
                                'date_maturity': line_info.date_maturity,
                                'debit': 0.0,
                                'credit': 0.0,
                                'total': balance_amt,
                                'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                            })
                    else:  # if Open journal entry
                        if not line.payment_id and not line_info.reconciled:
                            balance_inv_amt = 0.0
                            if line_info.debit:
                                balance_inv_amt = line_info.amount_residual
                            if line_info.credit:
                                balance_inv_amt = line_info.amount_residual
                            if line_info.currency_id and line_info.currency_id != company_currency_id:
                                balance_inv_amt = line_info.amount_residual_currency
                            balance_amt = round(balance_inv_amt, 2)
                            if balance_amt > 0 or balance_amt < 0:
                                res.append({
                                    'ref': 'Balance b/f',
                                    'invoice_date': line_info.date,
                                    'date_maturity': line_info.date_maturity,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                    'total': balance_amt,
                                    'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                                })

                        elif line.invoice_id and line.reconciled:
                            balance_amt = line.get_line_residual_at_specific_date(partner.overdue_date)
                            balance_amt = round(balance_amt, 2)
                            if balance_amt > 0 or balance_amt < 0:
                                res.append({
                                    'ref': 'Balance b/f',
                                    'invoice_date': line_info.date,
                                    'date_maturity': line_info.date_maturity,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                    'total': balance_amt,
                                    'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                                })
            else:
                domain = [('max_date', '<=', partner.overdue_date)]
                has_usd_payment_for_myr_invoice = partner.has_usd_payment_for_myr_invoice()
                # check_currency = False
                for line in reversed_balance_move_lines:
                    if line.is_forex_trade_line(exch_journal):
                        continue
                    line_info = self.query_fetch(
                        f"select credit,debit,amount_currency,reconciled,amount_residual,amount_residual_currency,balance,currency_id,ref,date,date_maturity from account_move_line where id={line.id}",
                        obj_format=True)

                    invoice_date = line_info.date
                    date_maturity = line_info.date_maturity
                    # if not has_usd_payment_for_myr_invoice and line_info.currency_id :#or line.company_currency_id :#!= self.env.user.company_id.currency_id:
                    if not has_usd_payment_for_myr_invoice and line_info.currency_id and line_info.currency_id != curr_company.currency_id.id:
                        sum_debit = sum(de.amount_currency for de in
                                        partial_obj.search([('credit_move_id', '=', line.id)] + domain))
                        sum_credit = sum(
                            cr.amount_currency for cr in partial_obj.search([('debit_move_id', '=', line.id)] + domain))
                        amount = line_info.amount_currency + sum_debit - sum_credit
                    else:
                        sum_debit = sum(
                            de.amount for de in partial_obj.search([('credit_move_id', '=', line.id)] + domain))
                        sum_credit = sum(
                            cr.amount for cr in partial_obj.search([('debit_move_id', '=', line.id)] + domain))
                        amount = line_info.balance + sum_debit - sum_credit

                    if amount > 0 or amount < 0:
                        res.append({
                            'ref': 'Balance b/f',
                            'invoice_date': invoice_date,
                            'date_maturity': date_maturity,
                            'debit': 0.0,
                            'credit': 0.0,
                            'total': float(amount),
                            'currency_id': (has_usd_payment_for_myr_invoice and line.company_id.currency_id) or line.currency_id or line.company_currency_id or line.company_id.currency_id
                        })
        return res

    def get_lines(self, partner, check_first_line=False):
        """check_first_line: if True then return True whenever there is any printable line"""

        # get bf balance only
        self = self.sudo()
        curr_company = self.env.user.company_id
        company_currency = curr_company.currency_id
        company_currency_id = company_currency.id
        bf_date_domain = [('date', '<', partner.invoice_start_date), ('company_id', '=', curr_company.id)]
        sel_date_domain = [('date', '>=', partner.invoice_start_date), ('date', '<=', partner.overdue_date),
                           ('company_id', '=', curr_company.id)]
        if partner.aging_by == 'due_date':
            bf_date_domain = [('date_maturity', '<', partner.invoice_start_date),
                              ('company_id', '=', curr_company.id)]
            sel_date_domain = [('date_maturity', '>=', partner.invoice_start_date),
                               ('date_maturity', '<=', partner.overdue_date),
                               ('company_id', '=', curr_company.id)]
        bf_domain = [('partner_id', '=', partner.id)] + bf_date_domain
        selected_domain = [('partner_id', '=', partner.id)] + sel_date_domain
        exch_journal = curr_company.currency_exchange_journal_id

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
        balance_total1 = 0.0
        currency_dict = {}
        if balance_move_lines:
            # reversed_balance_move_lines = balance_move_lines.sorted(
            #     key=lambda x: x.date)
            query = f""" SELECT json_agg(sub.id) FROM (     
            SELECT id FROM account_move_line WHERE id IN {balance_move_lines._ids + (0,0)} ORDER BY date 
            ) sub; """
            self._cr.execute(query)
            reversed_balance_move_lines = self.env['account.move.line'].browse(self._cr.fetchone()[0])
            # Canon - 2 Jun 2023 Start
            company_currency = self.env.user.currency_id
            has_usd_payment_for_myr_invoice = partner.has_usd_payment_for_myr_invoice()
            check_currency = False
            for line in reversed_balance_move_lines:
                # Ahmad Zaman - 4/4/25 - Fixed amount_currency error
                line_info = self.query_fetch(
                    f"select credit,amount_currency,debit,reconciled,amount_residual,amount_residual_currency,currency_id,ref,date,date_maturity,payment_id,invoice_id from account_move_line where id={line.id}",
                    obj_format=True)
                if not has_usd_payment_for_myr_invoice:
                    check_currency = True
                    if not line_info.currency_id or line_info.currency_id == company_currency_id:
                        check_currency = False
                if line.is_forex_trade_line(exch_journal):
                    continue

                balance_inv_amt = 0.0
                balance_paid_amt = 0.0

                if line_info.debit:
                    if check_currency:
                        balance_inv_amt = line_info.amount_currency
                    else:
                        balance_inv_amt = line_info.debit
                    if line.payment_id:
                        balance_inv_amt = self.get_line_amount(line, balance_inv_amt)
                if line_info.credit:
                    if check_currency:
                        balance_paid_amt = line_info.amount_currency * -1
                    else:
                        balance_paid_amt = line_info.credit
                    if line_info.payment_id:
                        balance_paid_amt = self.get_line_amount(line, balance_paid_amt)

                total_inv_amt += round(balance_inv_amt, 2)
                if balance_inv_amt < 0:  # for credit note
                    # balance_paid_amt = math.fabs(balance_paid_amt)
                    balance_paid_amt = round(math.fabs(balance_paid_amt), 2)
                    balance_inv_amt = 0
                total_paid_amt += round(balance_paid_amt, 2)
                balance_total += float(balance_inv_amt - balance_paid_amt)
                if line_info.currency_id and check_currency:
                    balance_total1 += line_info.amount_currency
            if balance_total1 > 0:
                balance_total = balance_total1
            # Canon - 2 Jun 2023 Start
            if balance_total > 0 or balance_total < 0:
                if check_first_line:
                    return True
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
            # reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
            query = f""" SELECT json_agg(sub.id) FROM (     
            SELECT id FROM account_move_line WHERE id IN {move_lines._ids + (0,0)} ORDER BY date 
            ) sub; """
            self._cr.execute(query)
            reversed_move_lines = self.env['account.move.line'].browse(self._cr.fetchone()[0])

            company_currency = self.env.user.currency_id
            has_usd_payment_for_myr_invoice = partner.has_usd_payment_for_myr_invoice()
            payments_in_soa = []
            for line in reversed_move_lines:
                line_info = self.query_fetch(
                    f"select credit,debit,reconciled,amount_residual,amount_residual_currency,amount_currency,currency_id,ref,date,date_maturity,payment_id from account_move_line where id={line.id}",
                    obj_format=True)
                if line_info.payment_id in payments_in_soa:
                    continue
                check_currency = False
                if not has_usd_payment_for_myr_invoice:
                    check_currency = True
                    if not line_info.currency_id or line_info.currency_id == company_currency_id:
                        check_currency = False
                inv_amt = 0.0
                paid_amt = 0.0
                over_due = False
                if line_info.debit:
                    if check_currency:
                        inv_amt = line_info.amount_currency
                    else:
                        inv_amt = line_info.debit
                if line_info.credit:
                    if check_currency:
                        paid_amt = line_info.amount_currency * -1
                    else:
                        paid_amt = line_info.credit
                    if inv_amt > 0:
                        if date.today() > line_info.date_maturity:
                            over_due = True
                total = 0.0
                inv_amt = round(inv_amt, 2)
                if inv_amt < 0:  # for credit note
                    paid_amt = math.fabs(paid_amt)
                    paid_amt = round(paid_amt, 2)
                    inv_amt = 0

                """
                # Canon
                if line.currency_id:
                    inv_amt = line.amount_currency
                    paid_amt = 0
                if line.currency_id:
                    inv_amt = 0
                    paid_amt = line.amount_currency
                """

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
                is_invoice = False
                is_payment = False
                is_contra_payment = False
                is_je_payment = False
                is_je_invoice = False
                is_trade_line = False  # creditor line or debtor line
                for invoice in invoices:
                    invoice_info = self.query_fetch(
                        f'select type,reference,origin,number,amount_total from account_invoice where id={invoice.id}',
                        obj_format=True)
                    payment_term = invoice.payment_term_id.name
                    invoice_ref = invoice_info.number
                    invoice_original = invoice_info.origin
                    if invoice_info.type == 'out_invoice':
                        payment_ref = invoice_info.origin
                    else:
                        payment_ref = invoice_info.reference

                    quantity__price_unit = self.query_fetch(
                        f"select quantity,price_unit from account_invoice_line where invoice_id={invoice.id} --and sequence=1",
                        first_column=False)
                    if quantity__price_unit:
                        nett_weight = quantity__price_unit[0]
                        unit_price = quantity__price_unit[1]
                    is_invoice = True

                is_forex_trade_line = line.is_forex_trade_line(exch_journal)

                if paid_amt > 0 or line.payment_id:
                    payment = line.payment_id
                    invoice_ref = payment.name
                    if payment.reference:
                        payment_ref = payment.reference

                if line.payment_id:
                    paid_amt = 0
                    # for pi in line.payment_id.payment_invoice_ids:
                    #     if pi.reconcile_amount > 0:
                    #         if pi.invoice_id.exchange_rate_inverse == 0 or line.payment_id.currency_id != line.payment_id.company_id.currency_id:
                    #             paid_amt += pi.reconcile_amount
                    #         else:
                    #             paid_amt += pi.invoice_id.exchange_rate_inverse * pi.reconcile_amount
                    payment = line.payment_id
                    if payment.payment_type == 'inbound':
                        paid_amt = self.get_payment_amount(payment, payment.amount)
                        inv_amt = 0
                    elif payment.payment_type == 'outbound':
                        inv_amt = self.get_payment_amount(payment, payment.amount)
                        paid_amt = 0

                    total = float(inv_amt - paid_amt)
                    payments_in_soa.append(payment.id)

                    is_payment = True
                    if is_forex_trade_line: is_payment = False

                # TS Bug 2/12/2022 Suria - Do not display the exc.gain/loss

                if not is_forex_trade_line and total < 0 and not is_payment:
                    is_invoice = True
                    invoice_ref = line.ref

                line_name = line.name or ''
                move_ref = line.move_id.ref or ''

                if hasattr(line, 'netting_id'):
                    self._cr.execute(f"select netting_id from account_move_line where id={line.id} limit 1")
                    if self._cr.fetchone()[0]:
                        is_contra_payment = True

                if not is_contra_payment and not is_forex_trade_line and not is_invoice and not is_payment:
                    line_account_type = line.account_id.user_type_id.type
                    is_debtor_line = line_account_type == 'receivable' and 'Currency exchange rate difference' not in line_name
                    is_creditor_line = line_account_type == 'payable' and 'Currency exchange rate difference' not in line_name

                    # is_debtor_line = line.account_id.name == 'TRADE DEBTOR' and line.account_id.code == '6010-010' and 'Currency exchange rate difference' not in line_name
                    # is_creditor_line = line.account_id.name == 'TRADE CREDITORS' and line.account_id.code == '7010-010' and 'Currency exchange rate difference' not in line_name

                    # if 'CONTRA' in line_name.upper():
                    #     is_contra_payment = True
                    # elif 'PAYMENT' in line_name.upper():
                    #     is_je_payment = True
                    # else
                    if (partner.account_type == 'ar' and is_debtor_line) \
                            or (partner.account_type == 'ap' and is_creditor_line) \
                            or (partner.account_type == 'both' and (is_creditor_line or is_debtor_line)):
                        is_trade_line = True
                        # if 'CLOSING YR 2020' in move_ref.upper():
                        #     is_je_invoice = True

                if not is_payment:
                    if inv_amt:
                        inv_amt = self.get_line_amount(line, inv_amt)
                    else:
                        paid_amt = self.get_line_amount(line, paid_amt)

                if (inv_amt or paid_amt) and not is_forex_trade_line and (
                        is_invoice or is_payment or is_contra_payment or is_je_payment or is_trade_line):

                    if total and check_first_line:
                        return True

                    res_data = {
                        'date': line.date,
                        'desc': line.ref or '/',
                        'inv_ref': invoice_ref or (is_je_invoice and line.move_id.name) or line.move_id.name or '',
                        'inv_original': invoice_original or '',
                        'nett_weight': nett_weight or '',
                        'unit_price': unit_price or '',
                        'payment_ref': (is_je_invoice and move_ref) or ((
                                                                                    is_contra_payment or is_je_payment or is_trade_line) and f'{line_name} ({line.move_id.name})') or payment_ref or '',
                        'invoice_prod_cat': invoice_prod_cat or '',
                        'ref': line.move_id.name or '',
                        'date_maturity': line.date_maturity,
                        'over_due': over_due,
                        'debit': float(inv_amt),
                        'credit': float(paid_amt),
                        'total': float(total),
                        'payment_term': payment_term,
                        'show_date_maturity': bool(line.invoice_id),
                        'currency_id': (
                                                   has_usd_payment_for_myr_invoice and line.company_id.currency_id) or line.currency_id or line.company_currency_id or line.company_id.currency_id
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

    def get_lines_open(self, partner, check_first_line=False):
        """check_first_line: if True then return True whenever there is any printable line"""

        curr_company = self.env.user.company_id
        company_currency = curr_company.currency_id
        company_currency_id = company_currency.id

        inv_obj_sudo = self.env['account.invoice'].sudo()
        # get open bf balance only
        bf_date_domain = [('date', '<', partner.invoice_start_date), ('company_id', '=', curr_company.id)]
        sel_date_domain = [('date', '>=', partner.invoice_start_date), ('date', '<=', partner.overdue_date),
                           ('company_id', '=', curr_company.id)]
        if partner.aging_by == 'due_date':
            bf_date_domain = [('date_maturity', '<', partner.invoice_start_date),
                              ('company_id', '=', curr_company.id)]
            sel_date_domain = [('date_maturity', '>=', partner.invoice_start_date),
                               ('date_maturity', '<=', partner.overdue_date),
                               ('company_id', '=', curr_company.id)]
        bf_domain = [('partner_id', '=', partner.id)] + bf_date_domain
        selected_domain = [('partner_id', '=', partner.id)] + sel_date_domain

        exch_journal = curr_company.currency_exchange_journal_id

        if partner.account_type == 'ar':
            balance_move_lines = self._lines_get_all_receivable_bf(bf_domain)
        if partner.account_type == 'ap':
            balance_move_lines = self._lines_get_all_payable_bf(bf_domain)
        elif partner.account_type == 'both':
            balance_move_lines = self._lines_get_all_bf(bf_domain)

        currency_dict = {}
        if balance_move_lines:
            # should not include payment
            # reversed_balance_move_lines = balance_move_lines.sorted(
            #     key=lambda x: x.date)
            query = f""" SELECT json_agg(sub.id) FROM (     
            SELECT id FROM account_move_line WHERE id IN {balance_move_lines._ids + (0,0)} ORDER BY date 
            ) sub; """
            self._cr.execute(query)
            reversed_balance_move_lines = self.env['account.move.line'].browse(self._cr.fetchone()[0])

            for line in reversed_balance_move_lines:
                if line.is_forex_trade_line(exch_journal): continue
                # invoice_paid = False
                # invoices = inv_obj_sudo.search([
                #     ('move_id', '=', line.move_id.id), ])
                # invoice = False
                # for inv in invoices:
                #     #print('>>>>>>>>>>>> get_lines_open invoice=', inv.name, ' , residual=', inv.residual)
                #     if inv.residual == 0:
                #         invoice_paid = True
                #     invoice = inv

                invoice_paid = False
                invoice = line.invoice_id
                invoice_residual = False
                if invoice:
                    invoice_residual = line.get_line_residual_at_specific_date()
                    if invoice_residual == 0:
                        invoice_paid = True

                line_info = self.query_fetch(
                    f"select credit,debit,reconciled,amount_residual,amount_residual_currency,currency_id from account_move_line where id={line.id}",
                    obj_format=True)

                # for credit note
                if line_info.credit and line_info.credit > 0:
                    invoice_paid = False
                if not invoice_paid and (not line_info.reconciled or invoice_residual):
                    balance_inv_amt = 0
                    if line_info.debit and invoice:
                        # get the amount due for partial payment
                        balance_inv_amt = invoice_residual
                    elif (line_info.credit and line_info.credit > 0) or (line_info.debit and not invoice):
                        balance_inv_amt = line_info.amount_residual
                    if line_info.currency_id and line_info.currency_id != company_currency_id and (
                            line_info.amount_residual != 0 or (
                            line_info.amount_residual > 0 and line.invoice_id.type == 'out_refund')):
                        balance_inv_amt = line_info.amount_residual_currency

                    balance_inv_amt = round(balance_inv_amt, 2)

                    if balance_inv_amt:
                        if check_first_line:
                            return True

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

        # get the selected date
        date_res = {}
        if move_lines:
            # should not include payment
            # reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
            query = f""" SELECT json_agg(sub.id) FROM (     
            SELECT id FROM account_move_line WHERE id IN {move_lines._ids + (0,0)} ORDER BY date 
            ) sub; """
            self._cr.execute(query)
            reversed_move_lines = self.env['account.move.line'].browse(self._cr.fetchone()[0])

            for line in reversed_move_lines:
                invoices = inv_obj_sudo.search(
                    [('move_id', '=', line.move_id.id)])

                if line.is_forex_trade_line(exch_journal): continue
                line_info = self.query_fetch(
                    f"select credit,debit,reconciled,amount_residual,amount_residual_currency,currency_id,ref,date,date_maturity from account_move_line where id={line.id}",
                    obj_format=True)

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

                    invoice_info = self.query_fetch(
                        f'select type,reference,origin,number,amount_total from account_invoice where id={invoice.id}',
                        obj_format=True)
                    payment_term = invoice.payment_term_id.name
                    balance_inv_amt = 0
                    total_credit = 0
                    balance = 0.0
                    residual = invoice_info.amount_total
                    reconciles = self.query_fetch(
                        f'select max_date,amount,amount_currency from account_partial_reconcile where credit_move_id={line.id} or debit_move_id={line.id}',
                        fetchall=True, obj_format=True)
                    for reconcile in reconciles:
                        if reconcile.max_date <= partner.overdue_date:
                            if line_info.currency_id and line_info.currency_id != company_currency_id:
                                residual -= reconcile.amount_currency
                            else:
                                residual -= reconcile.amount
                    residual = round(residual, 2)
                    if residual == 0:
                        invoice_paid = True
                    if line.invoice_id.type in ['out_invoice',
                                                'in_invoice'] and line_info.credit and line_info.credit > 0:
                        invoice_paid = False
                    if not invoice_paid:
                        if invoice:
                            invoice_original = invoice.origin
                            invoice_ref = invoice.number
                            # TODO BHL
                            if invoice.type == 'out_invoice':
                                payment_ref = invoice.origin
                            else:
                                payment_ref = invoice.reference
                            if line_info.debit:
                                balance_inv_amt = residual
                            elif line_info.credit:
                                total_credit = residual
                                # if line.currency_id and line.currency_id != self.env.user.company_id.currency_id:
                                #     total_credit = line.amount_residual_currency
                                # else:
                                #     total_credit = line.amount_residual

                        elif line.payment_id:
                            invoice_original = line.payment_id.name
                            invoice_ref = line.payment_id.name
                            payment_ref = line.payment_id.reference
                            if line_info.currency_id and line_info.currency_id != company_currency_id:
                                total_credit = line_info.amount_residual_currency
                            else:
                                total_credit = line_info.amount_residual

                        # TS - 11/10/2022 - Fixed when the USD CN has paid, but appear in SOA
                        # if line.currency_id and line.currency_id != self.env.user.company_id.currency_id and line.amount_residual>0:
                        #     balance_inv_amt = line.amount_residual_currency
                        balance = total_credit + balance_inv_amt
                        if invoice.type == 'out_refund':
                            balance = -balance
                        over_due = line_info.date
                        date_maturity = line_info.date_maturity

                        if balance:
                            if check_first_line:
                                return True
                            res_data = {
                                'date': date,
                                'desc': line_info.ref or '/',
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
                                'total': round(balance_inv_amt, 2) - total_credit,
                                'currency_id': invoice.currency_id,
                                'payment_term': payment_term
                            }
                            if line_info.date not in date_res:
                                date_res.update({line_info.date: [res_data]})
                            else:
                                flag = False
                                for d_line in date_res[line_info.date]:
                                    if d_line.get('inv_ref') == invoice_ref:
                                        d_line['debit'] += round(
                                            balance_inv_amt, 2)
                                        d_line['credit'] += total_credit
                                        d_line['total'] += balance
                                        flag = True
                                if not flag:
                                    date_res[line_info.date] = [
                                                                   res_data] + date_res[line_info.date]
                if not invoices and not line_info.reconciled:
                    amount = line_info.amount_residual
                    if line_info.currency_id and line_info.currency_id != company_currency_id and (
                            line_info.amount_residual != 0 or (
                            line_info.amount_residual > 0 and line.invoice_id.type == 'out_refund')):
                        amount = line_info.amount_residual_currency
                    if line.payment_id and not line.payment_id.unreconcile_amount:
                        continue
                    # print('>>>>>>>>>>>> get_lines_open 22 invoice amt=', amount,
                    #       ' , ref=', line.ref)
                    amount = math.fabs(round(amount, 2))
                    if amount:
                        if check_first_line:
                            return True
                        res_data = {
                            'date': date,
                            'desc': line_info.ref or '/',
                            'inv_ref': invoice_ref or line.move_id.name or '',
                            'inv_original': invoice_original or '',
                            'nett_weight': nett_weight or '',
                            'unit_price': unit_price or '',
                            'payment_ref': payment_ref or line.ref or '',
                            'invoice_prod_cat': invoice_prod_cat or '',
                            'ref': line.move_id.name or '',
                            'date_maturity': line_info.date_maturity,
                            'over_due': line_info.date,
                            'debit': round(amount, 2) if line_info.debit else 0.0,
                            'credit': round(amount, 2) if line_info.credit else 0.0,
                            'currency_id': line.currency_id or line.company_currency_id or line.company_id.currency_id
                        }
                        res_data['total'] = res_data['debit'] - res_data['credit']
                        if line_info.date not in date_res:
                            date_res.update({line_info.date: [res_data]})
                        else:
                            flag = False
                            for d_line in date_res[line_info.date]:
                                if d_line.get('inv_ref') and d_line.get('inv_ref') == invoice_ref:
                                    d_line['debit'] += amount if line_info.debit else 0.0
                                    d_line['credit'] += amount if line_info.credit else 0.0
                                    d_line['total'] += amount
                                    flag = True
                            if not flag:
                                date_res[line_info.date] = [
                                                               res_data] + date_res[line.date]
        for key, vals in date_res.items():
            for v in sorted(vals, key=lambda d: d['inv_ref']):
                if v['currency_id'] in currency_dict:
                    currency_dict[v['currency_id']].append(v)
                else:
                    currency_dict.update({v['currency_id']: [v]})

        return currency_dict

    def get_payment_amount(self, payment, amount):
        return amount

    def get_line_amount(self, line, amount):
        return amount


class customer_statement(models.TransientModel):
    _inherit = "customer.statement"

    @api.onchange('soa_type')
    def set_default_invoice_date(self):
        if self.soa_type == 'unpaid_invoices':
            default_soa_invoice_date_type = self.env.user.company_id.soa_invoice_date_type
            if default_soa_invoice_date_type == 'beginning':
                self.invoice_start_date = '2021-01-01'


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def is_forex_trade_line(self, exch_journal):
        if exch_journal and self.journal_id == exch_journal:
            return True
        if self.name and ('audit adjustment for' in self.name.lower() or 'Currency exchange rate difference' in self.name):
            return True
        sibling_move_lines = self.env['report.goexcel_customer_statement.cust_statement_template'].query_fetch(
            f"""select acc.name as account_name,aml.credit,aml.debit from account_move_line aml 
            left join account_account acc on acc.id=aml.account_id where move_id={self.move_id.id} """,
            fetchall=True,obj_format=True)
        for sml in sibling_move_lines:
            if 'forex' in sml.account_name.lower() and (self.credit == sml.debit != 0 or self.debit == sml.credit != 0):
                return True
        return False

    def get_line_residual_at_specific_date(line, date=False):
        query_fetcher = line.env['report.goexcel_customer_statement.cust_statement_template'].query_fetch
        line_info = query_fetcher(
                    f"select credit,debit,reconciled,currency_id,amount_currency from account_move_line where id={line.id}",
                    obj_format=True)
        if line_info.currency_id and line_info.currency_id != line.env.user.company_id.currency_id:
            residual = line_info.amount_currency
        else:
            residual = (line_info.credit or line_info.debit)
        compare_date = date or line.partner_id.overdue_date
        reconciles = line.env['report.goexcel_customer_statement.cust_statement_template'].query_fetch(
            f"select id,max_date,amount,amount_currency from account_partial_reconcile where max_date <= '{compare_date}' and (credit_move_id={line.id} or debit_move_id={line.id})",
            fetchall=True, obj_format=True)
        for reconcile in reconciles:
            line._cr.execute(f"select max_date from account_partial_reconcile where id={reconcile.id} limit 1")
            max_date = line._cr.fetchone()
            if max_date and max_date[0] <= compare_date:
                if line.currency_id and line.currency_id != line.env.user.company_id.currency_id:
                    residual -= reconcile.amount_currency
                else:
                    residual -= reconcile.amount
        return residual


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def has_usd_payment_for_myr_invoice(self):
        if self.account_type == 'ar':
            i_type = "('inbound')"
        elif self.account_type == 'ap':
            i_type = "('outbound')"
        else:
            i_type = "('outbound', 'inbound')"

        sql = f"""select api.id
from account_payment_invoice api
         left join account_payment p on p.id = api.payment_id
         left join account_move_line aml on p.id = aml.payment_id
         left join account_move am on am.id = aml.move_id
         left join account_invoice i on i.id = api.invoice_id
where i.currency_id != p.currency_id and p.currency_id=2 and am.state='posted' and p.payment_type in {i_type} and am.partner_id={self.id}"""
        sql += " limit 1;"
        self._cr.execute(sql)
        return bool(self._cr.fetchone())
