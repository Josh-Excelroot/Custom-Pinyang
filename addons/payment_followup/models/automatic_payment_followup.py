# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import tools
import datetime
import time
import base64
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)
# from datetime import timedelta


# class AccountFollowupByPartner(models.Model):
#     _name = "payment.followup.by.partner"
#     _description = "Follow-up Statistics by Partner"
#     _rec_name = 'partner_id'
#     _auto = False

#     # @api.multi
#     # def _get_invoice_partner_id(self):
#     #     for rec in self:
#     #         rec.invoice_partner_id = rec.partner_id.address_get(adr_pref=['invoice']).get('invoice', rec.partner_id.id)

#     partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
#     date_move = fields.Date('First move', readonly=True)
#     date_move_last = fields.Date('Last move', readonly=True)
#     date_followup = fields.Date('Latest follow-up', readonly=True)
#     max_followup_id = fields.Many2one('payment.followup.line', 'Last Follow Up Level', readonly=True, ondelete="cascade")
#     balance = fields.Float('Balance', readonly=True)
#     company_id = fields.Many2one('res.company', 'Company', readonly=True)
#     # invoice_partner_id = fields.Many2one('res.partner', compute='_get_invoice_partner_id', string='Invoice Address')

#     _depends = {
#         'account.move.line': [
#             'account_id', 'company_id', 'credit', 'date', 'debit',
#             'followup_date', 'followup_line_id', 'partner_id',
#             'full_reconcile_id',
#         ],
#         'account.account': ['user_type_id'],
#     }

#     @api.model_cr
#     def init(self):
#         tools.drop_view_if_exists(self._cr, 'payment_followup_by_partner')
#         # Here we don't have other choice but to create a virtual ID based on
#         # the concatenation of the partner_id and the company_id, because if
#         #  a partner is shared between 2 companies, we want to see 2 lines
#         # for him in this table. It means that both company should be able
#         # to send him follow-ups separately . An assumption that the number
#         # of companies will not reach 10 000 records is made, what should be
#         #  enough for a time.
#         self._cr.execute("""
#             create view payment_followup_by_partner as (
#                 SELECT
#                     l.partner_id * 10000::bigint + l.company_id as id,
#                     l.partner_id AS partner_id,
#                     min(l.date) AS date_move,
#                     max(l.date) AS date_move_last,
#                     max(l.followup_date) AS date_followup,
#                     max(l.followup_line_id) AS max_followup_id,
#                     sum(l.debit - l.credit) AS balance,
#                     l.company_id as company_id
#                 FROM
#                     account_move_line l
#                     LEFT JOIN account_account a ON (l.account_id = a.id)
#                 WHERE
#                     a.user_type_id IN (SELECT id FROM account_account_type
#                     WHERE type = 'receivable') AND
#                     l.full_reconcile_id is NULL AND
#                     l.partner_id IS NOT NULL
#                     GROUP BY
#                     l.partner_id, l.company_id
#             )""")


