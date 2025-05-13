from odoo import fields, models, api, tools
from lxml import etree

from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move','mail.thread', 'mail.activity.mixin']

    invoice_type = fields.Char(compute='_compute_invoice')

    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True,
                                 readonly=True,track_visibility='always')

    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status',
                             required=True, readonly=True, copy=False, default='draft',
                             help='All manually created new journal entries are usually in the status \'Unposted\', '
                                  'but you can set the option to skip that status on the related journal. '
                                  'In that case, they will behave as journal entries automatically created by the '
                                  'system on document validation (invoices, bank statements...) and will be created '
                                  'in \'Posted\' status.',track_visibility='onchange')

    ref = fields.Char(string='Reference', copy=False,track_visibility='always')
    @api.multi
    def _get_default_journal(self):
        if self.env.context.get('default_journal_type'):
            return self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id), ('type', '=', self.env.context['default_journal_type'])], limit=1).id

    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 states={'posted': [('readonly', True)]}, default=_get_default_journal,track_visibility='always')

    date = fields.Date(required=True, states={'posted': [('readonly', True)]}, index=True,
                       default=fields.Date.context_today,track_visibility='always')

    line_ids = fields.One2many('account.move.line', 'move_id', string='Journalsss Items',
                               states={'posted': [('readonly', True)]}, copy=True,track_visibility='always')
    payment_id = fields.Many2one('account.payment', compute='_compute_payment')
    invoice_id = fields.Many2one('account.invoice', compute='_compute_invoice')
    attachment_ids = fields.Many2many('ir.attachment',
                                      compute='_compute_attachments')

    @api.multi
    def _get_default_journal(self):
        if self.env.context.get('default_journal_type'):
            return self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id),
                                                       ('type', '=', self.env.context['default_journal_type'])],
                                                      limit=1).id

    def _compute_invoice(self):
        for rec in self:
            invoice = rec.line_ids.mapped('invoice_id')
            if invoice:
                rec.invoice_id = invoice.id
                rec.invoice_type = invoice.get_invoice_type()
            else:
                rec.invoice_id = False
                rec.invoice_type = False

    def _compute_payment(self):
        for rec in self:
            payment = rec.line_ids.mapped('payment_id')
            if payment:
                if len(payment)>1:
                    rec.payment_id = payment[0].id
                else:
                    rec.payment_id = payment.id
            else:
                rec.payment_id=False


