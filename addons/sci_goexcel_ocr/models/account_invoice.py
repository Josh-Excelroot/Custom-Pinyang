##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from collections import OrderedDict
import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils, float_round
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
import tempfile
import base64
import os
import dateutil.parser as dparser
from datetime import datetime

import os
import shutil

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        if self._context.get('currency_id'):
            return self.env['res.currency'].browse(
                self._context.get('currency_id'))
        return journal.currency_id or journal.company_id.currency_id or \
            self.env.user.company_id.currency_id

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            if self._context.get('currency_id'):
                self.currency_id = self._context.get('currency_id')
            else:
                self.currency_id = self.journal_id.currency_id.id or \
                               self.journal_id.company_id.currency_id.id

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=_default_currency,
                                  track_visibility='always')

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        # Split `From` and `CC` email address from received email to look for related partners to subscribe on the invoice
        subscribed_emails = email_split((msg_dict.get('from') or '') + ',' + (msg_dict.get('cc') or ''))
        seen_partner_ids = [pid for pid in self._find_partner_from_emails(subscribed_emails) if pid]

        # Detection of the partner_id of the invoice:
        # 1) check if the email_from correspond to a supplier
        email_from = msg_dict.get('from') or ''
        email_from = email_escape_char(email_split(email_from)[0])
        partner_id = self._search_on_partner(email_from, extra_domain=[('supplier', '=', True)])

        is_internal = lambda p: (p.user_ids and
                                 all(p.user_ids.mapped(lambda u: u.has_group('base.group_user'))))
        # 2) otherwise, if the email sender is from odoo internal users then it is likely that the vendor sent the bill
        # by mail to the internal user who, inturn, forwarded that email to the alias to automatically generate the bill
        # on behalf of the vendor.
        if not partner_id:
            user_partner_id = self._search_on_user(email_from)
            if user_partner_id and user_partner_id in self.env.ref('base.group_user').users.mapped('partner_id').ids:
                # In this case, we will look for the vendor's email address in email's body
                email_addresses = set(email_re.findall(msg_dict.get('body')))
                if email_addresses:
                    pids_list = [self._find_partner_from_emails([email], force_create=False) for email in
                                 email_addresses]
                    partner_ids = set(pid for pids in pids_list for pid in pids if pid)
                    potential_vendors = self.env['res.partner'].browse(partner_ids).filtered(
                        lambda x: not is_internal(x))
                    partner_id = ((potential_vendors.filtered('supplier') and potential_vendors.filtered('supplier')[
                        0].id)
                                  or (potential_vendors and potential_vendors[0].id))
            # otherwise, there's no fallback on the partner_id found for the regular author of the mail.message as we want
            # the partner_id to stay empty

        # If the partner_id can be found, subscribe it to the bill, otherwise it's left empty to be manually filled
        if partner_id:
            seen_partner_ids.append(partner_id)

        # Find the right purchase journal based on the "TO" email address
        destination_emails = email_split((msg_dict.get('to') or '') + ',' + (msg_dict.get('cc') or ''))
        alias_names = [mail_to.split('@')[0] for mail_to in destination_emails]
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'), ('alias_name', 'in', alias_names)
        ], limit=1)

        # Create the message and the bill.
        values = dict(custom_values or {}, partner_id=partner_id, source_email=email_from)

        branch = False
        if email_from:
            user = self.env['res.users'].search([
                ('login', '=', email_from),
            ])
            if user and user.default_branch:
                branch = user.default_branch.id
        if journal:
            values['journal_id'] = journal.id
        # Passing `type` in context so that _default_journal(...) can correctly set journal for new vendor bill
        invoice = super(AccountInvoice, self.with_context(type=values.get('type'))).message_new(msg_dict, values)
        invoice.write({'branch': branch,})
        # Subscribe internal users on the newly created bill
        partners = self.env['res.partner'].browse(seen_partner_ids)
        partners_to_subscribe = partners.filtered(is_internal)
        if partners_to_subscribe:
            invoice.message_subscribe([p.id for p in partners_to_subscribe])

        attachments = msg_dict.get('attachments')
        if attachments:
            has_attachment = True
        else:
            has_attachment = False
        message_monitor = self.env['message.monitor'].create({
            'type': 'account.invoice',
            'object_id': invoice.id,
            'has_attachment': has_attachment,
        })

        print(message_monitor)

        return invoice

    @api.model
    def _delete_ocr_temp_data(self):
        folder_path = self.env['ir.config_parameter'].sudo().get_param('ocr_temp_files_dir')
        if not folder_path:
            _logger.error('No value or parameter for ocr_temp_files_dir specified')
        if not os.path.exists(folder_path):
            _logger.error(f'Path "{folder_path}" to remove OCR temporary files does not exist')
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        strings_to_delete = ['tempimagenew', 'image2txt', 'temptext']
        for subfolder in subfolders:
            if any(string in subfolder for string in strings_to_delete):
                subfolder_path = os.path.join(folder_path, subfolder)
                shutil.rmtree(subfolder_path)
