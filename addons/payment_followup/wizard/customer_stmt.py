from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import base64


class customer_statement(models.TransientModel):
    _inherit = "customer.statement"

    @api.depends('invoice_include_type')
    def get_invoice_include_type(self):
        for res in self:
            res.send_invoice = False
            res.send_open_invoice = False
            if self.invoice_include_type == 'open':
                res.send_invoice = False
                res.send_open_invoice = True
            if self.invoice_include_type == 'overdue':
                res.send_invoice = True
                res.send_open_invoice = False

    send_invoice = fields.Boolean(string="Include Overdue Invoice?", compute="get_invoice_include_type")
    send_open_invoice = fields.Boolean(string="Include Open Invoice?", compute="get_invoice_include_type")

    invoice_include_type = fields.Selection([('open', 'Open'), ('overdue', 'Overdue')], string="Include Invoice?", default=lambda self: self.env.user.company_id.invoice_include_type)
    # TS - bug
    inv_over_due_date = fields.Date(string="Invoices Overdue Before", default=datetime.now().date())

    @api.onchange('invoice_include_type')
    def onchange_invoice_include_type(self):
        self.send_invoice = False
        self.send_open_invoice = False
        if self.invoice_include_type == 'open':
            self.send_invoice = False
            self.send_open_invoice = True
        if self.invoice_include_type == 'overdue':
            self.send_invoice = True
            self.send_open_invoice = False

    def get_over_due_invoice(self):
        if self.send_invoice:
            return self.env['account.invoice'].search([('date_due', '<=', self.inv_over_due_date), ('state', '=', 'open'), ('type', '=', 'out_invoice')])

    @api.multi
    def send_statement(self):
        '''
        override from goexcel_customer_statement
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('goexcel_customer_statement', 'email_template_edi_customer_statement')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        # partners = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].browse(self._context.get('active_ids'))
        template = self.env['mail.template'].browse(template_id)
        if template.attachment_ids:
            for res in template.attachment_ids:
                res.unlink()
        ctx = {
                'default_model': 'res.partner',
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'make_followup_histry': True,
                'custom_layout': "mail.mail_notification_light",
                'force_email': True
            }
        # print("partner_ids", partner_ids)
        # partner_data = {'last_sent_date': datetime.date.today(), 'last_sent_by': self.env.uid}

        if len(partner_ids) > 1:
            # print("partner_ids=", len(partner_ids))
            for rec in partner_ids:
                history_data = {
                    "partner_id": rec.id,
                    "date": datetime.now(),
                    "sent_by": self.env.uid,
                    "overdue_amount": rec.payment_amount_overdue,
                    "due_amount": rec.payment_amount_due,
                    "earliyest_duedate": rec.payment_earliest_due_date,
                    "action_type": "manual"
                    }
                template.write({'email_to': rec.followup_emails})
                if self.send_invoice:
                    if not self.env.user.company_id.payment_followup_report_id:
                        raise ValidationError(_("Please Configure Report Template for Overdue Invoice"))
                    history_data.update({'inc_over_due_inv': True, 'send_type': 'soa_overdue'})
                    # invoices = self.get_over_due_invoice()
                    overdue_invoices = self.env['account.invoice'].search([('date_due', '<=', self.inv_over_due_date), ('state', '=', 'open'), ('type', '=', 'out_invoice'), ('partner_id', '=', rec.id)])

                    # overdue_invoices = invoices.filtered(lambda x: x.partner_id.id == rec.id)
                    # for inv in overdue_invoices:
                    data_id = False
                    if len(overdue_invoices) > 0:
                        report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(overdue_invoices.ids)
                        data_record = base64.b64encode(report_template_id[0])
                        ir_values = {
                           'name': "Overdue Invoices.pdf",
                           'type': 'binary',
                           'datas': data_record,
                           'datas_fname': "Overdue Invoices.pdf",
                           'store_fname': 'Overdue Invoices',
                           'mimetype': 'application/pdf',
                        }
                        data_id = self.env['ir.attachment'].create(ir_values)
                        template.attachment_ids = [(4, data_id.id)]
                    ctx['default_res_id'] = rec.id
                    template.with_context(ctx).send_mail(rec.id, force_send=True)
                    template.attachment_ids = False
                    if data_id:
                        data_id.unlink()
                    rec.last_send_type = 'soa_overdue'
                if self.send_open_invoice:
                    if not self.env.user.company_id.payment_followup_report_id:
                        raise ValidationError(_("Please Configure Report Template for Open Invoice"))
                    history_data.update({'inc_open_inv': True, 'send_type': 'soa_open'})
                    open_invoices = self.env['account.invoice'].search([('state', '=', 'open'), ('type', '=', 'out_invoice'), ('partner_id', '=', rec.id)])
                    data_id = False
                    if len(open_invoices) > 0:
                        report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(open_invoices.ids)
                        data_record = base64.b64encode(report_template_id[0])
                        ir_values = {
                           'name': "open Invoices.pdf",
                           'type': 'binary',
                           'datas': data_record,
                           'datas_fname': "open Invoices.pdf",
                           'store_fname': 'open Invoices',
                           'mimetype': 'application/pdf',
                        }
                        data_id = self.env['ir.attachment'].create(ir_values)
                        template.attachment_ids = [(4, data_id.id)]
                    ctx['default_res_id'] = rec.id
                    template.with_context(ctx).send_mail(rec.id, force_send=True)
                    template.attachment_ids = False
                    if data_id:
                        data_id.unlink()
                    rec.last_send_type = 'soa_overdue'
                else:
                    ctx['default_res_id'] = rec.id
                    template.with_context(ctx).send_mail(rec.id, force_send=True)

                rec.last_sent_date = datetime.now()
                rec.last_sent_by = self.env.uid
                rec.last_action_type = 'manual'
                if not rec.last_send_type:
                    rec.last_send_type = 'soa'
                # rec.write(partner_data)
                self.env['partner.payment.followup'].create(history_data)

        else:
            partner_ids.write({'overdue_date': self.invoice_end_date, 'aging_by': self.aging_by, 'aging_group': self.aging_group,
                               'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type, 'soa_type': self.soa_type})
            ctx['default_res_id'] = partner_ids[0].id
            if partner_ids[0].followup_emails:
                ctx['default_partner_ids'] = []
                partner_email_list = partner_ids[0].followup_emails.split(',')
                email_partner_ids = []
                for i in partner_email_list:
                    partner_to = self.env['res.partner'].search([('email', '=', i)], limit=1)
                    email_partner_ids.append(partner_to.id)
                ctx['default_partner_ids'] = email_partner_ids
            history_data = {
                "partner_id": partner_ids[0].id,
                "date": datetime.now(),
                "sent_by": self.env.uid,
                "overdue_amount": partner_ids[0].payment_amount_overdue,
                "due_amount": partner_ids[0].payment_amount_due,
                "earliyest_duedate": partner_ids[0].payment_earliest_due_date,
                "action_type": "manual"
            }
            if self.send_invoice:
                invoices = self.get_over_due_invoice()
                history_data.update({'inc_over_due_inv': True, 'send_type': 'soa_overdue'})
                overdue_invoices = invoices.filtered(lambda x: x.partner_id.id == partner_ids[0].id)
                if not self.env.user.company_id.payment_followup_report_id:
                    raise ValidationError(_("Please Configure Report Template for Overdue Invoice"))
                # for inv in overdue_invoices:
                if len(overdue_invoices) > 0:
                    report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(overdue_invoices.ids)
                    data_record = base64.b64encode(report_template_id[0])
                    ir_values = {
                       'name': "Overdue Invoices.pdf",
                       'type': 'binary',
                       'datas': data_record,
                       'datas_fname': "Overdue Invoices.pdf",
                       'store_fname': 'Overdue Invoices',
                       'mimetype': 'application/pdf',
                    }
                    data_id = self.env['ir.attachment'].create(ir_values)
                    template.attachment_ids = [(4, data_id.id)]
                    partner_ids[0].last_send_type = 'soa_overdue'
            if self.send_open_invoice:
                if not self.env.user.company_id.payment_followup_report_id:
                    raise ValidationError(_("Please Configure Report Template for Open Invoice"))
                history_data.update({'inc_open_inv': True, 'send_type': 'soa_open'})
                open_invoice_ids = self.env['account.invoice'].search([('date_due', '<=', self.inv_over_due_date), ('state', '=', 'open'), ('type', '=', 'out_invoice'), ('partner_id', '=', partner_ids[0].id)])
                # for inv in overdue_invoices:
                if len(open_invoice_ids) > 0:
                    report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(open_invoice_ids.ids)
                    data_record = base64.b64encode(report_template_id[0])
                    ir_values = {
                       'name': "Open Invoices.pdf",
                       'type': 'binary',
                       'datas': data_record,
                       'datas_fname': "Open Invoices.pdf",
                       'store_fname': 'Open Invoices',
                       'mimetype': 'application/pdf',
                    }
                    data_id = self.env['ir.attachment'].create(ir_values)
                    template.attachment_ids = [(4, data_id.id)]
                    partner_ids[0].last_send_type = 'soa_open'
            # self.env['partner.payment.followup'].create(history_data)
            ctx['history_data'] = history_data
            partner_ids[0].last_sent_date = datetime.now()
            partner_ids[0].last_sent_by = self.env.uid
            partner_ids[0].last_action_type = 'manual'
            if not partner_ids[0].last_send_type:
                partner_ids[0].last_send_type = 'soa'
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

    @api.multi
    def print_overdue_invoices(self):
        partners = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].browse(partners)
        if not self.env.user.company_id.payment_followup_report_id:
            raise ValidationError(_("Please Configure Report Template for Overdue Invoice"))
        if partner_ids:
            domain = [('date_due', '<=', self.inv_over_due_date), ('state', '=', 'open'), ('partner_id', 'in', partner_ids.ids), ('type', '=', 'out_invoice')]
            pdf_reports = self.env['account.invoice'].search(domain)
            return self.env.user.company_id.payment_followup_report_id.with_context(discard_logo_check=True).report_action(pdf_reports)
        return

    @api.multi
    def print_open_invoices(self):
        partners = self._context.get('active_ids')
        partner_ids = self.env['res.partner'].browse(partners)
        if not self.env.user.company_id.payment_followup_report_id:
            raise ValidationError(_("Please Configure Report Template for Open Invoice"))
        if partner_ids:
            domain = [('state', '=', 'open'), ('partner_id', 'in', partner_ids.ids), ('type', '=', 'out_invoice')]
            pdf_reports = self.env['account.invoice'].search(domain)
            return self.env.user.company_id.payment_followup_report_id.with_context(discard_logo_check=True).report_action(pdf_reports)
        return