class AccountFollowupAuto(models.Model):
    _name = 'payment.automatic'
    _description = 'Send SOA or Overdue Invoice or Both'

    def _get_followup(self):
        if self.env.context.get('active_model', 'ir.ui.menu') == 'payment.followup':
            return self.env.context.get('active_id', False)
        company_id = self.env.user.company_id.id
        followp_id = self.env['payment.followup'].search([('company_id', '=', company_id)], limit=1)
        return followp_id or False

    # def _get_partner_ids(self):
    #     for res in self:
    #         tmp = tmp = self._get_partners_followp()
    #         res.partner_ids = tmp['partner_ids']

    date = fields.Date('Follow-up Sending Date', required=True, help="This field allow you to select a forecast date to plan your follow-ups", default=lambda *a: time.strftime('%Y-%m-%d'))
    followup_id = fields.Many2one('payment.followup', 'Follow-Up', required=True, readonly=True, default=_get_followup)
    # partner_ids = fields.Many2many('payment.followup.by.partner', 'partner_stat_rel', 'osv_memory_id', 'partner_id', 'Partners', required=True)
    company_id = fields.Many2one('res.company', readonly=True, related='followup_id.company_id')

    def _get_partners_followp(self):
        data = self
        # company_id = data.company_id.id
        company_id = self.env.user.company_id.id
        context = self.env.context
        #Get all the invoices that are not yet paid.
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
                AND (l.move_id in (SELECT id FROM account_move WHERE id in (SELECT move_id FROM account_invoice WHERE type='out_invoice' AND state='open')))
                ORDER BY l.date''' % (company_id))
        # l.blocked added to take litigation into account and it is not
        # necessary to change follow-up level of account move lines
        # without debit
        move_lines = self._cr.fetchall()
       #print('>>>>>>>>>>>>>>>>>> _get_partners_followp 1')
        old = None
        fups = {}
        fup_id = 'followup_id' in context and context['followup_id'] or data.followup_id.id
        if not fup_id:
            fup_id = self.env['payment.followup'].search([('company_id', '=', company_id)], limit=1).id
        # date = 'date' in context and context['date'] or data.date
        date = time.strftime('%Y-%m-%d')
        current_date = datetime.date(*time.strptime(str(date), '%Y-%m-%d')[:3])
        self._cr.execute('''SELECT * FROM payment_followup_line WHERE followup_id=%s ORDER BY delay''' % (fup_id,))
        # Create dictionary of tuples where first element is the date to
        # compare with the due date and second element is the id of the
        # next level
        for result in self._cr.dictfetchall():
            delay = datetime.timedelta(days=result['delay'])
            fups[old] = (current_date - delay, result['id'])
            #print('>>>>>>>>>>>>>>>>>> _get_partners_followp 0 if 4441 =', fups[old])
            old = result['id']
        partner_list = []
        partner_data_list = []
        to_update = {}
        # Fill dictionary of accountmovelines to_update with the partners
        # that need to be updated
        for partner_id, followup_line_id, date_maturity, date, id in move_lines:
            partner_data = {}
            if not partner_id:
                continue
            # Comment line - 157 - 170 /Add line - 149 - 152 -> Issue: Followup Level is not working properly - 9 aug'22
            partner = self.env['res.partner'].sudo().browse(partner_id)
            followup_line_id = partner.last_followup_level_id.id
            if not followup_line_id:
                followup_line_id = None
            if followup_line_id not in fups:
                continue
            #TS - 09/10/2022 Shld not send out the payment followup if the date maturity (due date) is not due
            if date_maturity:
                # if partner_id == 4441:
                #     print('>>>>>>>>>>>>>>>>>> _get_partners_followp 2 if 4441=', date_maturity, ' VS ',
                # fups[followup_line_id][0].strftime('%Y-%m-%d'), ' Level=', fups[followup_line_id][1])
                # #partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
                #to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
                # if partner.follow_histry_ids:
                #     history_ids = partner.follow_histry_ids.sorted(key=lambda t: t.earliyest_duedate)
                #     if history_ids[0].earliyest_duedate < datetime.date.today():
                #         if partner_id == 4441:
                #             print('>>>>>>>>>>>>>>>>>> _get_partners_followp 3')
                #         if partner_id not in partner_list:
                #             partner_list.append(partner_id)
                #             to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
                #             partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
                # else:
                if date_maturity < datetime.date.today():
                    # if partner_id == 4441:
                    #     print('>>>>>>>>>>>>>>>>>> _get_partners_followp 3')
                    if partner_id not in partner_list:
                        partner_list.append(partner_id)
                        to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
                        partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
                        if partner_data not in partner_data_list:
                            partner_data_list.append(partner_data)
                        # if partner_id == 4441:
                        #     print('>>>>>>>>>>>>>>>>>> _get_partners_followp 4')
            # if followup_line_id and str(date_maturity) <= fups[followup_line_id][0].strftime('%Y-%m-%d'):
                #     if partner_id == 4441:
                #         print('>>>>>>>>>>>>>>>>>> _get_partners_followp 3')
                #     if partner_id not in partner_list:
                #         partner_list.append(partner_id)
                #         to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
                #         partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
            # if not followup_line_id:
            #     partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
            #     to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
            # if date_maturity:
            #     if str(date_maturity) <= fups[followup_line_id][0].strftime('%Y-%m-%d'):
            #         if partner_id not in partner_list:
            #             partner_list.append(partner_id)
            #         to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
            #     partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
            # elif date and date <= fups[followup_line_id][0].strftime('%Y-%m-%d'):
            #     if partner_id not in partner_list:
            #         partner_list.append(partner_id)
            #     to_update[str(id)] = {'level': fups[followup_line_id][1], 'partner_id': partner_id}
            #     partner_data = {'partner_id': partner_id, 'next_follow_up_id': fups[followup_line_id][1]}
            #         if partner_data not in partner_data_list:
            #             partner_data_list.append(partner_data)
        #print('>>>>>>>>>>>>>>>>>> _get_partners_followp partner_list=', partner_list)
        #print('>>>>>>>>>>>>>>>>>> _get_partners_followp partner_data_list=', partner_data_list)
        return {'partner_ids': partner_list, 'to_update': to_update, 'partner_data_list': partner_data_list}

    # combine new method from 2 method and update data
    def process_partners(self, partner_ids, to_update, partner_list, date):
        # for partner in self.env['payment.followup.by.partner'].sudo().search([('partner_id', 'in', partner_ids)]):
        for partner in partner_ids:

            partner_id = self.env['res.partner'].sudo().browse(partner.get('partner_id'))
            if partner_id:
                follow_up_id = self.env['payment.followup.line'].sudo().browse(partner.get('next_follow_up_id'))
                if partner_id.followup_emails and not partner_id.bypass_auto_followup:
                    send_flag = self.check_last_reset_date(partner_id, follow_up_id)
                    if not send_flag:
                        continue
                    over_due_pdf = False
                    only_soa_pdf = False
                    open_pdf = False
                    history_data = {
                        "partner_id": partner_id.id,
                        "date": datetime.datetime.now(),
                        "sent_by": self.env.uid,
                        "overdue_amount": partner_id.payment_amount_overdue,
                        "due_amount": partner_id.payment_amount_due,
                        "earliyest_duedate": partner_id.payment_earliest_due_date,
                        'send_type': follow_up_id.send_type,
                        'last_followup_level_id': follow_up_id.id,
                        'action_type': follow_up_id.action_type
                        }
                    start_date = datetime.datetime.today().date().replace(day=1)
                    soa_invoice_date_type = self.env.user.company_id.soa_invoice_date_type
                    if soa_invoice_date_type == 'last_6_mth':
                        start_date = datetime.date.today() + datetime.timedelta(days=-180)
                        start_date = start_date.replace(day=1)
                    elif soa_invoice_date_type == 'beginning':
                        part_ids = self._context.get('active_ids')
                        partner_ids = self.env['res.partner'].sudo().browse(part_ids)
                        mv_line_domain = [('partner_id', '=', partner_ids[0].id), ('account_id.user_type_id.type', 'in', ['receivable', 'payable']), ('move_id.state', '<>', 'draft')]
                        move_lines = self.env['account.move.line'].sudo().search(mv_line_domain, order="date asc")
                        if move_lines:
                            for line in move_lines:
                                invoices = self.env['account.invoice'].sudo().search([('move_id', '=', line.move_id.id)])
                                if invoices:
                                    start_date = invoices[0].date_invoice.replace(day=1)
                                    break
                    elif soa_invoice_date_type == 'last_mth':
                        start_date = str(datetime.date.today() + relativedelta(months=-1, day=1))[:10]
                    else:  # current month
                        start_date = str(datetime.date.today() + relativedelta(day=1))[:10]

                    soa_type = 'all'
                    soa_type = self.env.user.company_id.soa_type
                    # Only SOA
                    if follow_up_id.send_type == 'soa':
                        # start_date = datetime.datetime.today().date().replace(day=1)
                        end_date = datetime.date.today() + relativedelta(months=+1, day=1, days=-1)
                        p_data = {
                            'invoice_end_date': end_date,
                            'invoice_start_date': start_date,
                            'aging_by': 'inv_date',
                            'aging_group': 'by_month',
                            'account_type': 'ar',
                            'soa_type': soa_type}
                        wiz_id = self.env['customer.statement'].create(p_data)
                        del p_data['invoice_end_date']
                        p_data.update({'overdue_date': end_date})
                        partner_id.write(p_data)
                        data = {
                            'ids': [wiz_id.id],
                            'model': 'customer.statement',
                            'form': [partner_id.id]
                            }
                        report_template_id = self.env.ref('goexcel_customer_statement.report_customer_statement').render_qweb_pdf(wiz_id.id, data=data)
                        data_record = base64.b64encode(report_template_id[0])
                        ir_values = {
                            'name': "Statement of Account.pdf",
                            'type': 'binary',
                            'datas': data_record,
                            'datas_fname': "Statement of Account.pdf",
                            'store_fname': 'Statement of Account',
                            'mimetype': 'application/pdf',
                        }
                        only_soa_pdf = self.env['ir.attachment'].create(ir_values)

                    # Only Overdue Invoices
                    if follow_up_id.send_type == 'overdue_invoices':
                        over_due_inv = self.env['account.invoice'].search([('date_due', '<=', datetime.date.today()), ('state', '=', 'open'), ('partner_id', '=', partner_id.id), ('type', '=', 'out_invoice')])
                        if len(over_due_inv) > 0:
                            # report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(over_due_inv.ids)
                            report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(over_due_inv.ids)

                            data_record = base64.b64encode(report_template_id[0])
                            ir_values = {
                               'name': "Overdue Invoices.pdf",
                               'type': 'binary',
                               'datas': data_record,
                               'datas_fname': "Overdue Invoices.pdf",
                               'store_fname': 'Overdue Invoices',
                               'mimetype': 'application/pdf',
                            }
                            over_due_pdf = self.env['ir.attachment'].create(ir_values)

                    # SOA + OverDue Invoices
                    if follow_up_id.send_type == 'soa_overdue':
                        # SOA Data Create
                        # start_date = datetime.datetime.today().date().replace(day=1)
                        end_date = datetime.date.today() + relativedelta(months=+1, day=1, days=-1)
                        p_data = {
                            'invoice_end_date': end_date,
                            'invoice_start_date': start_date,
                            'aging_by': 'inv_date',
                            'aging_group': 'by_month',
                            'account_type': 'ar',
                            'soa_type': soa_type}
                        wiz_id = self.env['customer.statement'].create(p_data)
                        del p_data['invoice_end_date']
                        p_data.update({'overdue_date': end_date})
                        partner_id.write(p_data)
                        data = {
                            'ids': [wiz_id.id],
                            'model': 'customer.statement',
                            'form': [partner_id.id]
                            }
                        report_template_id = self.env.ref('goexcel_customer_statement.report_customer_statement').render_qweb_pdf(wiz_id.id, data=data)
                        data_record = base64.b64encode(report_template_id[0])
                        ir_values = {
                            'name': "Statement of Account.pdf",
                            'type': 'binary',
                            'datas': data_record,
                            'datas_fname': "Statement of Account.pdf",
                            'store_fname': 'Statement of Account',
                            'mimetype': 'application/pdf',
                        }
                        only_soa_pdf = self.env['ir.attachment'].create(ir_values)
                        # overdue Invocie Created
                        over_due_inv = self.env['account.invoice'].search([('date_due', '<=', datetime.date.today()), ('state', '=', 'open'), ('partner_id', '=', partner_id.id), ('type', '=', 'out_invoice')])
                        if len(over_due_inv) > 0:
                            # report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(over_due_inv.ids)
                            report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(over_due_inv.ids)
                            data_record = base64.b64encode(report_template_id[0])
                            ir_values = {
                               'name': "Overdue Invoices.pdf",
                               'type': 'binary',
                               'datas': data_record,
                               'datas_fname': "Overdue Invoices.pdf",
                               'store_fname': 'Overdue Invoices',
                               'mimetype': 'application/pdf',
                            }
                            over_due_pdf = self.env['ir.attachment'].create(ir_values)

                    # Only Open Invoices
                    if follow_up_id.send_type == 'open_invoice':
                        open_invoice_ids = self.env['account.invoice'].search([('state', '=', 'open'), ('partner_id', '=', partner_id.id), ('type', '=', 'out_invoice')])
                        if len(open_invoice_ids) > 0:
                            report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(open_invoice_ids.ids)
                            data_record = base64.b64encode(report_template_id[0])
                            ir_values = {
                               'name': "Opne Invoices.pdf",
                               'type': 'binary',
                               'datas': data_record,
                               'datas_fname': "Opne Invoices.pdf",
                               'store_fname': 'Opne Invoices',
                               'mimetype': 'application/pdf',
                            }
                            open_pdf = self.env['ir.attachment'].create(ir_values)

                    # SOA + Open Invoice
                    if follow_up_id.send_type == 'soa_open':
                        end_date = datetime.date.today() + relativedelta(months=+1, day=1, days=-1)
                        p_data = {
                            'invoice_end_date': end_date,
                            'invoice_start_date': start_date,
                            'aging_by': 'inv_date',
                            'aging_group': 'by_month',
                            'account_type': 'ar',
                            'soa_type': soa_type,
                            'send_open_invoice': True}
                        wiz_id = self.env['customer.statement'].create(p_data)
                        del p_data['invoice_end_date']
                        p_data.update({'overdue_date': end_date})
                        partner_id.write(p_data)
                        data = {
                            'ids': [wiz_id.id],
                            'model': 'customer.statement',
                            'form': [partner_id.id]
                            }
                        report_template_id = self.env.ref('goexcel_customer_statement.report_customer_statement').render_qweb_pdf(wiz_id.id, data=data)
                        data_record = base64.b64encode(report_template_id[0])
                        ir_values = {
                            'name': "Statement of Account.pdf",
                            'type': 'binary',
                            'datas': data_record,
                            'datas_fname': "Statement of Account.pdf",
                            'store_fname': 'Statement of Account',
                            'mimetype': 'application/pdf',
                        }
                        only_soa_pdf = self.env['ir.attachment'].create(ir_values)
                        # Open Invocie Created
                        open_inv = self.env['account.invoice'].search([('state', '=', 'open'), ('partner_id', '=', partner_id.id), ('type', '=', 'out_invoice')])
                        if len(open_inv) > 0:
                            # report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(over_due_inv.ids)
                            report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(open_inv.ids)
                            data_record = base64.b64encode(report_template_id[0])
                            ir_values = {
                               'name': "open Invoices.pdf",
                               'type': 'binary',
                               'datas': data_record,
                               'datas_fname': "open Invoices.pdf",
                               'store_fname': 'open Invoices',
                               'mimetype': 'application/pdf',
                            }
                            open_pdf = self.env['ir.attachment'].create(ir_values)

                    template = False
                    try:
                        if follow_up_id.email_template_id:
                            template = follow_up_id.email_template_id
                        else:
                            if follow_up_id.send_type == 'soa':
                                template = self.env.ref('payment_followup.email_template_soa_customer_statement')
                            elif follow_up_id.send_type == 'overdue_invoices':
                                template = self.env.ref('payment_followup.email_template_overdue_customer_statement')
                            elif follow_up_id.send_type == 'soa_overdue':
                                template = self.env.ref('payment_followup.email_template_soa_overdue_customer_statement')
                            elif follow_up_id.send_type == 'open_invoice':
                                template = self.env.ref('payment_followup.email_template_open_customer_statement')
                            elif follow_up_id.send_type == 'soa_open':
                                template = self.env.ref('payment_followup.email_template_soa_open_customer_statement')
                    except ValueError:
                        template = False
                    if template:
                        template.attachment_ids = False
                        # TS - use the
                        template_values = {
                                'email_to': partner_id.followup_emails,
                                'email_cc': False,
                                'auto_delete': True,
                                'partner_to': False,
                            }
                        if over_due_pdf:
                            template.attachment_ids = [(4, over_due_pdf.id)]
                        if only_soa_pdf:
                            template.attachment_ids = [(4, only_soa_pdf.id)]
                        if open_pdf:
                            template.attachment_ids = [(4, open_pdf.id)]
                        template.sudo().write(template_values)
                        if send_flag:
                            template.sudo().send_mail(partner_id.id, force_send=True, raise_exception=False)
                            _logger.info(f'>>>>>>>>>>>>> Email send 1')

                            # body_html = template.body_html
                            # partner_id.message_post(body=body_html, subtype='mail.mt_comment')
                            partner_id.message_post_with_template(int(template.id))
                            if follow_up_id:
                                partner_data = {
                                    'last_sent_date': datetime.datetime.now(),
                                    'last_sent_by': self.env.uid,
                                    'last_followup_level_id': follow_up_id.id,
                                    'last_action_type': follow_up_id.action_type,
                                    'last_send_type': follow_up_id.send_type
                                    }
                                partner_id.write(partner_data)
                            template.attachment_ids = False
                            if over_due_pdf:
                                over_due_pdf.unlink()
                            self.env['partner.payment.followup'].create(history_data)
                            # update for partner move line
                            for id in to_update.keys():
                                if to_update[id]['partner_id'] in partner_list and to_update[id]['partner_id'] == partner_id.id:
                                    self.env['account.move.line'].browse([int(id)]).write({'followup_line_id': to_update[id]['level'], 'followup_date': date})
            self._cr.commit()

    def do_process(self):
        company_id = self.env.user.company_id.id
        #if payment follow level is configured
        fup_id = self.env['payment.followup'].search([('company_id', '=', company_id)], limit=1).id
        if not fup_id:
            return
        #print('>>>>>>>>>>> do_process')
        context = dict(self.env.context or {})
        tmp = self._get_partners_followp()
        partner_list = tmp['partner_ids']
        to_update = tmp['to_update']
        partner_data_list = tmp['partner_data_list']
        date = time.strftime('%Y-%m-%d')
        reset_context = context.copy()
        if len(partner_data_list) > 0:
            # remove call to old method by shivam
            # add to call new method by shivam
            self.with_context(reset_context).process_partners(partner_data_list, to_update, partner_list, date)

    def check_last_reset_date(self, partner, follow_up_id):
        _logger.info(f'>>>>>>>>>>>>> check_last_reset_date 1, {partner}, {follow_up_id}')
        bypass_date = partner.reset_date and partner.reset_date or self.company_id.go_live_date
        delay = follow_up_id and follow_up_id.delay or 0
        today = datetime.datetime.today().date()

        if bypass_date and today <= bypass_date:
            return False

        if bool(partner.last_followup_level_id) != bool(partner.last_sent_date):
            partner.reset_payment_followup_level()

        if partner.last_followup_level_id and partner.last_sent_date:
            sibling_followups = follow_up_id.followup_id.followup_line
            _logger.info(f'>>>>>>>>>>> check_last_reset_date 2, {follow_up_id}, {follow_up_id.followup_id}, {sibling_followups}')
            _logger.info('>>>>>>>>>>>')
            for f in sibling_followups:
                _logger.info(f)
            _logger.info(f'>>>>>>>>>>> clrd 3, {partner.followup_histry_ids}, {partner.followup_histry_ids.mapped("last_followup_level_id")}')
            if partner.last_followup_level_id == sibling_followups[-1]:
                # do not send anymore emails, if last sent already
                return False

            followups_sent = partner.followup_histry_ids.filtered(lambda h: h.last_followup_level_id == sibling_followups[0]
                                                                  and h.earliyest_duedate
                                                                  and h.earliyest_duedate == partner.payment_earliest_due_date)
            if not followups_sent:
                # SOLVE ISSUE: no line for 1st followup for same due date to check when sending followup other than 1st
                partner.reset_payment_followup_level()
                return False

            first_fup_sent_date = followups_sent[0].date
            date_to_send = first_fup_sent_date.date() + relativedelta(days=delay)
            if today >= date_to_send:
                return True
            return False

        if not partner.last_followup_level_id and not partner.last_sent_date:
            if today >= partner.payment_earliest_due_date + relativedelta(days=delay):
                # send the email to 1st time for the earliest due
                return True

        return False
