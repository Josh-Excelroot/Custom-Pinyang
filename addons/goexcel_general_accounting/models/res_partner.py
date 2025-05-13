from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_company = fields.Boolean(string='Is a Company', default=True,
                                help="Check if the contact is a company, otherwise it is a person")
    roc = fields.Char(string='R.O.C', help="Company Registration")


    @api.model
    def _get_account_payable(self):
        account_id = self.env['account.account'].search([('default_ar_ap', '=', True),('user_type_id', '=', 2)])
        if account_id:
            return account_id.id

    @api.model
    def _get_account_receivable(self):
        account_id = self.env['account.account'].search([('default_ar_ap', '=', True),('user_type_id', '=', 1)])
        if account_id:
            return account_id.id

    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable", oldname="property_account_payable",
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                  default='_get_account_payable',
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=True)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable", oldname="property_account_receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                     default='_get_account_receivable',
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=True)