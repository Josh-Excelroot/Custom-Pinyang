from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

# from datetime import datetime, timedelta, date
# import calendar
import datetime
from dateutil.relativedelta import relativedelta

# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

FETCH_RANGE = 2500


class InsPartnerAgeing(models.TransientModel):
    _name = "ins.partner.ageing"
    _inherit = ['dynamic.reports.mixin']
    _description = "Partner Ageing"

    @api.onchange("partner_type")
    def onchange_partner_type(self):
        if 'update_partners' in self._context:
            self.partner_ids = [(5,)]
            if self.partner_type:
                company_id = self.env.user.company_id
                if self.partner_type == "customer":
                    partner_company_domain = [
                        ("parent_id", "=", False),
                        ("customer", "=", True),
                        "|",
                        ("company_id", "=", company_id.id),
                        ("company_id", "=", False),
                    ]

                    self.partner_ids |= self.env["res.partner"].search(
                        partner_company_domain
                    )
                if self.partner_type == "supplier":
                    partner_company_domain = [
                        ("parent_id", "=", False),
                        ("supplier", "=", True),
                        "|",
                        ("company_id", "=", company_id.id),
                        ("company_id", "=", False),
                    ]

                    self.partner_ids |= self.env["res.partner"].search(
                        partner_company_domain
                    )

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "Ageing"))
        return res

    @api.model
    def _get_default_bucket_1(self):
        return self.env.user.company_id.bucket_1

    @api.model
    def _get_default_bucket_2(self):
        return self.env.user.company_id.bucket_2

    @api.model
    def _get_default_bucket_3(self):
        return self.env.user.company_id.bucket_3

    @api.model
    def _get_default_bucket_4(self):
        return self.env.user.company_id.bucket_4

    @api.model
    def _get_default_bucket_5(self):
        return self.env.user.company_id.bucket_5

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_currency_domain(self):
        return [("id", "!=", self.env.user.company_id.currency_id.id)]

    # as_on_date = fields.Date(string='As on date', required=True, default=fields.Date.today())
    as_on_date = fields.Date(
        string="As on date", required=True, default=fields.Date.context_today
    )
    bucket_1 = fields.Integer(
        string="Bucket 1", required=True, default=_get_default_bucket_1
    )
    bucket_2 = fields.Integer(
        string="Bucket 2", required=True, default=_get_default_bucket_2
    )
    bucket_3 = fields.Integer(
        string="Bucket 3", required=True, default=_get_default_bucket_3
    )
    bucket_4 = fields.Integer(
        string="Bucket 4", required=True, default=_get_default_bucket_4
    )
    bucket_5 = fields.Integer(
        string="Bucket 5", required=True, default=_get_default_bucket_5
    )
    include_details = fields.Boolean(string="Include Details", default=True)
    type = fields.Selection(
        [
            ("receivable", "Receivable Accounts Only"),
            ("payable", "Payable Accounts Only"),
            ("", 'Both')
        ],
        string="Type", default='receivable'
    )
    partner_type = fields.Selection(
        [("customer", "Customer Only"), ("supplier", "Supplier Only")],
        string="Partner Type",
    )

    partner_ids = fields.Many2many("res.partner", required=False)
    partner_category_ids = fields.Many2many(
        "res.partner.category", string="Partner Tag",
    )
    display_accounts = fields.Selection(
        [("all", "All"), ("balance_not_zero", "With balance not equal to zero")],
        string="Display accounts",
        default="balance_not_zero",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=_get_default_company
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", domain=_get_currency_domain
    )
    ageing_by = fields.Selection(
        [("inv_date", "Invoice Date"), ("due_date", "Due Date")],
        string="Ageing By",
        default="inv_date",
        required="1",
    )

    salesperson = fields.Many2one("res.users", string="Salesperson")

    include_partner_ref = fields.Boolean('Include Partner\'s ref', default=True)
    include_exch_rate_entries = fields.Boolean()
    include_unposted_entries = fields.Boolean()

    date_from = fields.Date(string='Start date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End date', required=True, default=fields.Date.context_today)

    @api.model
    def default_get(self, fields):
        res = super(InsPartnerAgeing, self).default_get(fields)
        company = self.company_id.browse(res.get('company_id'))
        if 'include_exch_rate_entries' in fields:
            res['include_exch_rate_entries'] = company.partner_ageing_exch_entries
        if 'include_unposted_entries' in fields:
            res['include_unposted_entries'] = company.unposted_entries_dynamic_reports
        return res

    @api.multi
    def write(self, vals):
        if not vals.get("partner_ids"):
            vals.update({"partner_ids": [(5, 0, 0)]})

        if vals.get("partner_category_ids"):
            vals.update(
                {
                    "partner_category_ids": [(5, 0, 0)]
                    + [
                        (4, j)
                        for j in vals.get("partner_category_ids")
                        if type(j) is not list
                    ]
                    + vals.get("partner_category_ids")
                }
            )
        if vals.get("partner_category_ids") == []:
            vals.update({"partner_category_ids": [(5,)]})

        ret = super(InsPartnerAgeing, self).write(vals)
        return ret

    def validate_data(self):
        if not (
            self.bucket_1 < self.bucket_2
            and self.bucket_2 < self.bucket_3
            and self.bucket_3 < self.bucket_4
            and self.bucket_4 < self.bucket_5
        ):
            raise ValidationError(_('"Bucket order must be ascending"'))
        return True

    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        partner_company_domain = [
            ("parent_id", "=", False),
            "|",
            ("customer", "=", True),
            ("supplier", "=", True),
            "|",
            ("company_id", "=", company_id.id),
            ("company_id", "=", False),
        ]

        partners = (
            self.partner_ids
            if self.partner_ids
            else self.env["res.partner"].search(partner_company_domain)
        )
        partners_list = []
        partners_info = self.query_fetch(f"SELECT id,name,ref FROM res_partner WHERE id in {partners._ids + (0, 0)} and active=True",
                         obj_format=True, fetchall=True)
        for partner in partners_info:
            partner_name = partner.name
            if self.include_partner_ref and partner.ref:
                partner_name += f' ({partner.ref})'
            partners_list.append((partner.id, partner_name))

        categories = (
            self.partner_category_ids
            if self.partner_category_ids
            else self.env["res.partner.category"].search([])
        )

        filter_dict = {
            "partner_ids": self.partner_ids.ids,
            "partner_category_ids": self.partner_category_ids.ids,
            "company_id": self.company_id and self.company_id.id or False,
            "as_on_date": self.as_on_date,
            "ageing_by": self.ageing_by,
            "type": self.type,
            "partner_type": self.partner_type,
            "bucket_1": self.bucket_1,
            "bucket_2": self.bucket_2,
            "bucket_3": self.bucket_3,
            "bucket_4": self.bucket_4,
            "bucket_5": self.bucket_5,
            "include_details": self.include_details,
            "salesperson": self.salesperson.id,
            "currency_id": self.currency_id and self.currency_id.id,
            "display_accounts": self.display_accounts,
            "partners_list": partners_list,
            "category_list": [(c.id, c.name) for c in categories],
            "company_name": self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def process_filters(self):
        """ To show on report headers"""

        data = self.get_filters(default_filters={})

        filters = {}

        filters["bucket_1"] = data.get("bucket_1")
        filters["bucket_2"] = data.get("bucket_2")
        filters["bucket_3"] = data.get("bucket_3")
        filters["bucket_4"] = data.get("bucket_4")
        filters["bucket_5"] = data.get("bucket_5")
        filters["ageing_by"] = data.get("aging_by")

        if data.get("display_accounts") == "all":
            filters["display_accounts"] = "All"
        else:
            filters["display_accounts"] = "With balance not Zero"

        if data.get("partner_ids", []):
            filters["partners"] = (
                self.env["res.partner"]
                .browse(data.get("partner_ids", []))
                .mapped("name")
            )
        else:
            filters["partners"] = ["All"]

        if data.get("as_on_date", False):
            filters["as_on_date"] = data.get("as_on_date")

        if data.get("company_id"):
            filters["company_id"] = data.get("company_id")
        else:
            filters["company_id"] = ""

        if data.get("type"):
            filters["type"] = data.get("type")

        if data.get("salesperson"):
            sales_person = self.env["res.users"].search(
                [("id", "=", data.get("salesperson"))]
            )
            if sales_person:
                filters["salesperson"] = sales_person.name

        if data.get("partner_type"):
            filters["partner_type"] = data.get("partner_type")

        if data.get("partner_category_ids", []):
            filters["categories"] = (
                self.env["res.partner.category"]
                .browse(data.get("partner_category_ids", []))
                .mapped("name")
            )
        else:
            filters["categories"] = ["All"]

        if data.get("include_details"):
            filters["include_details"] = True
        else:
            filters["include_details"] = False

        if self.currency_id:
            filters["currency"] = self.currency_id.name
            filters["currency_id"] = self.currency_id.id
        else:
            filters["currency_id"] = False

        filters["partners_list"] = data.get("partners_list")
        filters["category_list"] = data.get("category_list")
        filters["company_name"] = data.get("company_name")
        filters['ageing_by'] = dict(self._fields['ageing_by'].selection)[data.get('ageing_by', 'inv_date')]

        return filters

    def prepare_bucket_list(self):
        periods = {}
        date_from = self.as_on_date
        date_from = fields.Date.from_string(date_from)

        # lang = self.env.user.lang
        # language_id = self.env['res.lang'].search([('code', '=', lang)])[0]

        bucket_list = [
            self.bucket_1,
            self.bucket_2,
            self.bucket_3,
            self.bucket_4,
            self.bucket_5,
        ]

        start = False

        stop = date_from
        name = "Not Due"
        periods[0] = {
            "bucket": "As on",
            "name": name,
            "start": "",
            "stop": stop.strftime("%Y-%m-%d"),
        }
        if self.ageing_by != "due_date":
            periods[0]['stop'] = datetime.datetime(9999, 12, 31)

        stop = date_from
        final_date = False
        for i in range(5):
            start = stop
            if self.ageing_by != "due_date" and i != 0:
                start -= relativedelta(days=1)
            stop_day = bucket_list[i]
            if i != 0:
                stop_day = bucket_list[i] - bucket_list[i - 1]
            stop = start - relativedelta(days=stop_day)
            name = (
                "0 - " + str(bucket_list[0])
                if i == 0
                else str(str(bucket_list[i - 1] + 1)) + " - " + str(bucket_list[i])
            )
            final_date = stop
            periods[i + 1] = {
                "bucket": bucket_list[i],
                "name": name,
                "start": start.strftime("%Y-%m-%d"),
                "stop": stop.strftime("%Y-%m-%d"),
            }

        start = final_date - relativedelta(days=1)
        stop = ""
        name = str(self.bucket_5) + " +"

        periods[6] = {
            "bucket": "Above",
            "name": name,
            "start": start.strftime("%Y-%m-%d"),
            "stop": "",
        }
        return periods

    def get_exclude_exch_journal_id(self):
        if not self.include_exch_rate_entries:
            return self.company_id.currency_exchange_journal_id.id
        return False

    def get_move_ids_to_exclude(self, partner_id=False):
        excl_accounts = self.company_id.partner_ageing_exclude_accounts._ids
        if excl_accounts:
            excl_accounts += (0,)
            sql = f"""select distinct move_id from account_move_line where account_id in {excl_accounts} and company_id={self.company_id.id}"""
            if partner_id:
                sql += f""" and partner_id={partner_id}"""
            self._cr.execute(sql)
            fetched = self._cr.fetchall()
            move_ids_to_exclude = tuple(row[0] for row in fetched if row[0] is not None)
            if move_ids_to_exclude:
                return move_ids_to_exclude + (0,)
            return False
        return False

    def process_detailed_data(self, offset=0, partner=0, fetch_range=FETCH_RANGE):
        """

        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list of dict)
        """
        as_on_date = self.as_on_date
        period_dict = self.prepare_bucket_list()
        period_list = [period_dict[a]["name"] for a in period_dict]
        company_id = self.env.user.company_id

        type = ("receivable", "payable")
        if self.type:
            type = tuple([self.type, "none"])

        offset = offset * fetch_range
        count = 0

        exclude_exch_journal_id = self.get_exclude_exch_journal_id()
        move_state_clause = (not self.include_unposted_entries and " AND m.state = 'posted'") or ''

        if partner:

            sql = f"""
                    SELECT COUNT(*)
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN 
                        account_invoice AS inv ON (l.invoice_id=inv.id)
                    LEFT JOIN 
                        account_payment_term AS pt ON (inv.payment_term_id=pt.id)
                    WHERE
                        l.balance <> 0
                        {move_state_clause}
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                        AND (l.invoice_id IS NOT NULL 
                            OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                            OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                            )
                            """
            if exclude_exch_journal_id:
                sql += f" AND j.id != {exclude_exch_journal_id}"

            exclude_move_ids = self.get_move_ids_to_exclude(partner)
            if exclude_move_ids:
                sql += f" AND m.id not in {exclude_move_ids}"

            if self.currency_id:
                sql += " AND l.currency_id=%s" % (self.currency_id.id)

            if self.salesperson.id:
                sql += " AND inv.user_id=%s" % (self.salesperson.id)

            self.env.cr.execute(sql % (type, partner, as_on_date, company_id.id))
            count = self.env.cr.fetchone()[0]

            SELECT = """SELECT m.name AS move_name,
                                m.id AS move_id,
                                l.date AS date,
                                l.date_maturity AS date_maturity,
                                j.name AS journal_name,
                                cc.id AS company_currency_id,
                                l.currency_id AS currency_id,
                                inv.reference AS reference,
                                inv.date_invoice AS date_invoice,
                                pt.name AS payment_term,
                                a.name AS account_name, """

            for period in period_dict:
                if not self.currency_id:
                    if period_dict[period].get("start") and period_dict[period].get(
                        "stop"
                    ):
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) >= '%s' AND
                                            COALESCE(l.date_maturity,l.date) <= '%s'
                                        THEN
                                            sum(l.balance) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            period_dict[period].get("start"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )
                    elif not period_dict[period].get("start"):
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) >= '%s'
                                        THEN
                                            sum(
                                                l.balance
                                                ) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )
                    else:
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) <= '%s'
                                        THEN
                                            sum(
                                                l.balance
                                                ) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s """ % (
                            period_dict[period].get("start"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )
                else:
                    if period_dict[period].get("start") and period_dict[period].get(
                        "stop"
                    ):
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) >= '%s' AND
                                            COALESCE(l.date_maturity,l.date) <= '%s'
                                        THEN
                                            sum(
                                                l.amount_currency
                                                ) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            period_dict[period].get("start"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )
                    elif not period_dict[period].get("start"):
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) >= '%s'
                                        THEN
                                            sum(
                                                l.amount_currency
                                                ) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )
                    else:
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) <= '%s'
                                        THEN
                                            sum(
                                                l.amount_currency
                                                ) +
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                ) -
                                            sum(
                                                COALESCE(
                                                    (SELECT
                                                        SUM(amount_currency)
                                                    FROM account_partial_reconcile
                                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                    )
                                                )
                                        ELSE
                                            0
                                        END AS %s """ % (
                            period_dict[period].get("start"),
                            as_on_date,
                            as_on_date,
                            "range_" + str(period),
                        )

            if not self.ageing_by or self.ageing_by == 'inv_date':
                SELECT = SELECT.replace("COALESCE(l.date_maturity,l.date)", "l.date")

            sql = f"""
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN
                        res_currency AS cc ON l.company_currency_id = cc.id
                    LEFT JOIN
                        account_invoice inv ON (l.invoice_id=inv.id)
                    LEFT JOIN 
                        account_payment_term AS pt ON (inv.payment_term_id=pt.id)
                    WHERE
                        l.balance <> 0
                        {move_state_clause}
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                        AND (l.invoice_id IS NOT NULL 
                            OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                            OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                            )
                            """
            if exclude_exch_journal_id:
                sql += f"AND j.id != {exclude_exch_journal_id}"

            if exclude_move_ids:
                sql += f" AND m.id not in {exclude_move_ids}"

            last_section = """
                    GROUP BY
                        l.date, l.date_maturity, m.id, m.name, j.name, a.name, cc.id, l.currency_id, reference, payment_term, date_invoice
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                """ % (
                offset,
                fetch_range,
            )

            if self.salesperson.id:
                sql += " AND inv.user_id=%s" % (self.salesperson.id)

            if self.currency_id:
                sql += " AND l.currency_id=%s" % (self.currency_id.id)
            self.env.cr.execute(
                SELECT + sql % (type, partner, as_on_date, company_id.id) + last_section
            )
            final_list = self.env.cr.dictfetchall() or 0.0
            move_lines = []
            if not self.ageing_by or self.ageing_by == 'inv_date':
                date_field = 'date'
            else:
                date_field = 'date_maturity'
            for m in final_list:
                if m[date_field] or m['date']:
                    m['date_invoice'] = str((self.as_on_date - (m[date_field] or m['date'])).days) + " days"
                else:
                    m['date_invoice'] = "-"
                if not m['payment_term']:
                    m['payment_term'] = ""
                if (
                        round(m["range_0"], 2)
                        or round(m["range_1"], 2)
                        or round(m["range_2"], 2)
                        or round(m["range_3"], 2)
                        or round(m["range_4"], 2)
                        or round(m["range_5"], 2)
                        or round(m["range_6"], 2)
                ):
                    move_lines.append(m)
            if move_lines:
                if self.ageing_by != 'due_date':  # hide not due for by inv date
                    period_list[0] = ''
                return count, offset, move_lines, period_list
            else:
                return 0, 0, [], []

    def process_data(self):
        """ Query Start Here
        ['partner_id':
            {'0-30':0.0,
            '30-60':0.0,
            '60-90':0.0,
            '90-120':0.0,
            '>120':0.0,
            'as_on_date_amount': 0.0,
            'total': 0.0}]
        1. Prepare bucket range list from bucket values
        2. Fetch partner_ids and loop through bucket range for values
        """
        period_dict = self.prepare_bucket_list()
        company_id = self.env.user.company_id
        domain = ["|", ("company_id", "=", company_id.id), ("company_id", "=", False)]
        if self.partner_type == "customer":
            domain.append(("customer", "=", True))
        if self.partner_type == "supplier":
            domain.append(("supplier", "=", True))

        if self.partner_category_ids:
            domain.append(("category_id", "in", self.partner_category_ids.ids))

        partner_ids = self.partner_ids or self.env["res.partner"].search(domain)
        as_on_date = self.as_on_date
        company_currency_id = company_id.currency_id.id

        exclude_exch_journal_id = self.get_exclude_exch_journal_id()

        type = ("receivable", "payable")
        if self.type:
            type = tuple([self.type, "none"])

        partner_dict = {}
        for partner in partner_ids:
            partner_dict.update({partner.id: {}})

        partner_dict.update({"Total": {}})
        for period in period_dict:
            partner_dict["Total"].update({period_dict[period]["name"]: 0.0})
        partner_dict["Total"].update({"total": 0.0, "partner_name": "ZZZZZZZZZ"})
        partner_dict["Total"].update({"company_currency_id": company_currency_id})

        move_state_clause = (not self.include_unposted_entries and " AND m.state = 'posted'") or ''
        partners_info = self.query_fetch(f"SELECT id,name,ref FROM res_partner WHERE id in {partner_ids._ids + (0, 0)} AND active=True ",
                                         obj_format=True, fetchall=True)
        for partner in partners_info:
            exclude_move_ids = self.get_move_ids_to_exclude(partner.id)

            partner_name = partner.name or ''
            if self.include_partner_ref and partner.ref:
                partner_name += f' ({partner.ref})'

            partner_dict[partner.id].update({"partner_name": partner_name})
            total_balance = 0.0
            sql = f"""
                SELECT
                    COUNT(*) AS count
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                LEFT JOIN
                    account_account_type AS ty ON a.user_type_id = ty.id
                LEFT JOIN
                    account_invoice AS inv ON inv.id = l.invoice_id
                LEFT JOIN
                    account_journal AS j ON j.id = l.journal_id
                WHERE
                    l.balance <> 0
                    {move_state_clause}
                    AND ty.type IN %s
                    AND l.partner_id = %s
                    AND l.company_id = %s
                    AND (l.invoice_id IS NOT NULL 
                        OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                        OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                        )
                            """
            if exclude_exch_journal_id:
                sql += f"AND j.id != {exclude_exch_journal_id}"

            if exclude_move_ids:
                sql += f" AND m.id not in {exclude_move_ids}"

            where = " AND l.date <= '%s'" % (as_on_date)

            self.env.cr.execute(sql % (type, partner.id, company_id.id))
            if self.salesperson.id:
                sql += " AND inv.user_id=%s" % (self.salesperson.id)

            if self.ageing_by == "due_date":
                where = " AND l.date_maturity <= '%s'" % (as_on_date)
            if self.currency_id:
                sql += " AND l.currency_id = %s" % (self.currency_id.id)
            sql += where
            self.env.cr.execute(sql % (type, partner.id, company_id.id))
            fetch_dict = self.env.cr.dictfetchone() or 0.0
            count = fetch_dict.get("count") or 0.0

            if count:
                for period in period_dict:
                    if not self.ageing_by or self.ageing_by == 'inv_date':
                        if period_dict[period].get("start") and period_dict[period].get("stop"):  # all ranges
                            where = " AND l.date BETWEEN '%s' AND '%s'" % (
                            period_dict[period].get("stop"),
                            period_dict[period].get("start"),
                        )
                        elif not period_dict[period].get("start"):  # not due
                            where = " AND 1=0 "
                        else:  # before last range
                            where = " AND l.date <= '%s'" % (
                            period_dict[period].get("start")
                        )
                    else:  # self.ageing_by == due_date
                        where = " AND l.date <= '%s' " % (as_on_date)
                        if period_dict[period].get("start") and period_dict[period].get("stop"):  # all ranges
                            where += " AND l.date_maturity BETWEEN '%s' AND '%s'" % (
                                period_dict[period].get("stop"),
                                period_dict[period].get("start"),
                            )
                        elif not period_dict[period].get("start"):  # not due
                            where += " AND l.date_maturity > '%s'" % (
                                period_dict[period].get("stop")
                            )
                        else:  # before last range
                            where += " AND l.date_maturity <= '%s'" % (
                                period_dict[period].get("start")
                            )
                    # where = " AND l.date <= CAST('%s' as DATE AND l.partner_id = %s AND COALESCE(l.date_maturity,l.date) " % (
                    #     as_on_date, partner.id)
                    # if period_dict[period].get('start') and period_dict[period].get('stop'):
                    #     where += " BETWEEN CAST('%s' as DATE AND CAST('%s' as DATE" % (
                    #         period_dict[period].get('stop'), period_dict[period].get('start'))
                    # elif not period_dict[period].get('start'):  # ie just
                    #     where += " >= CAST('%s' as DATE" % (period_dict[period].get('stop'))
                    # else:
                    #     where += " <= CAST('%s' as DATE" % (
                    #         period_dict[period].get('start'))
                    if self.currency_id and self.currency_id != self.company_id.currency_id:
                        q = """ sum(COALESCE(l.amount_currency, 0)) AS balance,
                            sum(COALESCE((SELECT SUM(amount_currency)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount_currency) FROM account_partial_reconcile
                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_credit"""
                    else:
                        q = """ sum(COALESCE(l.balance, 0)) AS balance,
                            sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile
                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_credit"""
                    sql = f"""
                        SELECT
                           {q}      
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        LEFT JOIN
                            account_invoice AS inv ON inv.id = l.invoice_id
                        LEFT JOIN
                            account_journal AS j ON j.id = l.journal_id
                        WHERE
                            l.balance <> 0
                            {move_state_clause}
                            AND ty.type IN %s
                            AND l.company_id = %s
                            AND l.partner_id = %s
                            AND (l.invoice_id IS NOT NULL 
                                OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                                OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                                )
                            """
                    if exclude_exch_journal_id:
                        sql += f"AND j.id != {exclude_exch_journal_id}"

                    if exclude_move_ids:
                        sql += f" AND m.id not in {exclude_move_ids}"

                    if self.salesperson.id:
                        sql += " AND inv.user_id=%s" % (self.salesperson.id)

                    if self.currency_id:
                        sql += " AND l.currency_id = %s" % (self.currency_id.id)
                    sql += where

                    self.env.cr.execute(
                        sql % (as_on_date, as_on_date, type, company_id.id, partner.id)
                    )
                    fetch_dict = self.env.cr.dictfetchall() or 0.0

                    # if not self.currency_id:
                    amount = (
                            (fetch_dict[0].get("balance") or 0.0)
                        + (fetch_dict[0].get("sum_debit") or 0.0)
                        - (fetch_dict[0].get("sum_credit") or 0.0)
                    )
                    # else:
                    #     amount = fetch_dict[0].get("balance_currency") or 0.0

                    if amount:
                        amount = round(amount, 2)
                        total_balance += amount
                        partner_dict[partner.id].update(
                            {period_dict[period]["name"]: amount}
                        )
                        partner_dict["Total"][period_dict[period]["name"]] += amount
                partner_dict[partner.id].update({"count": count})
                partner_dict[partner.id].update({"pages": self.get_page_list(count)})
                partner_dict[partner.id].update(
                    {"single_page": True if count <= FETCH_RANGE else False}
                )
                partner_dict[partner.id].update({"total": total_balance})
                partner_dict["Total"]["total"] += total_balance
                partner_dict[partner.id].update(
                    {"company_currency_id": company_currency_id}
                )
                partner_dict[partner.id].update(
                    {"currency_id": self.currency_id and self.currency_id.id}
                )
                partner_dict["Total"].update(
                    {"company_currency_id": company_currency_id}
                )
                partner_dict["Total"].update(
                    {"currency_id": self.currency_id and self.currency_id.id}
                )
            else:
                partner_dict.pop(partner.id, None)

        if self.display_accounts == "balance_not_zero":
            for key, value in list(partner_dict.items()):
                amount = value.get("total")
                if not round(amount, 2) or amount == 0:
                    del partner_dict[key]

        if self.ageing_by != 'due_date':  # hide not due for by inv date
            period_dict[0]['name'] = ''
        return period_dict, partner_dict

    def get_page_list(self, total_count):
        """
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        """
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    def get_report_datas(self, default_filters={}):
        """
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        """
        if self.validate_data():
            filters = self.process_filters()
            period_dict, ageing_lines = self.process_data()
            period_list = [period_dict[a]["name"] for a in period_dict]

            return filters, ageing_lines, period_dict, period_list

    def action_pdf(self):
        filters, ageing_lines, period_dict, period_list = self.get_report_datas()
        part_list = list(ageing_lines.keys())
        partner_list = [
            key[1] for key in filters["partners_list"] if key[0] in part_list
        ] or []
        partner_list = list(set(partner_list))
        partner_list.sort()
        partner_list.append("Total")
        return (
            self.env.ref("account_dynamic_reports" ".action_print_partner_ageing")
            .with_context(landscape=True)
            .report_action(
                self,
                data={
                    "Ageing_data": ageing_lines,
                    "Filters": filters,
                    "Period_Dict": period_dict,
                    "Period_List": period_list,
                    "partner_list": partner_list,
                },
            )
        )

    def action_xlsx(self):
        raise UserError(
            _(
                'Please install a free module "dynamic_xlsx".'
                'You can get it by contacting "pycustech@gmail.com". It is free'
            )
        )

    def action_view(self):
        res = {
            "type": "ir.actions.client",
            "name": "Ageing View",
            "tag": "dynamic.pa",
            "context": {"wizard_id": self.id},
        }
        return res
