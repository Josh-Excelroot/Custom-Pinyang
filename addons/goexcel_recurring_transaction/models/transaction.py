from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date as datetime_date, timedelta, datetime


class TransactionTemplate(models.Model):
    _name = "transaction.template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Transaction Template"
    _rec_name = 'name'

    name = fields.Char("Name", track_visibility='always')
    status = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], "Status", default='new', track_visibility='always')
    interval_t = fields.Selection([
        ('days', 'Daily'),
        ('weeks', 'Weekly'),
        ('months', 'Monthly'),
        ('years', 'Yearly')], "Interval Type", track_visibility='always')
    previous_date = fields.Date('Last Recurred Date', track_visibility='always', default=fields.Date.today)
    next_date = fields.Date(string="Next Scheduled Date", track_visibility='always')
    journal_id = fields.Many2one('account.journal', string='Journal', track_visibility='always')
    credit_amount = fields.Integer(string='Credit Amount', compute='compute_credit', track_visibility='always')
    debit_amount = fields.Integer(string='Debit Amount', compute='compute_debit', track_visibility='always')
    transaction_account_ids = fields.One2many('transaction.account.line', 'acc_id', track_visibility='always')
    journal_count = fields.Integer(compute="compute_journal_count", string="Journal Count")
    account_move_ids = fields.One2many('account.move', 'transaction_act_id')
    remark = fields.Char(string="Remark", track_visibility='always')
    journal_post = fields.Boolean(string='Post Journal Entry')
    selection_type = fields.Selection([
        ('number_of_days', 'Number Of Days'),
        ('end_date', 'End Date')], string="Type", track_visibility='always')
    interval = fields.Integer(string='Number of Entries', track_visibility='always')
    end_date = fields.Date('End Date', track_visibility='always')
    acc_move_id = fields.Many2one('account.move', string='Account Entry')

    @api.onchange('acc_move_id')
    def get_datas_acc(self):
        for rec in self:
            if rec.acc_move_id:
                rec.transaction_account_ids = False
                credit = 0
                debit = 0
                for res in rec.acc_move_id.line_ids:
                    credit = credit + res.credit
                    debit = debit + res.debit
                rec.journal_id = rec.acc_move_id.journal_id
                rec.credit_amount = credit
                rec.debit_amount = debit
                line_data = [(0, 0, {
                    'account_id': line.account_id,
                    'credit': line.credit,
                    'debit': line.debit,
                    }) for line in rec.acc_move_id.line_ids]
                # self.transaction_account_ids = line_data
                rec.transaction_account_ids = line_data

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('transaction.template')
        return super(TransactionTemplate, self).create(vals)

    @api.onchange('transaction_account_ids')
    def compute_credit(self):
        for res in self:
            credit = 0
            for rec in res.transaction_account_ids:
                credit = credit + rec.credit
            res.credit_amount = credit

    @api.onchange('transaction_account_ids')
    def compute_debit(self):
        for res in self:
            debit = 0
            for rec in res.transaction_account_ids:
                debit = debit + rec.debit
            res.debit_amount = debit

    def action_reset_draft_btn(self):
        for rec in self:
            rec.previous_date = False
            rec.next_date = False
            rec.status = 'new'

    def action_comfirm_btn(self):
        for rec in self:
            if (rec.credit_amount != 0 or rec.debit_amount != 0) and rec.credit_amount == rec.debit_amount:
                rec.status = 'confirm'
            else:
                raise ValidationError(_("Credit Amount and Debit Amount not Equal."))

    def action_cancel_btn(self):
        for rec in self:
            rec.status = 'cancel'

    def action_done_btn(self):
        for rec in self:
            rec.status = 'done'

    def action_create_journal_data_btn(self):
        line_ids = []
        for line_id in self.transaction_account_ids:
            line_ids.append({'account_id': line_id.account_id.id, 'credit': line_id.credit, 'debit': line_id.debit})
        for rec in self:
            if rec.credit_amount == rec.debit_amount:
                request_line_data = {
                    'date': datetime.today(),
                    'transaction_act_id': self.id,
                    'ref': rec.name,
                    'journal_id': rec.journal_id and rec.journal_id.id or False,
                    'line_ids': [(0, 0, vals) for vals in line_ids],
                }
                jid = self.env['account.move'].create(request_line_data)
                if rec.journal_post:
                    jid.action_post()
                rec.message_post(body=_('New Journal Record Created %s : %s') % (rec.journal_count, jid.name))
                rec.compute_journal_count()

    def action_journal_data(self):
        return {
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'context': {},
            'domain': [('transaction_act_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window', }

    @api.depends('account_move_ids')
    def compute_journal_count(self):
        for rec in self:
            rec.journal_count = self.env['account.move'].search_count([('transaction_act_id', '=', rec.id)])
            if rec.selection_type == "number_of_days":
                if rec.interval == rec.journal_count and rec.journal_count > 0:
                    rec.action_done_btn()
            elif rec.selection_type == "end_date":
                final_end_date = rec.end_date + timedelta(days=1)
                if final_end_date == datetime_date.today():
                    rec.action_done_btn()
