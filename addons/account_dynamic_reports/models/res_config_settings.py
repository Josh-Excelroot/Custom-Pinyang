from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    load_last_dynamic_reports_record = fields.Boolean(related="company_id.load_last_dynamic_reports_record", readonly=False)
    partner_ageing_exch_entries = fields.Boolean(related="company_id.partner_ageing_exch_entries", readonly=False)
    partner_ageing_exclude_accounts = fields.Many2many('account.account', related="company_id.partner_ageing_exclude_accounts", readonly=False)
    general_ledger_exch_entries = fields.Boolean(related="company_id.general_ledger_exch_entries", readonly=False)
    unposted_entries_dynamic_reports = fields.Boolean(related="company_id.unposted_entries_dynamic_reports", readonly=False)

    unrealized_forex_gain_account_id = fields.Many2one('account.account', related="company_id.unrealized_forex_gain_account_id", readonly=False)
    unrealized_forex_loss_account_id = fields.Many2one('account.account', related="company_id.unrealized_forex_loss_account_id", readonly=False)