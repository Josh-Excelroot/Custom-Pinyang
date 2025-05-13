from odoo import fields, models, _


class TransactionAccountLine(models.Model):
    _name = "transaction.account.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Transaction Account Line"

    account_id = fields.Many2one('account.account', string='Account', track_visibility='always')
    credit = fields.Integer(string='Credit', track_visibility='always')
    debit = fields.Integer(string='Debit', track_visibility='always')
    remark = fields.Char(string="Remark", track_visibility='always')
    acc_id = fields.Many2one('transaction.template')

    def write(self, vals):
        for rec in self:
            old_account_id = rec.account_id.name
            old_credit = rec.credit
            old_debit = rec.debit
            old_remark = rec.remark
            res = super(TransactionAccountLine, rec).write(vals)
            msg = ""
            if 'account_id' in vals:
                msg += "<br/>Account : %s changed to %s" % (old_account_id, rec.account_id.name)
            if 'credit' in vals:
                msg += "<br/>Credit : %s Changed to %s" % (old_credit, rec.credit)
            if 'debit' in vals:
                msg += "<br/>Debit : %s Changed to %s" % (old_debit, rec.debit)
            if 'remark' in vals:
                msg += "<br/>Remark : %s Changed to %s" % (old_remark, rec.remark)
            if len(msg) > 0:
                rec.acc_id.message_post(body=_(
                    'You Update order with <a href=# data-oe-model=transaction.template data-oe-id=%d>%s</a>') % (rec.id, msg))
            return res
