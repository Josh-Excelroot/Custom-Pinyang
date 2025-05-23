from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from dateutil.relativedelta import relativedelta
FETCH_RANGE = 2000


def format_date(date_str):
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError as e:
        return datetime.strptime(date_str, '%d/%m/%Y')


class InsGeneralLedger(models.TransientModel):
    _name = "ins.general.ledger"
    _inherit = ['dynamic.reports.mixin']
    _description = "General Ledger"

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'General Ledger'))
        return res

    target_moves = fields.Selection(
        [('all_entries', 'All entries'),
         ('posted_only', 'Posted Only')], string='Target Moves',
        default='posted_only', required=True
    )
    sort_accounts_by = fields.Selection(
        [('date', 'Date'), ('journal', 'Journal and Partner')], string='Sort By',
        default='date', required=True
    )
    display_accounts = fields.Selection(
        [('all', 'All'),
         ('balance_not_zero', 'With balance not equal to zero')], string='Display accounts',
        default='balance_not_zero', required=True
    )
    initial_balance = fields.Boolean(
        string='Include Initial Balance', default=True
    )
    account_type_ids = fields.Many2many(
        'account.account.type', string='Account Types'
    )
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    account_tag_ids = fields.Many2many(
        'account.account.tag', string='Account Tags'
    )
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags'
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
    include_period_13 = fields.Boolean(
        'Include Period 13 Entries?', default=True
    )
    include_exch_rate_entries = fields.Boolean()
    include_partner_ref = fields.Boolean()

    @api.onchange('account_type_ids')
    def _onchange_account_type_ids(self):
        if self.account_type_ids:
            self.account_ids = self.env['account.account'].search([
                ('company_id', '=', self.company_id.id),
                ('user_type_id', 'in', self.account_type_ids.ids)])
        else:
            self.account_ids = None

    @api.onchange('partner_ids')
    def onchange_partner_ids(self):
        """Handle partners change."""
        if self.partner_ids:
            self.account_type_ids = self.env['account.account.type'].search([
                ('type', 'in', ['receivable', 'payable'])])
        else:
            self.account_type_ids = None
        self._onchange_account_type_ids()

    @api.model
    def default_get(self, fields):
        res = super(InsGeneralLedger, self).default_get(fields)
        company = self.company_id.browse(res.get('company_id'))
        if 'include_exch_rate_entries' in fields:
            res['include_exch_rate_entries'] = company.general_ledger_exch_entries
        if 'target_moves' in fields and company.unposted_entries_dynamic_reports:
            res['target_moves'] = 'all_entries'
        return res

    @api.model
    def create(self, vals):
        # print('>>>>>ins.general.ledger create=', vals)
        date_from = vals.get('date_from')
        if date_from and type(date_from) == str:
            vals['date_from'] = format_date(date_from)
        date_to = vals.get('date_to')
        if date_to and type(date_to) == str:
            vals['date_to'] = format_date(date_to)
        ret = super(InsGeneralLedger, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):
        # print('>>>>>ins.general.ledger write=', vals)
        date_from = vals.get('date_from')
        if date_from and type(date_from) == str:
            vals['date_from'] = format_date(date_from)
        date_to = vals.get('date_to')
        if date_to and type(date_to) == str:
            vals['date_to'] = format_date(date_to)
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

        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(5, 0, 0)] + [(4, j) for j in vals.get(
                'account_tag_ids') if type(j) is not list] + vals.get('account_tag_ids')})
        if vals.get('account_tag_ids') == []:
            vals.update({'account_tag_ids': [(5,)]})

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
        return super(InsGeneralLedger, self).write(vals)

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(
                _('"Date from" must be less than or equal to "Date to"'))
        return True

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}
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
        if data.get('account_tag_ids', []):
            filters['account_tags'] = self.env['account.account.tag'].browse(
                data.get('account_tag_ids', [])).mapped('name')
        else:
            filters['account_tags'] = ['All']
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
                data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('display_accounts') == 'all':
            filters['display_accounts'] = 'All'
        else:
            filters['display_accounts'] = 'With balance not Zero'

        if data.get('target_moves') == 'all_entries':
            filters['target_moves'] = 'All Entries'
        else:
            filters['target_moves'] = 'Posted Only'

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('sort_accounts_by', False) == 'date':
            filters['sort_accounts_by'] = 'Date'
        else:
            filters['sort_accounts_by'] = 'Journal and partner'
        if data.get('initial_balance'):
            filters['initial_balance'] = 'Yes'
        else:
            filters['initial_balance'] = 'No'
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
        filters['account_tag_list'] = data.get('account_tag_list')
        filters['analytics_list'] = data.get('analytics_list')
        filters['analytic_tag_list'] = data.get('analytic_tag_list')
        filters['partners_list'] = data.get('partners_list')
        filters['company_name'] = data.get('company_name')
        filters['include_period_13'] = data.get('include_period_13')

        return filters

    def build_where_clause(self, data=False):
        if not data:
            data = self.get_filters(default_filters={})

        if data:

            WHERE = '(1=1)'

            if data.get('journal_ids', []):
                WHERE += ' AND j.id IN %s' % str(
                    tuple(data.get('journal_ids')) + tuple([0]))

            if data.get('analytic_ids', []):
                WHERE += ' AND anl.id IN %s' % str(
                    tuple(data.get('analytic_ids')) + tuple([0]))

            if data.get('analytic_tag_ids', []):
                WHERE += self.analytic_tags_where_clause(data.get('analytic_tag_ids'), 'l')

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))

            if data.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % data.get('company_id')

            if data.get('target_moves') == 'posted_only':
                WHERE += " AND m.state = 'posted'"

            if 'include_period_13' in data and not data.get('include_period_13'):
                WHERE += " AND (m.period_13 = False OR m.period_13 IS NULL)"

            return WHERE

    def get_exclude_exch_journal_id(self):
        if not self.include_exch_rate_entries:
            return self.company_id.currency_exchange_journal_id.id
        return False

    def build_detailed_move_lines(self, offset=0, account=0, fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param account: Integer - Account_id
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
        # WHERE += ' and (p.active = True or p.id is null) 
        exclude_exch_journal_id = self.get_exclude_exch_journal_id()
        if exclude_exch_journal_id:
            WHERE += f"AND j.id != {exclude_exch_journal_id}"

        WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
        WHERE_INIT += " AND l.account_id = %s" % account

        WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
            'date_to')
        WHERE_CURRENT += " AND a.id = %s" % account

        if data.get('initial_balance'):
            WHERE_FULL = WHERE + " AND l.date <= '%s'" % data.get('date_to')
        else:
            WHERE_FULL = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
        WHERE_FULL += " AND a.id = %s" % account

        if data.get('sort_accounts_by') == 'date':
            ORDER_BY_CURRENT = 'l.date, l.move_id'
        else:
            ORDER_BY_CURRENT = 'j.code, p.name, l.move_id'

        move_lines = []
        if data.get('initial_balance'):
            sql = (f'''
                    SELECT
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON (analtag.account_move_line_id=l.id)
                    {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
            account_rec = self.env['account.account'].browse(account)
            if account_rec.user_type_id.include_initial_balance:
                cr.execute(sql)
                row = cr.dictfetchone()
            else:
                row = {'balance': 0}
            opening_balance += row.get('balance')

        sql = (f'''
            SELECT
                COALESCE(SUM(l.debit - l.credit),0) AS balance,
                CASE
                   WHEN count(distinct l.currency_id) = 1
                       THEN COALESCE(SUM(l.amount_currency), 0)
                   ELSE 0 END AS amount_currency,
                CASE
                   WHEN count(distinct l.currency_id) = 1
                       THEN min(l.currency_id)
                   ELSE min(l.company_currency_id)
                   END AS currency_id
            FROM account_move_line l
            JOIN account_move m ON (l.move_id=m.id)
            JOIN account_account a ON (l.account_id=a.id)
            LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
            -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
            {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
            GROUP BY j.code, p.name, l.date, l.move_id
            ORDER BY %s
            OFFSET %s ROWS
            FETCH FIRST %s ROWS ONLY
        ''') % (WHERE_CURRENT, ORDER_BY_CURRENT, 0, offset_count)
        cr.execute(sql)
        running_balance_list = cr.fetchall()
        for running_balance in running_balance_list:
            opening_balance += running_balance[0]

        sql = (f'''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
        ''') % (WHERE_CURRENT)
        cr.execute(sql)
        count = cr.fetchone()[0]
        if (int(offset_count / fetch_range) == 0) and data.get('initial_balance'):
            sql = (f'''
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
                           ELSE min(l.company_currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
            cr.execute(sql)
            if account_rec.user_type_id.include_initial_balance:
                cr.execute(sql)
                init_bal_res = cr.dictfetchall()
            else:
                init_bal_res = [{'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                                 'amount_currency': 0, 'currency_id': currency_id.id}]
            for row in init_bal_res:
                row['move_name'] = 'Initial Balance'
                row['account_id'] = account
                row['company_currency_id'] = currency_id.id
                move_lines.append(row)
        sql = (f'''
                SELECT
                    l.id AS lid,
                    l.account_id AS account_id,
                    l.date AS ldate,
                    j.code AS lcode,
                    l.currency_id,
                    --l.ref AS lref,
                    l.name AS lname,  -- Entry Label in UI, Refernce in PDF
                    m.id AS move_id,
                    m.name AS move_name,
                    c.symbol AS currency_symbol,
                    c.position AS currency_position,
                    c.rounding AS currency_precision,
                    cc.id AS company_currency_id,
                    cc.symbol AS company_currency_symbol,
                    cc.rounding AS company_currency_precision,
                    cc.position AS company_currency_position,
                    {(self.include_partner_ref and "'(' || COALESCE(p.ref, '') || ') ' || ") or ''} p.name AS partner_name,
                    anl.name AS analytic_account,
                    CASE
                        WHEN pay.id > 0
                        THEN pay.reference
                        WHEN inv.id > 0
                        THEN CONCAT(inv.reference, ' ', inv.invoice_description)
                        ELSE m.ref -- For Manual JE - description will be JE Reference
                        END AS description,
                    (SELECT string_agg(DISTINCT tag.name, ',')
                        FROM account_analytic_tag
                        JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                        JOIN account_analytic_tag tag ON tag.id = analtag.account_analytic_tag_id) as analytic_tag,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency,
                    c.name as currency_name,
                    c.id as currency_id
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_payment pay ON (l.payment_id=pay.id)
                LEFT JOIN account_invoice inv ON (l.invoice_id=inv.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name, p.ref, anl.name, description, c.name, c.id
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
            if not account_rec.user_type_id.include_initial_balance:
                WHERE_FULL += f' and l.date >= \'{data.get("date_from")}\''
            sql = (f'''
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
                           ELSE min(l.company_currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                row['move_name'] = 'Ending Balance'
                row['account_id'] = account
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
        # WHERE += ' and (p.active = True or p.id is null) '
        if not self.include_exch_rate_entries:
            exclude_exch_journal_id = self.get_exclude_exch_journal_id()
            if exclude_exch_journal_id:
                WHERE += f"AND j.id != {exclude_exch_journal_id}"

        company_id = self.env.user.company_id
        account_company_domain = [('company_id', '=', company_id.id)]

        if data.get('account_tag_ids', []):
            account_company_domain.append(
                ('tag_ids', 'in', data.get('account_tag_ids', [])))

        if data.get('account_ids', []):
            account_company_domain.append(
                ('id', 'in', data.get('account_ids', [])))

        account_ids = self.env['account.account'].search(
            account_company_domain)

        move_lines = {
            x.code: {
                'name': x.name,
                'code': x.code,
                'company_currency_id': 0,
                'company_currency_symbol': 'AED',
                'company_currency_precision': 0.0100,
                'company_currency_position': 'after',
                'amount_currency': 0,
                'id': x.id,
                'lines': [],
            } for x in account_ids.sorted('code')
        }  # base for accounts to display
        for account in account_ids:
            company_id = self.env.user.company_id
            currency = account.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0

            WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
            WHERE_INIT += " AND l.account_id = %s" % account.id
            if data.get('sort_accounts_by') == 'date':
                ORDER_BY_CURRENT = 'l.date, l.move_id'
            else:
                ORDER_BY_CURRENT = 'j.code, p.name, l.move_id'
            if data.get('initial_balance'):
                sql = (f'''
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
                           ELSE min(l.company_currency_id)
                           END AS currency_id
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % WHERE_INIT
                if account.user_type_id.include_initial_balance:
                    cr.execute(sql)
                    init_bal_res = cr.dictfetchall()
                else:
                    init_bal_res = [{'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                                     'amount_currency': 0, 'currency_id': currency.id}]
                for row in init_bal_res:
                    row['move_name'] = 'Initial Balance'
                    row['account_id'] = account.id
                    row['initial_bal'] = True
                    row['ending_bal'] = False
                    opening_balance += row['balance']
                    move_lines[account.code]['lines'].append(row)
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND a.id = %s" % account.id
            ORDER_BY_CURRENT += ', l.id'
            sql = (f'''
                SELECT
                    DISTINCT l.id AS lid,
                    l.date AS ldate,
                    j.code AS lcode,
                    p.name AS partner_name,
                    m.name AS move_name,
                    l.name AS lname,
                    anl.name AS analytic_account,
                    CASE
                        WHEN pay.id > 0
                        THEN pay.reference
                        WHEN inv.id > 0
                        THEN CONCAT(inv.reference, ' ', inv.invoice_description)
                        ELSE m.ref -- For Manual JE - description will be JE Reference
                        END AS description,
                    (SELECT string_agg(DISTINCT tag.name, ',')
                        FROM account_analytic_tag
                        JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                        JOIN account_analytic_tag tag ON tag.id = analtag.account_analytic_tag_id) as analytic_tag,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency,
                    c.name as currency_name,
                    c.symbol as currency_sign,
                    c.id as currency_id,
                    l.move_id as move_id
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_payment pay ON (l.payment_id=pay.id)
                LEFT JOIN account_invoice inv ON (l.invoice_id=inv.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                --GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.debit_currency, l.credit_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name, anl.name
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

                move_lines[account.code]['lines'].append(row)
            if account.user_type_id.include_initial_balance and data.get('initial_balance'):
                WHERE_FULL = WHERE + \
                    " AND l.date <= '%s'" % data.get('date_to')
            else:
                WHERE_FULL = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
            WHERE_FULL += " AND a.id = %s" % account.id
            sql = (f'''
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
                       ELSE min(l.company_currency_id)
                       END AS currency_id
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                -- LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                {self.analytic_tags_left_join(data.get('analytic_tag_ids'), 'l')}
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
            ''') % WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                if data.get('display_accounts') == 'balance_not_zero' and currency.is_zero(row['debit'] - row['credit']):
                    move_lines.pop(account.code, None)
                else:
                    row['ending_bal'] = True
                    row['initial_bal'] = False
                    move_lines[account.code]['lines'].append(row)
                    move_lines[account.code]['debit'] = row['debit']
                    move_lines[account.code]['credit'] = row['credit']
                    move_lines[account.code]['balance'] = row['balance']
                    move_lines[account.code]['company_currency_id'] = currency.id
                    move_lines[account.code]['company_currency_symbol'] = symbol
                    move_lines[account.code]['company_currency_precision'] = rounding
                    move_lines[account.code]['company_currency_position'] = position
                    move_lines[account.code]['count'] = len(current_lines)
                    move_lines[account.code]['pages'] = self.get_page_list(
                        len(current_lines))
                    move_lines[account.code]['single_page'] = True if len(
                        current_lines) <= FETCH_RANGE else False

        total_initial, total_debit, total_credit, total_balance = 0, 0, 0, 0
        for account_code in move_lines:
            move_lines[account_code]['initial_balance'] = 0.0
            move_lines[account_code]['currency_id'] = None
            total_debit += move_lines[account_code]['debit']
            total_credit += move_lines[account_code]['credit']
            total_balance += move_lines[account_code]['balance']
            if not data.get('initial_balance', False):
                continue
            sub_lines = move_lines[account_code].get('lines')
            if sub_lines:
                if len(sub_lines) > 3 and sub_lines[1].get('currency_id') and sub_lines[1].get('currency_id') != move_lines[account_code]['company_currency_id']:
                    move_lines[account_code]['currency_name'] = sub_lines[1].get('currency_name')
                    move_lines[account_code]['currency_id'] = sub_lines[1].get('currency_id')
                    move_lines[account_code]['amount_currency'] = sum([l['amount_currency'] for l in sub_lines[1:-1]])
                move_lines[account_code]['initial_balance'] = sub_lines[0].get('balance', 0.0)
                total_initial += move_lines[account_code]['initial_balance']

        currency = self.env.user.company_id.currency_id
        move_lines['Total'] = {
            'name': 'TOTAL', 'code': '', 'id': 0, 'lines': [], 'count': 0, 'pages': [1], 'single_page': True,
            'company_currency_id': currency.id, 'company_currency_symbol': currency.symbol,
            'company_currency_precision': currency.rounding, 'company_currency_position': currency.position,
            'initial_balance': total_initial, 'debit': total_debit, 'credit': total_credit, 'balance': total_balance,
            'amount_currency': 0.0
        }

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

    def analytic_tags_left_join(self, analytic_tags, aml_alias):
        return ''
        if not analytic_tags:
            return ''
        analytic_tags = tuple(analytic_tags) + (0,0)
        return f"""LEFT JOIN (
             SELECT account_move_line_id
             FROM account_analytic_tag_account_move_line_rel
             WHERE account_analytic_tag_id in {analytic_tags}
             GROUP BY account_move_line_id
         ) analtag ON analtag.account_move_line_id = {aml_alias}.id"""

    def analytic_tags_where_clause(self, analytic_tag_ids, aml_alias):
        if not analytic_tag_ids:
            return ''
        analytic_tag_ids = tuple(analytic_tag_ids) + (0,0)
        return f""" AND {aml_alias}.id IN (
             SELECT account_move_line_id
             FROM account_analytic_tag_account_move_line_rel
             WHERE account_analytic_tag_id in {analytic_tag_ids}
             GROUP BY account_move_line_id
         ) """

    def get_filters(self, default_filters={}):
        # TS - fix the bug that the user must select the empty date_range if want to use the start_date and end_date
        # self.onchange_date_range()
        # print('>>>>>>>>Before GL get_filters self.date_from=', self.date_from, ' , date_to=', self.date_to,
        #      ' , dater range=', self.date_range)
        # Added so that Trial Balance's date range will be used when opening the GL
        if not self.date_from and not self.date_to:
            self.date_from = self.env.user.company_id.tb_date_from
            self.date_to = self.env.user.company_id.tb_date_to
        # if not self.date_from and not self.date_to:
        #     self.onchange_date_range()
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
        account_tags = self.account_tag_ids if self.account_tag_ids else self.env['account.account.tag'].search([
        ])
        analytics = self.analytic_ids if self.analytic_ids else self.env['account.analytic.account'].search(
            company_domain)
        analytic_tags = self.analytic_tag_ids if self.analytic_tag_ids else self.env['account.analytic.tag'].sudo().search(
            ['|', ('company_id', '=', company_id.id), ('company_id', '=', False)])
        partners = self.partner_ids if self.partner_ids else self.env['res.partner'].search(
            partner_company_domain)

        # 12.1.9.1 Kenny - Fix analytic tags showing analytic account in general ledger
        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'account_tag_ids': self.account_tag_ids.ids,
            'analytic_ids': self.analytic_ids.ids,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'target_moves': self.target_moves,
            'sort_accounts_by': self.sort_accounts_by,
            'initial_balance': self.initial_balance,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'display_accounts': self.display_accounts,
            'include_details': self.include_details,

            'journals_list': self.create_query_and_fetch('account_journal', 'id,name', f'id in {journals._ids + (0,0)}', fetchall=True, first_column=False),
            'accounts_list': self.create_query_and_fetch('account_account', 'id,name', f'id in {accounts._ids + (0,0)}', fetchall=True, first_column=False),
            'account_tag_list': self.create_query_and_fetch('account_account_tag', 'id,name', f'id in {account_tags._ids + (0,0)}', fetchall=True, first_column=False),
            'partners_list': self.create_query_and_fetch('res_partner', 'id,name', f'id in {partners._ids + (0,0)}', fetchall=True, first_column=False),
            'analytics_list': self.create_query_and_fetch('account_analytic_account', 'id,name', f'id in {analytics._ids + (0,0)}', fetchall=True, first_column=False),
            'analytic_tag_list': self.create_query_and_fetch('account_analytic_tag', 'id,name', f'id in {analytic_tags._ids + (0,0)}', fetchall=True, first_column=False),
            'company_name': self.company_id and self.company_id.name,
            'include_period_13': self.include_period_13,
        }
        # 'analytic_tag_list': self.create_query_and_fetch('account_account_tag', 'id,name', f'id in {analytic_tags._ids + (0,0)}', fetchall=True, first_column=False),
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
            'account_dynamic_reports'
            '.action_print_general_ledger').report_action(  # Rajeel | Remove Landscape | 30/03/23
            self, data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamfic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'GL View',
            'tag': 'dynamic.gl',
            'context': {'wizard_id': self.id}
        }
        return res
