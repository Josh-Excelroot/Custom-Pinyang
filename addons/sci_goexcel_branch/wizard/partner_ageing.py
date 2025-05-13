from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import datetime
from dateutil.relativedelta import relativedelta

# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

FETCH_RANGE = 2500


class InsPartnerAgeing(models.TransientModel):
    _inherit = "ins.partner.ageing"

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

        branch_ids = tuple([])
        if self.partner_category_ids:
            branch_ids = tuple(
                self.env['account.analytic.tag'].search([('name', 'in', self.partner_category_ids.mapped('name'))]).ids)
            if len(branch_ids) == 1:
                branch_ids = str(branch_ids).replace(',', '')

        type = ("receivable", "payable")
        if self.type:
            type = tuple([self.type, "none"])

        offset = offset * fetch_range
        count = 0

        if partner:

            sql = """
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
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                        AND (l.invoice_id IS NOT NULL 
                            OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                            OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                            )
                        AND (j.name != 'Exchange Difference' OR a.name ilike '%%FOREX%%')
                """
            if self.partner_category_ids:
                sql += f" AND m.branch in {branch_ids}"

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
                                                CASE WHEN l.amount_residual = 0 THEN 0
                                                     ELSE l.amount_residual_currency
                                                     END
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            period_dict[period].get("start"),
                            "range_" + str(period),
                        )
                    elif not period_dict[period].get("start"):
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) >= '%s'
                                        THEN
                                            sum(
                                                CASE WHEN l.amount_residual = 0 THEN 0
                                                     ELSE l.amount_residual_currency
                                                     END
                                                )
                                        ELSE
                                            0
                                        END AS %s,""" % (
                            period_dict[period].get("stop"),
                            "range_" + str(period),
                        )
                    else:
                        SELECT += """ CASE
                                        WHEN
                                            COALESCE(l.date_maturity,l.date) <= '%s'
                                        THEN
                                            sum(
                                                CASE WHEN l.amount_residual = 0 THEN 0
                                                     ELSE l.amount_residual_currency
                                                     END
                                                )
                                        ELSE
                                            0
                                        END AS %s """ % (
                            period_dict[period].get("start"),
                            "range_" + str(period),
                        )

            sql = """
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
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                        AND (l.invoice_id IS NOT NULL 
                            OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                            OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                            )
                        AND (j.name != 'Exchange Difference' OR a.name ilike '%%FOREX%%')
                """
            last_section = """
                    GROUP BY
                        l.date, l.date_maturity, m.id, m.name, j.name, a.name, cc.id, l.currency_id, reference, payment_term, date_invoice
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                """ % (
                offset,
                fetch_range,
            )
            if self.partner_category_ids:
                sql += f" AND m.branch in {branch_ids}"

            if self.salesperson.id:
                sql += " AND inv.user_id=%s" % (self.salesperson.id)

            if self.currency_id:
                sql += " AND l.currency_id=%s" % (self.currency_id.id)
            self.env.cr.execute(
                SELECT + sql % (type, partner, as_on_date, company_id.id) + last_section
            )
            final_list = self.env.cr.dictfetchall() or 0.0
            move_lines = []
            for m in final_list:
                if m['date_invoice']:
                    d1 = datetime.datetime.strptime(str(m['date_invoice']), '%Y-%m-%d') or datetime.datetime.now()
                    d2 = datetime.datetime.now()
                    d3 = d2 - d1
                    m['date_invoice'] = str(d3.days) + " days"
                else:
                    m['date_invoice'] = "-"
                if not m['payment_term']:
                    m['payment_term'] = ""
                if (
                    m["range_0"]
                    or m["range_1"]
                    or m["range_2"]
                    or m["range_3"]
                    or m["range_4"]
                    or m["range_5"]
                    or m["range_6"]
                ):
                    move_lines.append(m)
            if move_lines:
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

        branch_ids = tuple([])
        if self.partner_category_ids:
            branch_ids = tuple(self.env['account.analytic.tag'].search([('name', 'in', self.partner_category_ids.mapped('name'))]).ids)
            if len(branch_ids) == 1:
                branch_ids = str(branch_ids).replace(',', '')

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

        for partner in partner_ids:
            partner_dict[partner.id].update({"partner_name": partner.name})
            total_balance = 0.0
            sql = """
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
                    AND m.state = 'posted'
                    AND ty.type IN %s
                    AND l.partner_id = %s
                    AND l.company_id = %s
                    AND (l.invoice_id IS NOT NULL 
                        OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                        OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                        )
                    AND (j.name != 'Exchange Difference' OR a.name ilike '%%FOREX%%')
            """
            if self.partner_category_ids:
                sql += f" AND m.branch in {branch_ids}"

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
                    where = " AND l.date <= '%s'" % (as_on_date)
                    if period_dict[period].get("start") and period_dict[period].get(
                        "stop"
                    ):
                        where += " AND l.date BETWEEN '%s' AND '%s'" % (
                            period_dict[period].get("stop"),
                            period_dict[period].get("start"),
                        )
                    elif not period_dict[period].get("start"):  # ie just
                        where += " AND l.date >= '%s'" % (
                            period_dict[period].get("stop")
                        )
                    else:
                        where += " AND l.date <= '%s'" % (
                            period_dict[period].get("start")
                        )
                    if self.ageing_by == "due_date":
                        where = " AND l.date_maturity <= '%s' " % (as_on_date)
                        if period_dict[period].get("start") and period_dict[period].get(
                            "stop"
                        ):
                            where += " AND l.date_maturity BETWEEN '%s' AND '%s'" % (
                                period_dict[period].get("stop"),
                                period_dict[period].get("start"),
                            )
                        elif not period_dict[period].get("start"):  # ie just
                            where += " AND l.date_maturity >= '%s'" % (
                                period_dict[period].get("stop")
                            )
                        else:
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

                    sql = """
                        SELECT
                            sum(COALESCE(l.balance, 0)) AS balance,
                            sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile
                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_credit,
                            sum(CASE WHEN l.amount_residual = 0 THEN 0
                                     ELSE l.amount_residual_currency
                                     END ) AS balance_currency
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
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.company_id = %s
                            AND l.partner_id = %s
                            AND (l.invoice_id IS NOT NULL 
                                OR (l.payment_id IS NULL AND l.invoice_id IS NULL)
                                OR (l.payment_id IS NOT NULL AND (l.amount_residual != 0 or l.balance != 0))
                                )
                            AND (j.name != 'Exchange Difference' OR a.name ilike '%%FOREX%%')
                    """
                    if self.partner_category_ids:
                        sql += f" AND m.branch in {branch_ids}"

                    if self.salesperson.id:
                        sql += " AND inv.user_id=%s" % (self.salesperson.id)

                    if self.currency_id:
                        sql += " AND l.currency_id = %s" % (self.currency_id.id)
                    sql += where
                    amount = 0.0
                    self.env.cr.execute(
                        sql % (as_on_date, as_on_date, type, company_id.id, partner.id)
                    )
                    fetch_dict = self.env.cr.dictfetchall() or 0.0

                    if not self.currency_id:
                        amount = (
                                (fetch_dict[0].get("balance") or 0.0)
                                + (fetch_dict[0].get("sum_debit") or 0.0)
                                - (fetch_dict[0].get("sum_credit") or 0.0)
                        )
                    else:
                        amount = fetch_dict[0].get("balance_currency") or 0.0

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
        return period_dict, partner_dict
