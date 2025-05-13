from datetime import timedelta
from datetime import datetime, date
from odoo import api, fields, models
import datetime
from dateutil.relativedelta import *
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError
import calendar
import math


class customer_statement(models.TransientModel):
    _name = "customer.statement"

    @api.model
    def default_get(self, fields):
        res = super(customer_statement, self).default_get(fields)
        part_ids = self._context.get('active_ids')
        if part_ids:
            res['partner_ids'] = [(6, 0, part_ids)]
        return res

    @api.multi
    def _get_default_start_date(self):
        # print('>>>>>>>>>>>>>> _get_default_start_date before')
        # invoice_start_date = datetime.date.today().replace(day=1)
        invoice_start_date = False
        soa_invoice_date_type = self.env.user.company_id.soa_invoice_date_type
        if soa_invoice_date_type == 'last_6_mth':
            start_date = datetime.date.today() + timedelta(days=-180)
            invoice_start_date = start_date.replace(day=1)
        elif soa_invoice_date_type == 'last_12_mth':
            start_date = datetime.date.today() + timedelta(days=-365)
            invoice_start_date = start_date.replace(day=1)
        elif soa_invoice_date_type == 'beginning':
            part_ids = self._context.get('active_ids')
            partner_ids = self.env['res.partner'].sudo().browse(part_ids)
            mv_line_domain = [('partner_id', '=', partner_ids[0].id), ('account_id.user_type_id.type', 'in', ['receivable', 'payable']), ('move_id.state', '<>', 'draft')]
            move_lines = self.env['account.move.line'].sudo().search(mv_line_domain, order="date asc")
            if move_lines:
                for line in move_lines:
                    invoices = self.env['account.invoice'].sudo().search([('move_id', '=', line.move_id.id)])
                    if invoices:
                        invoice_start_date = invoices[0].date_invoice.replace(day=1)
                        break
        elif soa_invoice_date_type == 'last_mth':
            invoice_start_date = str(datetime.date.today() + relativedelta(months=-1, day=1))[:10]
        else:  # current month
            invoice_start_date = str(datetime.date.today() + relativedelta(day=1))[:10]

        return invoice_start_date

    @api.multi
    def _get_default_end_date(self):

        soa_invoice_date_type = self.env.user.company_id.soa_invoice_date_type
        # invoice_end_date = datetime.datetime(datetime.date.today().year, datetime.date.today().month,
        #                             calendar.mdays[datetime.date.today().month])
        current_day = datetime.date.today()
        invoice_end_date = current_day.replace(day=calendar.monthrange(current_day.year, current_day.month)[1])
        if soa_invoice_date_type == 'last_mth':
            last_month_day = datetime.date.today() + relativedelta(months=-1)
            invoice_end_date = last_month_day.replace(day=calendar.monthrange(last_month_day.year, last_month_day.month)[1])
            # invoice_end_date = str(datetime.date.today() + relativedelta(months=-1, day=1))[:10]
        # else:#current month
        #    invoice_end_date = str(datetime.date.today() + relativedelta(months=+1, day=1, days=-1))[:10]
        return invoice_end_date

    @api.multi
    def _get_partner(self):
        act_ids = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].sudo().browse(act_ids)
        # print('>>>>>> current partner ID=', partner_ids[0])
        return partner_ids and partner_ids[0] or False

    customer = fields.Many2one(
        'res.partner', string='Customer', track_visibility='onchange', default=_get_partner)
    # Dennis - 17/3/2022 12.3.1.8 - added for attention
    attention = fields.Many2many('res.partner', string='Attention')
    soa_type = fields.Selection([('all', 'All'), ('unpaid_invoices', 'Open Invoices Only')], string='SOA Type', default=lambda self: self.env.user.company_id.soa_type, required="1")
    invoice_start_date = fields.Date(string='Invoice Start Date', default=_get_default_start_date)
    invoice_end_date = fields.Date(string='Invoice End Date', default=_get_default_end_date)
    # month = fields.Selection([('1','JAN'),('2','FEB'),('3','MAR'),('4','APR'),('5','MAY'),('6','JUN'),('7','JUL'),('8','AUG'),('9','SEP'),('10','OCT'),('11','NOV'),('12','DEC')], string='End Month (Current Year)')
    aging_by = fields.Selection([('inv_date', 'Invoice Date'), ('due_date', 'Due Date')], string='Ageing By', default='inv_date', required="1")
    aging_group = fields.Selection([('by_month', 'By Month'), ('by_days', 'By Days')], string='Ageing Group', default=lambda self: self.env.user.company_id.aging_group, required="1")
    date_upto = fields.Date('Upto Date', required="1", default=datetime.date.today())
    account_type = fields.Selection([('ar', 'Receivable'), ('ap', 'Payable'), ('both', 'Both')], string='Account Type', default='ar', required="1")
    partner_ids = fields.Many2many('res.partner', string="Partners")
    show_payment_term = fields.Boolean(default=lambda self: self.env.user.company_id.show_payment_term, readonly=False, string='Show Payment Term')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    #kashif 7nov 23: added new field to show partner ref
    print_partner_ref = fields.Boolean(default=False,string="Print partner ref")

    # @api.multi
    # def _get_default_start_date(self):
    #     for rec in self:
    #         part_ids = self._context.get('active_ids')
    #         partner_ids = self.env['res.partner'].sudo().browse(part_ids)
    #         move_lines = self.env['account.move.line'].sudo().search([('partner_id', '=', partner_ids[0].id),
    #                                                                   ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
    #                                                                   ('move_id.state', '<>', 'draft')], order="date asc")
    #         if move_lines:
    #             for line in move_lines:
    #                 invoices = self.env['account.invoice'].sudo().search([
    #                     ('move_id', '=', line.move_id.id), ])
    #                 if invoices:
    #                     rec.invoice_start_date = invoices[0].date_invoice.replace(day=1)
    #                     break

    def _get_last_day_of_month(self):
        for operation in self:
            end_date = datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                                         calendar.mdays[datetime.date.today().month])
            self.invoice_end_date = end_date

    @api.multi
    def print_statement(self):
        #print('>>>>>>>>>>>> print_statement 1 >>>>>>>>>>>>')
        part_ids = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].sudo().browse(part_ids)
        #print('>>>>>>>>>>>>>>>>> partner_ids=', partner_ids)
        if partner_ids:
            for partner in partner_ids:
                my_list = []
                attention_name = ''
                for attn in self.attention:
                    if attn.name != partner.name:
                        my_list.append(attn.name)
                        #print('>>>>>>>>>>>> print_statement 1 >>>>>>>>>>>>attn=', attn.name)
                #attention_name = ', '.join((my_list))
                partner.sudo().write({'show_payment_term': self.show_payment_term, 'overdue_date': self.invoice_end_date, 'aging_by': self.aging_by, 'aging_group': self.aging_group,
                                          'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type, 'soa_type': self.soa_type, 'attention': attention_name})
            datas = {
                'form': partner_ids.ids,
                'model': self._name,
                'partner_ids': partner_ids.ids,
                'ids': self.ids,
                'print_partner_ref':self.print_partner_ref
            }
            self.env.context = dict(self.env.context)
            if 'active_domain' in self._context:
                self.env.context.update({"active_domain": []})
            #print('>>>>>>>>>>>> print_statement 2 >>>>>>>>>>>>')
            # kashif 10nov12: check weather report holds data or not
        report_model = self.env['report.goexcel_customer_statement.cust_statement_template']
        if self.soa_type == 'all' and report_model.get_lines(partner_ids, check_first_line=True):
            return self.env.ref('goexcel_customer_statement.report_customer_statement').report_action(self, data=datas)
        elif self.soa_type == 'unpaid_invoices' and report_model.get_lines_open(partner_ids, check_first_line=True):
            return self.env.ref('goexcel_customer_statement.report_customer_statement').report_action(self, data=datas)
        else:
            raise ValidationError("Nothing to print")

    @api.multi
    def download_xlsx(self):
        # print('>>>>>>>>>>>> print_statement 1 >>>>>>>>>>>>')
        part_ids = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].sudo().browse(part_ids)
        # print('>>>>>>>>>>>>>>>>> partner_ids=', partner_ids)
        if partner_ids:
            for partner in partner_ids:
                my_list = []
                attention_name = ''
                for attn in self.attention:
                    if attn.name != partner.name:
                        my_list.append(attn.name)
                        # print('>>>>>>>>>>>> print_statement 1 >>>>>>>>>>>>attn=', attn.name)
                # attention_name = ', '.join((my_list))
                partner.sudo().write(
                    {'show_payment_term': self.show_payment_term, 'overdue_date': self.invoice_end_date,
                     'aging_by': self.aging_by, 'aging_group': self.aging_group,
                     'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type,
                     'soa_type': self.soa_type, 'attention': attention_name})
            datas = {
                'form': partner_ids.ids,
                'model': self._name,
                'partner_ids': partner_ids.ids,
                'ids': partner_ids.ids,
            }
            self.env.context = dict(self.env.context)
            if 'active_domain' in self._context:
                self.env.context.update({"active_domain": []})
            # print('>>>>>>>>>>>> print_statement 2 >>>>>>>>>>>>')
        # kashif 10nov12: check weather report holds data or not
        report_model = self.env['report.goexcel_customer_statement.cust_statement_template']
        if self.soa_type == 'all' and report_model.get_lines(partner_ids, check_first_line=True):
            return self.env.ref('goexcel_customer_statement.report_customer_statement_xlsx').report_action(self)
        elif self.soa_type == 'unpaid_invoices' and report_model.get_lines_open(partner_ids, check_first_line=True):
            return self.env.ref('goexcel_customer_statement.report_customer_statement_xlsx').report_action(self)
        else:
            raise ValidationError("Nothing to print")

        #
        # if self.get_lines_open(partner_ids):
        #     return self.env.ref('goexcel_customer_statement.report_customer_statement_xlsx').report_action(self)
        # else:
        #     raise ValidationError("Nothing to print")

    @api.multi
    def send_statement(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        _logger.warning('send email')
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference(
                    'goexcel_customer_statement', 'email_template_edi_customer_statement')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        # _logger.warning("active_ids=" + str(self._context.get('active_ids')))
        partner_ids = self.env['res.partner'].sudo().browse(self._context.get('active_ids'))
        # kashif 10nov12: check weather report holds data or not
        report_model = self.env['report.goexcel_customer_statement.cust_statement_template']
        if partner_ids:
            partner_ids.sudo().write({'show_payment_term': self.show_payment_term, 'overdue_date': self.invoice_end_date, 'aging_by': self.aging_by, 'aging_group': self.aging_group,
                                      'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type, 'soa_type': self.soa_type})
        if self.soa_type == 'all' and not report_model.get_lines(partner_ids, check_first_line=True):
            raise ValidationError("Nothing to send")
        elif self.soa_type == 'unpaid_invoices' and not report_model.get_lines_open(partner_ids, check_first_line=True):
            raise ValidationError("Nothing to send")

        # _logger.warning("partner_ids=" + str(partner_ids))
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': partner_ids[0].id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