# Ahmad Zaman - 6/5/24 - Changed the logic to fix singleton error
    def _compute_attachments(self):
        for rec in self:
            attachment_ids = False
            if rec.invoice_id:
                attachment_ids = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'account.invoice'),
                    ('res_id', '=', rec.invoice_id.id)
                ])
            elif rec.payment_id:
                attachment_ids = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'account.payment'),
                    ('res_id', '=', rec.payment_id.id)
                ])
            rec.attachment_ids = attachment_ids and attachment_ids.ids


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # @api.model
    # def create(self, vals):
    #     # _logger.warning("in create")
    #     res = super(AccountMoveLine, self).create(vals)
    #
    #     # currency = self.env.user.company_id.currency_id.id
    #     content = ""
    #     if vals.get("account_id"):
    #         acc = self.env['account.account'].search([('id','=',vals.get("account_id"))])
    #         content = content + "  \u2022 Account: " + str(acc.name) + "<br/>"
    #     if vals.get("partner_id"):
    #         partner = self.env['res.partner'].search([('id','=',vals.get("partner_id"))])
    #         content = content + "  \u2022 Partner: " + str(partner.name) + "<br/>"
    #     if vals.get("name"):
    #         content = content + "  \u2022 Name: " + str(vals.get("name")) + "<br/>"
    #     if vals.get("balance"):
    #         content = content + "  \u2022 Balance: " + str(vals.get("balance")) + "<br/>"
    #     if vals.get("currency_id"):
    #         currency = self.env['res.currency'].search([('id', '=', vals.get("currency_id"))])
    #         content = content + "  \u2022 Profit Currency: " + str(currency.name) + "<br/>"
    #
    #     if vals.get("analytic_account_id"):
    #         analytic_account = self.env['account.analytic.account'].search([('id','=',vals.get("analytic_account_id"))])
    #         content = content + "  \u2022 Analytic Account: " + str(analytic_account.name) + "<br/>"
    #
    #     if vals.get("journal_currency_rate"):
    #         content = content + "  \u2022 Total Exchange Currency Rate: " + str(vals.get("journal_currency_rate")) + "<br/>"
    #
    #     if vals.get("amount_currency"):
    #         content = content + "  \u2022 Amount: " + str(vals.get("amount_currency")) + "<br/>"
    #     if vals.get("debit"):
    #         content = content + "  \u2022 Debit: " + str(vals.get("debit")) + "<br/>"
    #     if vals.get("credit"):
    #         content = content + "  \u2022 Credit: " + str(vals.get("credit")) + "<br/>"
    #     if vals.get("analytic_tag_ids"):
    #         lst = vals.get("analytic_tag_ids")
    #         ids = [i for i in lst[0][2]]
    #         tag = self.env['account.analytic.tag'].search([('id','in',ids)])
    #         ana_tag = [i.name for i in tag]
    #         content = content + "  \u2022 Analytic Tag: " + str(ana_tag) + "<br/>"
    #
    #
    #     res.move_id.message_post(body=content)
    #     return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        data =  {}
        for i in self:
            data = {
               "account":i.account_id if i.account_id else False,
               "partner_id":i.partner_id if i.partner_id else False,
               "name":i.name if i.name else False,
               "balance":i.balance if i.balance else False,
                "currency_id":i.currency_id if i.currency_id else False,
                "analytic_account_id":i.analytic_account_id if i.analytic_account_id else False,
                "journal_currency_rate":i.journal_currency_rate if i.journal_currency_rate else False,
                "amount_currency":i.amount_currency if i.amount_currency else 0,
                "debit":i.debit if i.debit else 0,
                "credit": i.credit if i.credit else 0,
                "analytic_tag_ids": i.analytic_tag_ids if i.analytic_tag_ids else False
            }

        res = super(AccountMoveLine, self).write(vals)
        content = ""
        if vals.get("account_id"):
            acc = self.env['account.account'].search([('id', '=', vals.get("account_id"))])
            if data['account']:
                acout =data['account'].name
            else:
                acout = False
            content = content + "  \u2022 Account: " + str(acout) + " -> " + str(acc.name) + "<br/>"
        if vals.get("partner_id"):
            partner = self.env['res.partner'].search([('id', '=', vals.get("partner_id"))])
            if data['partner_id']:
                partn_name = data['partner_id'].name
            else:
                partn_name = False
            content = content + "  \u2022 Partner: "+str(partn_name) +" -> "+ str(partner.name) + "<br/>"
        if vals.get("name"):
            content = content + "  \u2022 Name: " +str(data['name']) +" -> "+ str(vals.get("name")) + "<br/>"
        if vals.get("balance"):
            content = content + "  \u2022 Balance: " + str(data['balance']) + " -> "+str(vals.get("balance")) + "<br/>"

        if vals.get("currency_id"):
            currency = self.env['res.currency'].search([('id', '=', vals.get("currency_id"))])
            if data['currency_id']:
                amcu = data['currency_id'].name
            else:
                amcu = False
            content = content + "  \u2022  Currency: " + str(amcu) +" -> "+ str(currency.name) + "<br/>"

        if vals.get("analytic_account_id"):
            analytic_account = self.env['account.analytic.account'].search(
                [('id', '=', vals.get("analytic_account_id"))])
            if data['analytic_account_id']:
                analytic_a = data['analytic_account_id'].name
            else:
                analytic_a = False
            content = content + "  \u2022 Analytic Account: " + str(analytic_a) +" -> "+ str(analytic_account.name) + "<br/>"

        if vals.get("journal_currency_rate"):
            content = content + "  \u2022 Total Exchange Currency Rate: " + str(data['journal_currency_rate'])+" -> "+str(
                vals.get("journal_currency_rate")) + "<br/>"

        if vals.get("amount_currency"):
            if data['amount_currency']:
                amcu = data['amount_currency']
            else:
                amcu=0
            content = content + "  \u2022 Amount: " + str(amcu) +" -> "+str(vals.get("amount_currency")) + "<br/>"
        if vals.get("debit"):
            content = content + "  \u2022 Debit: "+ str(data['debit']) +" -> "+ str(vals.get("debit")) + "<br/>"
        if vals.get("credit"):
            content = content + "  \u2022 Credit: "+ str(data['credit']) +" -> " + str(vals.get("credit")) + "<br/>"
        if vals.get("analytic_tag_ids"):
            lst = vals.get("analytic_tag_ids")
            ids = [i for i in lst[0][2]]
            tag = self.env['account.analytic.tag'].search([('id', 'in', ids)])
            ana_tag = [i.name for i in tag]
            if data['analytic_tag_ids']:
                ana_tags = [i.name for i in data['analytic_tag_ids']]
            else:
                ana_tags = False
            content = content + "  \u2022 Analytic Tag: " +str(ana_tags) +" -> "+ str(ana_tag) + "<br/>"


        for i in self:
            i.move_id.message_post(body=content)
        return res
