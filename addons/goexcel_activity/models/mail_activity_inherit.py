# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging
import pytz

from odoo import api, exceptions, fields, models, _

from odoo.tools import pycompat
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """ An actual activity to perform. Activities are linked to
    documents using res_id and res_model_id fields. Activities have a deadline
    that can be used in kanban view to display a status. Once done activities
    are unlinked and a message is posted. This message has a new activity_type_id
    field that indicates the activity linked to the message. """
    _inherit = 'mail.activity'

    def send_reminder_email(self):
        activity_record = self.env['mail.activity'].search([])
        ctx = {}
        if activity_record:
            for record in activity_record:
                today_date = datetime.today().date()
                # if record.user_id and record.activity_type_id and record.summary and record.date_deadline:
                #     print(record.user_id,record.activity_type_id.name, record.summary, record.date_deadline)
                if today_date <= record.date_deadline:
                    ctx['email_from'] = self.env.user.company_id.email
                    ctx['email_to'] = record.user_id.login
                    ctx['partner_name'] = record.user_id.name
                    ctx['activity_name'] = record.activity_type_id.name
                    ctx['summary'] = record.summary
                    ctx['date'] = record.date_deadline
                    ctx['lang'] = self.env.user.lang
                    ctx['company_name'] = self.env.user.company_id.name
                    print(ctx)
                    template = self.env.ref('goexcel_activity.activity_reminder_email_template_id')
                    template.with_context(ctx).sudo().send_mail(self.id, force_send=True, raise_exception=False)