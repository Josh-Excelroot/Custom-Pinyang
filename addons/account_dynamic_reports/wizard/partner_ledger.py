from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

FETCH_RANGE = 2000


class InsPartnerLedger(models.TransientModel):
    _name = "ins.partner.ledger"
    _inherit = ['dynamic.reports.mixin']
    _description = "Partner Ledger"

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Partner Ledger'))
        return res

    @api.model
    def default_get(self, fields):
        res = super(InsPartnerLedger, self).default_get(fields)
        company = self.company_id.browse(res.get('company_id'))
        if 'target_moves' in fields and company.unposted_entries_dynamic_reports:
            res['target_moves'] = 'all_entries'
        return res

    target_moves = fields.Selection(
        [('all_entries', 'All entries'),
         ('posted_only', 'Posted Only')], string='Target Moves',
        default='posted_only', required=True
    )
    display_accounts = fields.Selection(
        [('all', 'All'),
         ('balance_not_zero', 'With balance not equal to zero')], string='Display accounts',
        default='balance_not_zero', required=True
    )
    balance_less_than_zero = fields.Boolean(
        string='With balance less than zero')
    balance_greater_than_zero = fields.Boolean(
        string='With balance greater than zero')
    type = fields.Selection(
        [('receivable', 'Receivable Only'),
         ('payable', 'Payable only')],
        string='Account Type', required=False
    )
    initial_balance = fields.Boolean(
        string='Include Initial Balance', default=True
    )
    reconciled = fields.Selection([('reconciled', 'Reconciled Only'),
                                   ('unreconciled', 'Unreconciled Only')],
                                  string='Reconcile Type')
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals',
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Partners'
    )
    include_details = fields.Boolean(
        string='Include Details', default=True
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    include_partner_ref = fields.Boolean(
        'Include Partner\'s ref', default=True
    )

    @api.model
    def create(self, vals):
        ret = super(InsPartnerLedger, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):

        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range': False})
        if vals.get('date_range'):
            date_from, date_to = self.get_dates_from_date_range(vals.get('date_range'))
            vals.update({'date_from': date_from, 'date_to': date_to})

        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'journal_ids') if type(j) is not list] + vals.get('journal_ids')})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('account_ids'):
            vals.update({'account_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'account_ids') if type(j) is not list] + vals.get('account_ids')})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})

        if vals.get('partner_ids'):
            vals.update({'partner_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'partner_ids') if type(j) is not list] + vals.get('partner_ids')})
        if vals.get('partner_ids') == []:
            vals.update({'partner_ids': [(5,)]})

        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'partner_category_ids') if type(j) is not list] + vals.get('partner_category_ids')})
        if vals.get('partner_category_ids') == []:
            vals.update({'partner_category_ids': [(5,)]})

        ret = super(InsPartnerLedger, self).write(vals)
        return ret

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(
                _('"Date from" must be less than or equal to "Date to"'))
        return True

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}
        if data.get('display_accounts') == 'all':
            filters['display_accounts'] = 'All'
        else:
            filters['display_accounts'] = 'With balance not Zero'
        if data.get('journal_ids', []):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids', [])).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']

        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('partner_category_ids', []):
            filters['categories'] = self.env['res.partner.category'].browse(
                data.get('partner_category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        if data.get('target_moves') == 'all_entries':
            filters['target_moves'] = 'All Entries'
        else:
            filters['target_moves'] = 'Posted Only'

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('initial_balance'):
            filters['initial_balance'] = 'Yes'
        else:
            filters['initial_balance'] = 'No'

        filters['reconciled'] = '-'
        if data.get('reconciled') == 'reconciled':
            filters['reconciled'] = 'Yes'
        if data.get('reconciled') == 'unreconciled':
            filters['reconciled'] = 'No'

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False

        filters['journals_list'] = data.get('journals_list')
        filters['accounts_list'] = data.get('accounts_list')
        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def build_where_clause(self, data=False):
        if not data:
            data = self.get_filters(default_filters={})

        if data:

            WHERE = '(1=1)'

            type = ('receivable', 'payable')
            if self.type:
                type = tuple([self.type, 'none'])

            WHERE += ' AND ty.type IN %s' % str(type)

            if data.get('reconciled') == 'reconciled':
                WHERE += ' AND l.amount_residual = 0'
            if data.get('reconciled') == 'unreconciled':
                WHERE += ' AND l.amount_residual != 0'

            if data.get('journal_ids', []):
                WHERE += ' AND j.id IN %s' % str(
                    tuple(data.get('journal_ids')) + tuple([0]))

            if data.get('account_ids', []):
                WHERE += ' AND a.id IN %s' % str(
                    tuple(data.get('account_ids')) + tuple([0]))

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))

            if data.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % data.get('company_id')

            if data.get('target_moves') == 'posted_only':
                WHERE += " AND m.state = 'posted'"

            return WHERE

    def build_detailed_move_lines(self, offset=0, partner=0, fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner_id
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list of dict)

        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        '''
        cr = self.env.cr
        data = self.get_filters(default_filters={})
        offset_count = offset * fetch_range
        count = 0
        opening_balance = 0
        company_id = self.env.user.company_id
        currency_id = company_id.currency_id

        WHERE = self.build_where_clause()

        WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
        WHERE_INIT += " AND l.partner_id = %s" % partner

        WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
            'date_to')
        WHERE_CURRENT += " AND p.id = %s" % partner

        if data.get('initial_balance'):
            WHERE_FULL = WHERE + " AND l.date <= '%s'" % data.get('date_to')
        else:
            WHERE_FULL = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
        WHERE_FULL += " AND p.id = %s" % partner

        ORDER_BY_CURRENT = 'l.date'

        move_lines = []
        if data.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance,
                        CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN COALESCE(SUM(l.amount_currency), 0)
                           ELSE 0 END AS amount_currency,
                       CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN min(l.currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
            cr.execute(sql)
            row = cr.dictfetchone()
            opening_balance += row.get('balance')

        sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                    GROUP BY l.date, l.move_id
                    ORDER BY %s
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                ''') % (WHERE_CURRENT, ORDER_BY_CURRENT, 0, offset_count)
        cr.execute(sql)
        running_balance_list = cr.fetchall()
        for running_balance in running_balance_list:
            opening_balance += running_balance[0]
        sql = ('''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
        ''') % (WHERE_CURRENT)
        cr.execute(sql)
        count = cr.fetchone()[0]
        if (int(offset_count / fetch_range) == 0) and data.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance,
                        CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN COALESCE(SUM(l.amount_currency), 0)
                           ELSE 0 END AS amount_currency,
                       CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN min(l.currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
            cr.execute(sql)
            for row in cr.dictfetchall():
                row['move_name'] = 'Initial Balance'
                row['partner_id'] = partner
                row['company_currency_id'] = currency_id.id
                move_lines.append(row)
        sql = ('''
                SELECT
                    l.id AS lid,
                    l.account_id AS account_id,
                    l.partner_id AS partner_id,
                    l.date AS ldate,
                    j.code AS lcode,
                    l.currency_id,
                    l.amount_currency,
                    --l.ref AS lref,
                    l.name AS lname,
                    m.id AS move_id,
                    m.name AS move_name,
                    c.symbol AS currency_symbol,
                    c.position AS currency_position,
                    c.rounding AS currency_precision,
                    cc.id AS company_currency_id,
                    cc.symbol AS company_currency_symbol,
                    cc.rounding AS company_currency_precision,
                    cc.position AS company_currency_position,
                    p.name AS partner_name,
                    a.name AS account_name,
                    anl.name AS analytic_account,
                    CASE 
                        WHEN pay.id > 0 
                        THEN pay.reference 
                        ELSE CONCAT(inv.reference, ' ', inv.invoice_description) 
                        END AS description,
                    (SELECT string_agg(DISTINCT tag.name, ',')
                        FROM account_analytic_tag
                        JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                        JOIN account_analytic_tag tag ON tag.id = analtag.account_analytic_tag_id) as analytic_tag,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                --LEFT JOIN account_analytic_tag tag ON tag.id = analtag.account_analytic_tag_id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_payment pay ON (l.payment_id=pay.id)
                LEFT JOIN account_invoice inv ON (l.invoice_id=inv.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, l.partner_id, a.name, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name, anl.name, description
                ORDER BY %s
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            ''') % (WHERE_CURRENT, ORDER_BY_CURRENT, offset_count, fetch_range)
        cr.execute(sql)

        for row in cr.dictfetchall():
            current_balance = row['balance']
            row['balance'] = opening_balance + current_balance
            opening_balance += current_balance
            row['initial_bal'] = False
            move_lines.append(row)

        if ((count - offset_count) <= fetch_range) and data.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance,
                        CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN COALESCE(SUM(l.amount_currency), 0)
                           ELSE 0 END AS amount_currency,
                       CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN min(l.currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                row['move_name'] = 'Ending Balance'
                row['partner_id'] = partner
                row['company_currency_id'] = currency_id.id
                move_lines.append(row)
        return count, offset_count, move_lines

    def process_data(self):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        cr = self.env.cr

        data = self.get_filters(default_filters={})

        WHERE = self.build_where_clause(data)
        company_id = self.env.user.company_id
        if self.type == 'receivable':
            partner_type_domain = [('customer', '=', True)]
        elif self.type == 'payable':
            partner_type_domain = [('supplier', '=', True)]
        else:
            partner_type_domain = ['|', ('customer', '=', True), ('supplier', '=', True)]
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)] + partner_type_domain
        if self.partner_category_ids:
            partner_company_domain.append(
                ('category_id', 'in', self.partner_category_ids.ids))

        if data.get('partner_ids', []):
            partner_ids = self.env['res.partner'].browse(
                data.get('partner_ids'))
        else:
            partner_ids = self.env['res.partner'].search(
                partner_company_domain)

        currency = self.env.user.company_id.currency_id
        line_common_keys = {
            'company_currency_id': currency.id, 'company_currency_symbol': currency.symbol,
            'company_currency_precision': currency.rounding, 'company_currency_position': currency.position,
            'currency_id': 0, 'currency_symbol': '',
            'currency_precision': currency.rounding, 'currency_position': currency.position,
            'debit': 0.0, 'credit': 0.0, 'balance': 0.0, 'amount_currency': 0.0,
            'pages': [], 'single_page': True, 'lines': [], 'count': 0
        }
        move_lines = {}
        total_debit, total_credit, total_balance = 0.0, 0.0, 0.0
        for partner in partner_ids:
            line_key = f'{partner.name} - {str(partner.id)}'
            move_lines[line_key] = line_common_keys.copy()
            move_lines[line_key]['lines'] = []
            move_lines[line_key].update({
                'name': f'{partner.name} ({partner.ref})' if self.include_partner_ref and partner.ref else partner.name,
                'code': partner.id,
                'id': partner.id,
            })
            company_id = self.env.user.company_id
            currency = partner.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0.0

            WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
            WHERE_INIT += " AND l.partner_id = %s" % partner.id
            ORDER_BY_CURRENT = 'l.date'

            if data.get('initial_balance'):
                sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance,
                        CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN COALESCE(SUM(l.amount_currency), 0)
                           ELSE 0 END AS amount_currency,
                       CASE
                           WHEN count(distinct l.currency_id) = 1
                               THEN min(l.currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
                cr.execute(sql)
                for row in cr.dictfetchall():
                    row['move_name'] = 'Initial Balance'
                    row['partner_id'] = partner.id
                    row['initial_bal'] = True
                    row['ending_bal'] = False
                    opening_balance += row['balance']
                    move_lines[line_key]['lines'].append(row)
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND p.id = %s" % partner.id
            sql = ('''
                SELECT
                    l.id AS lid,
                    l.date AS ldate,
                    j.code AS lcode,
                    a.name AS account_name,
                    m.name AS move_name,
                    l.name AS lname,
                    anl.name AS analytic_account,
                    CASE 
                        WHEN pay.id > 0 
                        THEN pay.reference 
                        ELSE CONCAT(inv.reference, ' ', inv.invoice_description) 
                        END AS description,
                    (SELECT string_agg(DISTINCT tag.name, ',')
                        FROM account_analytic_tag
                        JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                        JOIN account_analytic_tag tag ON tag.id = analtag.account_analytic_tag_id) as analytic_tag,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.balance,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency,
                    l.currency_id as currency_id
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_payment pay ON (l.payment_id=pay.id)
                LEFT JOIN account_invoice inv ON (l.invoice_id=inv.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                --GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name, anl.name
                ORDER BY %s
            ''') % (WHERE_CURRENT, ORDER_BY_CURRENT)
            cr.execute(sql)
            current_lines = cr.dictfetchall()
            for row in current_lines:
                row['initial_bal'] = False
                row['ending_bal'] = False

                current_balance = row['balance']
                row['balance'] = opening_balance + current_balance
                opening_balance += current_balance
                row['initial_bal'] = False

                move_lines[line_key]['lines'].append(row)
            if data.get('initial_balance'):
                WHERE_FULL = WHERE + \
                    " AND l.date <= '%s'" % data.get('date_to')
            else:
                WHERE_FULL = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
            WHERE_FULL += " AND p.id = %s" % partner.id
            sql = ('''
                SELECT 
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit - l.credit),0) AS balance,
                    CASE
                       WHEN count(distinct l.currency_id) = 1
                           THEN COALESCE(SUM(l.amount_currency), 0)
                       ELSE 0 END AS amount_currency,
                    CASE
                       WHEN count(distinct l.currency_id) = 1
                           THEN min(l.currency_id)
                       END AS currency_id
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
            ''') % WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                if (data.get('display_accounts') == 'balance_not_zero' and currency.is_zero(
                        row['debit'] - row['credit'])) \
                        or (data.get('balance_less_than_zero') and (row['debit'] - row['credit']) > 0) \
                        or (data.get('balance_greater_than_zero') and (row['debit'] - row['credit']) < 0):
                    move_lines.pop(line_key, None)
                else:
                    row['ending_bal'] = True
                    row['initial_bal'] = False
                    move_lines[line_key]['lines'].append(row)
                    move_lines[line_key]['debit'] = row['debit']
                    move_lines[line_key]['credit'] = row['credit']
                    move_lines[line_key]['balance'] = row['balance']
                    total_debit += row['debit']
                    total_credit += row['credit']
                    total_balance += row['balance']
                    move_lines[line_key]['company_currency_id'] = currency.id
                    move_lines[line_key]['company_currency_symbol'] = symbol
                    move_lines[line_key]['company_currency_precision'] = rounding
                    move_lines[line_key]['company_currency_position'] = position
                    move_lines[line_key]['count'] = len(current_lines)
                    move_lines[line_key]['pages'] = self.get_page_list(
                        len(current_lines))
                    move_lines[line_key]['single_page'] = True if len(
                        current_lines) <= FETCH_RANGE else False
        

        move_lines['Total - 0'] = line_common_keys.copy()
        move_lines['Total - 0']['lines'] = []
        move_lines['Total - 0'].update({
            'name': '----------- TOTAL -----------', 'code': 0, 'id': 0,
            'debit': total_debit, 'credit': total_credit, 'balance': total_balance, 'amount_currency': 0
        })

        currency_data = {c['currency_id']: c
                         for c in self.create_query_and_fetch('res_currency',
                                                              'id as currency_id,symbol as currency_symbol,rounding as currency_precision,position as currency_position',
                                                              '', fetchall=True, first_column=False, obj_format=True)
                         }

        # 12.9.3 fix amount currency
        for key, vals in move_lines.items():
            currencies = {line['currency_id'] for line in vals['lines'] if line['currency_id']}
            currency_count = len(currencies)
            if currency_count == 1:
                currency_id = list(currencies)[0]
                for line in vals['lines']:
                    if line.get('ending_bal'):
                        continue
                    if line['currency_id'] == currency_id:
                        vals['amount_currency'] += line['amount_currency']
                vals.update(currency_data[currency_id])
            else:
                vals.update({'amount_currency': 0.0, 'currency_id': False})

        return move_lines

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

        journals = self.journal_ids if self.journal_ids else self.env['account.journal'].search(
            company_domain)
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(
            company_domain)
        partners = self.partner_ids if self.partner_ids else self.env['res.partner'].search(
            partner_company_domain)
        categories = self.partner_category_ids if self.partner_category_ids else self.env['res.partner.category'].search([
        ])

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'partner_category_ids': self.partner_category_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'target_moves': self.target_moves,
            'initial_balance': self.initial_balance,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'reconciled': self.reconciled,
            'display_accounts': self.display_accounts,
            'include_details': self.include_details,
            'balance_less_than_zero': self.balance_less_than_zero,
            'balance_greater_than_zero': self.balance_greater_than_zero,

            'journals_list': self.create_query_and_fetch('account_journal', 'id,name', f'id in {journals._ids + (0,0)}', fetchall=True, first_column=False),
            'accounts_list': self.create_query_and_fetch('account_account', 'id,name', f'id in {accounts._ids + (0,0)}', fetchall=True, first_column=False),
            'partners_list': self.create_query_and_fetch('res_partner', 'id,name', f'id in {partners._ids + (0,0)}', fetchall=True, first_column=False),
            'category_list': self.create_query_and_fetch('res_partner_category', 'id,name', f'id in {categories._ids + (0,0)}', fetchall=True, first_column=False),
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
            account_lines = self.process_data()
            return filters, account_lines

    def action_pdf(self):
        filters, account_lines = self.get_report_datas()
        return self.env.ref(
            'account_dynamic_reports.action_print_partner_ledger').report_action(
            self, data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PL View',
            'tag': 'dynamic.pl',
            'context': {'wizard_id': self.id}
        }
        return res
