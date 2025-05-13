# -*- coding: utf-8 -*-

from functools import reduce
from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from datetime import datetime, timezone


class Followup(models.Model):
    _name = 'payment.followup'
    _description = 'Account Follow-up'
    _rec_name = 'name'

    name = fields.Char(string="Name", copy=False, index=True, required=True)
    followup_line = fields.One2many('payment.followup.line', 'followup_id', 'Follow-up', copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env['res.company']._company_default_get('payment.followup'))
    time = fields.Float(string="Scheduled Time")

    # report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model', '=', 'account.invoice')]")

    _sql_constraints = [('company_uniq', 'unique(company_id)', 'Only one follow-up per company is allowed')]

    @api.constrains('time')
    def check_time_data(self):
        for res in self:
            if res.time and res.time < 0 or res.time > 24:
                raise ValidationError(_("Please enter proper time in 24HR format Ex.00:00 to 23:59"))

    @api.model
    def create(self, vals):
        res = super(Followup, self).create(vals)
        if res.time:
            self.change_chrone_job_time(res.time)
        return res

    @api.multi
    def write(self, values):
        res = super(Followup, self).write(values)
        if 'time' in values:
            self.change_chrone_job_time(values['time'])
        return res

    def change_chrone_job_time(self, time):
        crone_id = self.env.ref('payment_followup.ir_cron_overdue_invoice')
        next_date = crone_id.nextcall.date()
        next_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(time * 60, 60))
        next_time = datetime.strptime(next_time, '%H:%M')
        combined = datetime.combine(next_date, next_time.time())
        combined.replace(tzinfo=timezone.utc)
        crone_id.nextcall = combined
        crone_id.nextcall.astimezone(timezone.utc)


class FollowupLine(models.Model):
    _name = 'payment.followup.line'
    _description = 'Follow-up Criteria'
    _order = 'delay'

    @api.model
    def _get_default_template(self):
        try:
            return self.env['ir.model.data'].get_object_reference('payment_followup', 'email_template_soa_overdue_customer_statement')[1]
        except ValueError:
            return False

    name = fields.Char('Follow-Up Action', required=True)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of follow-up lines.")
    delay = fields.Integer('Due Days', help="The number of days after the due date of the invoice to wait before sending the reminder. Could be negative if you want to send a polite alert beforehand.", required=True)
    followup_id = fields.Many2one('payment.followup', 'Follow Ups', required=True, ondelete="cascade")

    action_type = fields.Selection([('manual', 'Manual'), ('automatic', ' Automatic')], string="Action Type", default='automatic', required=True)
    send_email = fields.Boolean('Send an Email', help="When processing, it will send an email")
    send_letter = fields.Boolean('Send a Letter', help="When processing, it will print a letter")
    manual_action_note = fields.Text('Action To Do', placeholder="e.g. Give a phone call, check with others , ...")
    manual_action_responsible_id = fields.Many2one('res.users', 'Assign a Responsible', ondelete='set null')
    email_template_id = fields.Many2one('mail.template', 'Email Template', ondelete='set null', default=_get_default_template, domain="[('model_id', '=', 'res.partner')]")

    send_type = fields.Selection([('soa', "SOA"), ('overdue_invoices', 'Overdue Invoices'), ('soa_overdue', 'SOA + Overdue Invoices'), ('open_invoice', 'Open Invoices'), ('soa_open', 'SOA + Open Invoices')], default='soa_overdue', string="Attach Documents")
    # send_soa = fields.Boolean('Send SOA', help="when Processing, it will Send only SOA")
    # send_overdue = fields.Boolean("Send Overdue Invoices", help="When Processign, It will send OverDue Invoice")
    # send_soa_overdue = fields.Boolean(string="SOA+Overdue Invoices", help="When Processing, It will send SOA and Overdue Invoice")
    manual_action = fields.Boolean('Manual Action', default=False, help="When processing, it will set the manual action to be taken for that customer. ")

    _sql_constraints = [('days_uniq', 'unique(followup_id, delay)', 'Days of the follow-up levels must be different')]

    @api.onchange('action_type')
    def onchange_action_type(self):
        if self.action_type == 'manual':
            self.send_type = False
        if self.action_type == 'automatic':
            self.send_letter = False
            self.send_email = False
            self.manual_action = False
