# -*- coding: utf-8 -*-

import datetime
import time

from odoo import api, fields, models, _
from odoo import tools


class AccountFollowupStatByPartner(models.Model):
    _name = "payment.followup.by.partner"
    _description = "Follow-up Statistics by Partner"
    _rec_name = 'partner_id'
    _auto = False

    @api.multi
    def _get_invoice_partner_id(self):
        for rec in self:
            rec.invoice_partner_id = rec.partner_id.address_get(adr_pref=['invoice']).get('invoice', rec.partner_id.id)

    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    date_move = fields.Date('First move', readonly=True)
    date_move_last = fields.Date('Last move', readonly=True)
    date_followup = fields.Date('Latest follow-up', readonly=True)
    max_followup_id = fields.Many2one('payment.followup.line', 'Max Follow Up Level', readonly=True, ondelete="cascade")
    balance = fields.Float('Balance', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    invoice_partner_id = fields.Many2one('res.partner', compute='_get_invoice_partner_id', string='Invoice Address')

    _depends = {
        'account.move.line': [
            'account_id', 'company_id', 'credit', 'date', 'debit',
            'followup_date', 'followup_line_id', 'partner_id',
            'full_reconcile_id',
        ],
        'account.account': ['user_type_id'],
    }

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'payment_followup_by_partner')
        # Here we don't have other choice but to create a virtual ID based on
        # the concatenation of the partner_id and the company_id, because if
        #  a partner is shared between 2 companies, we want to see 2 lines
        # for him in this table. It means that both company should be able
        # to send him follow-ups separately . An assumption that the number
        # of companies will not reach 10 000 records is made, what should be
        #  enough for a time.
        self._cr.execute("""
            create view payment_followup_by_partner as (
                SELECT
                    l.partner_id * 10000::bigint + l.company_id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS date_move,
                    max(l.date) AS date_move_last,
                    max(l.followup_date) AS date_followup,
                    max(l.followup_line_id) AS max_followup_id,
                    sum(l.debit - l.credit) AS balance,
                    l.company_id as company_id
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.user_type_id IN (SELECT id FROM account_account_type
                    WHERE type = 'receivable') AND
                    l.full_reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                    GROUP BY
                    l.partner_id, l.company_id
            )""")


