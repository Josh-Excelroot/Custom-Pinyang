from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from collections import defaultdict

FETCH_RANGE = 2000


class InsAnalyticReport(models.TransientModel):
    _name = "ins.analytic.report"
    _inherit = ['dynamic.reports.mixin']
    _description = "Analytic Report"

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Analytic Report'))
        return res

    reference = fields.Char(string='Filter By Reference')
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags'
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Partners'
    )

    hide_sublines = fields.Boolean(string='Hide Sub-lines')

    @api.model
    def create(self, vals):
        ret = super(InsAnalyticReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):

        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range': False})
        if vals.get('date_range'):
            date_from, date_to = self.get_dates_from_date_range(vals.get('date_range'))
            vals.update({'date_from': date_from, 'date_to': date_to})

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

        if vals.get('partner_ids'):
            vals.update({'partner_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'partner_ids') if type(j) is not list] + vals.get('partner_ids')})
        if vals.get('partner_ids') == []:
            vals.update({'partner_ids': [(5,)]})
        return super(InsAnalyticReport, self).write(vals)

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(
                _('"Date from" must be less than or equal to "Date to"'))
        return True

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})
        filters = {}

        if data.get('analytic_ids', []):
            filters['analytics'] = self.env['account.analytic.account'].browse(
                data.get('analytic_ids', [])).mapped('name')
        else:
            filters['analytics'] = ['All']
        if data.get('analytic_tag_ids', []):
            filters['analytic_tags'] = self.env['account.analytic.tag'].sudo().browse(
                data.get('analytic_tag_ids', [])).mapped('name')
        else:
            filters['analytic_tags'] = ['All']
        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partner_ids', [])).mapped(lambda x: x.name.replace('&', 'and'))
        else:
            filters['partners'] = ['All']

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        filters['analytics_list'] = data.get('analytics_list')
        filters['analytic_tag_list'] = data.get('analytic_tag_list')
        filters['partners_list'] = data.get('partners_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def build_where_clause(self, data=False):
        if not data:
            data = self.get_filters(default_filters={})

        if data:

            WHERE = '(1=1)'

            if data.get('analytic_ids', []):
                WHERE += ' AND an.id IN %s' % str(
                    tuple(data.get('analytic_ids')) + tuple([0]))

            if data.get('analytic_tag_ids', []):
                WHERE += ' AND analtag.tag_id IN %s' % str(
                    tuple(data.get('analytic_tag_ids')) + tuple([0]))

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))

            if data.get('company_id', False):
                WHERE += ' AND anl.company_id = %s' % data.get('company_id')

            return WHERE

    def _compute_debit_credit_balance(self, anl_acc_id=False, date_from=False, date_to=False, tag_ids=[], company_ids=[]):
        Curr = self.env['res.currency']
        analytic_line_obj = self.env['account.analytic.line']
        domain = [('account_id', '=', anl_acc_id)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if tag_ids:
            tag_domain = expression.OR(
                [[('tag_ids', 'in', [tag])] for tag in tag_ids])
            domain = expression.AND([domain, tag_domain])
        if company_ids:
            domain.append(('company_id', 'in', company_ids))

        user_currency = self.env.user.company_id.currency_id
        credit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '>=', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_credit = defaultdict(float)
        for l in credit_groups:
            data_credit[l['account_id'][0]] += Curr.browse(l['currency_id'][0])._convert(
                l['amount'], user_currency, self.env.user.company_id, fields.Date.today())

        debit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '<', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_debit = defaultdict(float)
        for l in debit_groups:
            data_debit[l['account_id'][0]] += Curr.browse(l['currency_id'][0])._convert(
                l['amount'], user_currency, self.env.user.company_id, fields.Date.today())

        return {
            'debit': abs(data_debit.get(anl_acc_id, 0.0)),
            'credit': data_credit.get(anl_acc_id, 0.0),
            'balance': data_credit.get(anl_acc_id, 0.0) - abs(data_debit.get(anl_acc_id, 0.0))
        }

    def process_data(self):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        :return:
        '''
        cr = self.env.cr

        data = self.get_filters(default_filters={})

        WHERE = self.build_where_clause(data)

        company_id = self.env.user.company_id
        analytic_company_domain = [('company_id', '=', company_id.id)]

        if data.get('analytic_ids', []):
            analytic_company_domain.append(
                ('id', 'in', data.get('analytic_ids', [])))

        if data.get('reference', False):
            analytic_company_domain.append(
                ('code', 'ilike', data.get('reference', '')))

        analytic_account_ids = self.env['account.analytic.account'].search(
            analytic_company_domain)

        move_lines = {
            x.name + str(x.id): {
                'name': x.name,
                'code': x.id,
                'analytic_account': '',
                'analytic_account_id': False,
                'reference': '',
                'amount': 0.0,
                'debit': 0.0,
                'credit': 0.0,
                'balance': 0.0,
                'company_currency_id': 0,
                'company_currency_symbol': 'AED',
                'company_currency_precision': 0.0100,
                'company_currency_position': 'after',
                'id': x.id,
                'ids': []
            } for x in sorted(analytic_account_ids, key=lambda a: a.name)
        }  # base for accounts to display
        for analytic in analytic_account_ids:
            company_id = self.env.user.company_id
            currency = analytic.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            ORDER_BY_CURRENT = 'p.name '
            WHERE_CURRENT = WHERE + " AND anl.date >= '%s'" % data.get('date_from') + " AND anl.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND an.id = %s" % analytic.id

            # Fetch data
            # sql = ('''
            #     SELECT
            #         COALESCE(SUM(anl.amount),0) AS amount
            #     FROM account_analytic_line anl
            #     LEFT JOIN account_analytic_account an ON (anl.account_id=an.id)
            #     LEFT JOIN account_analytic_line_tag_rel analtag ON analtag.line_id = anl.id
            #     LEFT JOIN res_partner p ON (anl.partner_id=p.id)
            #     WHERE %s
            #     --GROUP BY p.name, anl.date
            #     --ORDER BY %s
            # ''') % (WHERE_CURRENT, ORDER_BY_CURRENT)
            # cr.execute(sql)
            # current_lines = cr.dictfetchall()

            # Fetch Ids

            sql = ('''
                SELECT
                    anl.id
                FROM account_analytic_line anl
                LEFT JOIN account_analytic_account an ON (anl.account_id=an.id)
                LEFT JOIN account_analytic_line_tag_rel analtag ON analtag.line_id = anl.id
                LEFT JOIN res_partner p ON (anl.partner_id=p.id)
                WHERE %s
                --GROUP BY anl.id, p.name
                --ORDER BY %s
            ''') % (WHERE_CURRENT, ORDER_BY_CURRENT)
            cr.execute(sql)
            current_ids = [9999999, 8888888]
            for current_id in cr.fetchall():
                current_ids.append(current_id[0])
            key_c = analytic.name + str(analytic.id)

            # Get debit, credit and balance from dedicated method

            figures = self._compute_debit_credit_balance(
                analytic.id,
                data.get('date_from'),
                data.get('date_to'),
                data.get('analytic_tag_ids'),
                [data.get('company_id')])

            move_lines[key_c]['analytic_account'] = analytic.name
            move_lines[key_c]['analytic_account_id'] = analytic.id
            move_lines[key_c]['reference'] = analytic.code or ''
            move_lines[key_c]['amount'] = 10

            move_lines[key_c]['debit'] = figures['debit']
            move_lines[key_c]['credit'] = figures['credit']
            move_lines[key_c]['balance'] = figures['balance']

            move_lines[key_c]['ids'] = current_ids
            move_lines[key_c]['partner'] = analytic.partner_id and analytic.partner_id.name or ''
            move_lines[key_c]['partner_id'] = analytic.partner_id and analytic.partner_id.id or False
            move_lines[key_c]['company_currency_id'] = currency.id
            move_lines[key_c]['company_currency_symbol'] = symbol
            move_lines[key_c]['company_currency_precision'] = rounding
            move_lines[key_c]['company_currency_position'] = position

        final_balance = 0.0
        if move_lines:
            for line in move_lines.copy():
                if not move_lines[line]['balance']:
                    move_lines.pop(line)
                else:
                    final_balance += move_lines[line]['balance']

        return move_lines, final_balance

    def get_page_list(self, total_count):
        '''
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        '''
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i+1 for i in range(0, int(page_count))] or []

    def get_filters(self, default_filters={}):
        # TS - fix the bug that the user must select the empty date_range if want to use the start_date and end_date
        # self.onchange_date_range()
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('customer', '=', True),
                                  ('supplier', '=', True),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]
        analytics = self.analytic_ids if self.analytic_ids else self.env['account.analytic.account'].search(
            company_domain)
        analytic_tags = self.analytic_tag_ids if self.analytic_tag_ids else self.env['account.analytic.tag'].sudo().search(
            ['|', ('company_id', '=', company_id.id), ('company_id', '=', False)])
        partners = self.partner_ids if self.partner_ids else self.env['res.partner'].search(
            partner_company_domain)

        filter_dict = {
            'analytic_ids': self.analytic_ids.ids,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,

            'partners_list': self.create_query_and_fetch('res_partner', "id,REPLACE(name, '&', 'and')", f'id in {partners._ids + (0,0)}', fetchall=True, first_column=False),
            'analytics_list': self.create_query_and_fetch('account_analytic_account', 'id,name', f'id in {analytics._ids + (0,0)}', fetchall=True, first_column=False),
            'analytic_tag_list': self.create_query_and_fetch('account_analytic_tag', 'id,name', f'id in {analytic_tags._ids + (0,0)}', fetchall=True, first_column=False),
            'company_name': self.company_id and self.company_id.name,
            'reference': self.reference or ''
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_from_journal_items(self):
        account_data = []
        total_balance = 0
        res_partner_browse = self.env['res.partner'].sudo().browse
        account_move_line_analytic_tag_relation_table = self.env['account.move.line']._fields[
            'analytic_tag_ids'].relation
        company_id = self.env.user.company_id
        currency = company_id.currency_id
        symbol = currency.symbol
        rounding = currency.rounding
        position = currency.position
        cr = self._cr

        where = f"""rel.account_analytic_tag_id = %s 
        AND aml.date BETWEEN '{self.date_from}' 
        AND '{self.date_to}' 
        AND aml.company_id = {company_id.id} 
       """
        # AND aj.type='sale' AND aml.credit > 0"""
        if self.partner_ids:
            where += f"AND aml.partner_id in {str(tuple(self.partner_ids.ids)).replace(',)',')')}"
        if self.analytic_ids:
            where += f"AND aml.analytic_account_id in {str(tuple(self.analytic_ids.ids)).replace(',)',')')}"

        for analytic_tag in self.analytic_tag_ids or self.analytic_tag_ids.search([]):
            analytic_tag_id = analytic_tag.id
            analytic_tag_name = analytic_tag.name
            analytic_data = {'id': analytic_tag_id, 'name': analytic_tag_name, 'lines': [], 'balance': 0}
            sql = f"""SELECT aml.id, aml.name, rp.name, aml.credit, aml.debit
        FROM {account_move_line_analytic_tag_relation_table} rel
        LEFT JOIN account_move_line aml ON aml.id = rel.account_move_line_id
        LEFT JOIN res_partner rp ON aml.partner_id = rp.id
        LEFT JOIN account_journal aj ON aml.journal_id = aj.id
        WHERE {where % analytic_tag_id}"""
            cr.execute(sql)
            data = cr.fetchall()
            if not self.hide_sublines:
                for id_, ref, partner_name, credit, debit in data:
                    balance = credit - debit
                    analytic_data['lines'].append({
                        'id': id_,
                        'reference': ref,
                        'partner': partner_name and partner_name.replace('&', 'and'),
                        'credit': credit,
                        'debit': debit,
                        'balance': balance,
                        'company_currency_id': currency.id,
                        'company_currency_symbol': symbol,
                        'company_currency_precision': rounding,
                        'company_currency_position': position,
                    })
                    total_balance += balance
                    analytic_data['balance'] += balance
                account_data.append(analytic_data)
            else:
                total_credit = 0.0
                total_debit = 0.0
                for id_, ref, partner_name, credit, debit in data:
                    total_credit += credit
                    total_debit += debit
                    # balance = credit - debit
                analytic_data['lines'].append({
                    'id': [d[0] for d in data],
                    'reference': '-',
                    'partner': '-',
                    'credit': total_credit,
                    'debit': total_debit,
                    'balance': total_credit - total_debit,
                    'company_currency_id': currency.id,
                    'company_currency_symbol': symbol,
                    'company_currency_precision': rounding,
                    'company_currency_position': position,
                })
                # total_balance += balance
                analytic_data['balance'] = total_credit - total_debit
                account_data.append(analytic_data)

        return account_data, total_balance

    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
            # Rajeel | Analytic Report (from Journal Items) | 29/03/23
            # account_lines, final_balance = self.process_data()
            # if not account_lines:
            account_lines, final_balance = self.get_from_journal_items()
            return filters, account_lines, final_balance

    def action_pdf(self):
        filters, account_lines, final_balance = self.get_report_datas()
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_analytic_report').with_context(landscape=True).report_action(
            self, data={'Ledger_data': account_lines,
                        'Filters': filters,
                        'Final_balance': final_balance
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Analytic View',
            'tag': 'dynamic.anl',
            'context': {'wizard_id': self.id}
        }
        return res
