# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import fields, models, api
from odoo.tools import formataddr


class IrMailServer(models.Model):

    _inherit = "ir.mail_server"

    company_id = fields.Many2one("res.company", "Company")


class FetchMailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one("res.company", "Company")

    @api.model
    def _fetch_mails(self):
        """ Method called by cron to fetch mails from servers """
        for res in self.env['res.company'].search([]):
            self.search([('state', '=', 'done'), ('type', 'in', ['pop', 'imap']), ('company_id', '=', res.id)]).fetch_mail()
        return True


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def create(self, values):
        values['email_from'] = formataddr((self.env.user.company_id.name, self.env.user.company_id.email))
        return super(MailComposer, self).create(values)