class AccountFollowupAuto(models.TransientModel):
    _name = 'payment.automatic'
    _description = 'Send SOA or Overdue Invoice or Both'

    def _get_followup(self):
        if self.env.context.get('active_model', 'ir.ui.menu') == 'payment.followup':
            return self.env.context.get('active_id', False)
        company_id = self.env.user.company_id.id
        followp_id = self.env['payment.followup'].search([('company_id', '=', company_id)], limit=1)
        return followp_id or False

    def _get_partner_ids(self):
        tmp = self._get_partners_followp()
        partner_list = tmp['partner_ids']
        #print ("partner_list", partner_list)

    date = fields.Date('Follow-up Sending Date', required=True, help="This field allow you to select a forecast date to plan your follow-ups", default=lambda *a: time.strftime('%Y-%m-%d'))
    followup_id = fields.Many2one('payment.followup', 'Follow-Up', required=True, readonly=True, default=_get_followup)
    partner_ids = fields.Many2many('res.partner', 'partner_stat_rel', 'osv_memory_id', 'partner_id', 'Partners', required=True, default=_get_partner_ids)
    company_id = fields.Many2one('res.company', readonly=True, related='followup_id.company_id')
    email_conf = fields.Boolean('Send Email Confirmation')
    email_subject = fields.Char('Email Subject', size=64, default=_('Invoices Reminder'))
    partner_lang = fields.Boolean('Send Email in Partner Language', default=True, help='Do not change message text, if you want to send email in partner language, or configure from company')
    email_body = fields.Text('Email Body', default='')
    summary = fields.Text('Summary', readonly=True)
    test_print = fields.Boolean('Test Print', help='Check if you want to print follow-ups without changing follow-up level.')

    @api.multi
    def check_progress(self):
        pass

    def do_process(self):
        context = dict(self.env.context or {})
        #print('>>>>>>>>>>>> do_process')
        # Get partners
        tmp = self._get_partners_followp()
        partner_list = tmp['partner_ids']
        to_update = tmp['to_update']
        # date = self.browse(cr, uid, ids, context=context)[0].date
        date = self.date
        data = self.read()[0]
        data['followup_id'] = data['followup_id'][0]

        # Update partners
        self.do_update_followup_level(to_update, partner_list, date)
        # process the partners (send mails...)
        restot_context = context.copy()
        restot = self.with_context(restot_context).process_partners(partner_list, data)
        context.update(restot_context)
        # clear the manual actions if nothing is due anymore
        nbactionscleared = self.clear_manual_actions(partner_list)
        if nbactionscleared > 0:
            restot['resulttext'] = restot['resulttext'] + "<li>" + _(
                "%s partners have no credits and as such the "
                "action is cleared") % (str(nbactionscleared)) + "</li>"
        # return the next action
        resource_id = self.env.ref('payment_followup_management.view_payment_followup_management_sending_results')
        context.update({'description': restot['resulttext'],
                        'needprinting': restot['needprinting'],
                        'report_data': restot['action']})
        return {
            'name': _('Send Letters and Emails: Actions Summary'),
            'view_type': 'form',
            'context': context,
            'view_mode': 'tree,form',
            'res_model': 'payment_followup_management.sending.results',
            'views': [(resource_id.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            }


    def _get_partners_followp(self):
        data = self
        # company_id = data.company_id.id
        company_id = self.env.user.company_id.id
        context = self.env.context
        self._cr.execute(
            '''SELECT
                    l.partner_id,
                    l.followup_line_id,
                    l.date_maturity,
                    l.date, l.id
                FROM account_move_line AS l
                LEFT JOIN account_account AS a
                ON (l.account_id=a.id)
                WHERE (l.full_reconcile_id IS NULL)
                AND a.user_type_id IN (SELECT id FROM account_account_type
                    WHERE type = 'receivable')
                AND (l.partner_id is NOT NULL)
                AND (l.debit > 0)
                AND (l.company_id = %s)
                AND (l.blocked = False)
                ORDER BY l.date''' % (company_id))
        # l.blocked added to take litigation into account and it is not
        # necessary to change follow-up level of account move lines
        # without debit
        move_lines = self._cr.fetchall()
        #print('>>>>>>>>>>>> _get_partners_followp move_lines=', move_lines)
        old = None
        fups = {}
        fup_id = 'followup_id' in context and context['followup_id'] or data.followup_id.id
        if not fup_id:
            fup_id = self.env['payment.followup'].search([('company_id', '=', company_id)], limit=1).id
        # date = 'date' in context and context['date'] or data.date
        date = time.strftime('%Y-%m-%d')

        current_date = datetime.date(*time.strptime(str(date), '%Y-%m-%d')[:3])
        self._cr.execute(
            '''SELECT *
            FROM payment_followup_line
            WHERE followup_id=%s
            ORDER BY delay''' % (fup_id,))

        # Create dictionary of tuples where first element is the date to
        # compare with the due date and second element is the id of the
        # next level
        for result in self._cr.dictfetchall():
            delay = datetime.timedelta(days=result['delay'])
            fups[old] = (current_date - delay, result['id'])
            old = result['id']

        partner_list = []
        to_update = {}

        # Fill dictionary of accountmovelines to_update with the partners
        # that need to be updated
        for partner_id, followup_line_id, date_maturity, date, id in move_lines:
            if not partner_id:
                continue
            if followup_line_id not in fups:
                continue
            stat_line_id = partner_id * 10000 + company_id
            if date_maturity:
                ##print(date_maturity, fups[followup_line_id][0].strftime('%Y-%m-%d'))
                if str(date_maturity) <= fups[followup_line_id][0].strftime('%Y-%m-%d'):
                    if stat_line_id not in partner_list:
                        partner_list.append(stat_line_id)
                    to_update[str(id)] = {'level': fups[followup_line_id][1],
                                          'partner_id': stat_line_id}
            elif date and date <= fups[followup_line_id][0].strftime(
                    '%Y-%m-%d'):
                if stat_line_id not in partner_list:
                    partner_list.append(stat_line_id)
                to_update[str(id)] = {'level': fups[followup_line_id][1],
                                      'partner_id': stat_line_id}
        #print('>>>>>>>>>>>> _get_partners_followp partner_list=', partner_list, ' , to_update=', to_update)
        return {'partner_ids': partner_list, 'to_update': to_update}
