   # remove method and add to next method by shivam,
    # def do_update_followup_level(self, to_update, partner_list, date):
    #     # update the follow-up level on account.move.line
    #     # golive_date = self.env.user.company_id.go_live_date
    #     bypass_date = False
    #     for id in to_update.keys():
    #         partner_id = self.env['res.partner'].browse([to_update[id]['partner_id']])
    #         bypass_date = partner_id.reset_date and partner_id.reset_date or self.company_id.go_live_date
    #         today = datetime.datetime.today().date()
    #         if bypass_date:
    #             bypass_date = today <= bypass_date
    #         print ("bypass_date", bypass_date)
    #         if to_update[id]['partner_id'] in partner_list and bypass_date and today <= bypass_date:
    #                 self.env['account.move.line'].browse([int(id)]).write({'followup_line_id': to_update[id]['level'], 'followup_date': date})

    # shivam add above method code in current method
    # def process_partners1(self, partner_ids):
    #     for partner in self.env['payment.followup.by.partner'].sudo().search([('partner_id', 'in', partner_ids)]):
    #         send_flag = self.check_last_reset_date(partner)
    #         print ("send_flag", send_flag)
    #         if partner.partner_id.followup_emails and not partner.partner_id.bypass_auto_followup:
    #             partner_id = partner.partner_id
    #             over_due_pdf = False
    #             only_soa_pdf = False
    #             histry_data = {
    #                 "partner_id": partner_id.id,
    #                 "date": datetime.datetime.now(),
    #                 "sent_by": self.env.uid,
    #                 "overdue_amount": partner_id.payment_amount_overdue,
    #                 "due_amount": partner_id.payment_amount_due,
    #                 "earliyest_duedate": partner_id.payment_earliest_due_date,
    #                 'send_type': partner.max_followup_id.send_type,
    #                 'action_type': partner.max_followup_id.action_type
    #                 }
    #             statement_duration = self.env.user.company_id.statement_duration
    #             start_date = datetime.datetime.today().date().replace(day=1)
    #             if statement_duration == '3':
    #                 start_date = start_date + relativedelta(months=-2)
    #             if statement_duration == '6':
    #                 start_date = start_date + relativedelta(months=-5)
    #             if statement_duration == '9':
    #                 start_date = start_date + relativedelta(months=-8)
    #             if statement_duration == '1':
    #                 start_date = start_date + relativedelta(months=-11)
    #             # Only SOA
    #             if partner.max_followup_id.send_type == 'soa':
    #                 # start_date = datetime.datetime.today().date().replace(day=1)
    #                 end_date = datetime.date.today() + relativedelta(months=+1, day=1, days=-1)
    #                 p_data = {
    #                     'invoice_end_date': end_date,
    #                     'invoice_start_date': start_date,
    #                     'aging_by': 'inv_date',
    #                     'aging_group': 'by_month',
    #                     'account_type': 'ar',
    #                     'soa_type': 'all'}
    #                 wiz_id = self.env['customer.statement'].create(p_data)
    #                 del p_data['invoice_end_date']
    #                 p_data.update({'overdue_date': end_date})
    #                 partner.partner_id.write(p_data)
    #                 data = {
    #                     'ids': [wiz_id.id],
    #                     'model': 'customer.statement',
    #                     'form': [partner.partner_id.id]
    #                     }
    #                 report_template_id = self.env.ref('goexcel_customer_statement.report_customer_statement').render_qweb_pdf(wiz_id.id, data=data)
    #                 data_record = base64.b64encode(report_template_id[0])
    #                 ir_values = {
    #                     'name': "Statement of Account.pdf",
    #                     'type': 'binary',
    #                     'datas': data_record,
    #                     'datas_fname': "Statement of Account.pdf",
    #                     'store_fname': 'Statement of Account',
    #                     'mimetype': 'application/pdf',
    #                 }
    #                 only_soa_pdf = self.env['ir.attachment'].create(ir_values)

    #             # Only Overdue Invoices
    #             if partner.max_followup_id.send_type == 'overdue_invoices':
    #                 over_due_inv = self.env['account.invoice'].search([('date_due', '<=', datetime.date.today()), ('state', '=', 'open'), ('partner_id', '=', partner.partner_id.id), ('type', '=', 'out_invoice')])
    #                 if len(over_due_inv) > 0:
    #                     # report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(over_due_inv.ids)
    #                     report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(over_due_inv.ids)

    #                     data_record = base64.b64encode(report_template_id[0])
    #                     ir_values = {
    #                        'name': "Overdue Invoices.pdf",
    #                        'type': 'binary',
    #                        'datas': data_record,
    #                        'datas_fname': "Overdue Invoices.pdf",
    #                        'store_fname': 'Overdue Invoices',
    #                        'mimetype': 'application/pdf',
    #                     }
    #                     over_due_pdf = self.env['ir.attachment'].create(ir_values)

    #             # SOA + OverDue Invoices
    #             if partner.max_followup_id.send_type == 'soa_overdue':
    #                 # SOA Data Create
    #                 # start_date = datetime.datetime.today().date().replace(day=1)
    #                 end_date = datetime.date.today() + relativedelta(months=+1, day=1, days=-1)
    #                 p_data = {
    #                     'invoice_end_date': end_date,
    #                     'invoice_start_date': start_date,
    #                     'aging_by': 'inv_date',
    #                     'aging_group': 'by_month',
    #                     'account_type': 'ar',
    #                     'soa_type': 'all'}
    #                 wiz_id = self.env['customer.statement'].create(p_data)
    #                 del p_data['invoice_end_date']
    #                 p_data.update({'overdue_date': end_date})
    #                 partner.partner_id.write(p_data)
    #                 data = {
    #                     'ids': [wiz_id.id],
    #                     'model': 'customer.statement',
    #                     'form': [partner.partner_id.id]
    #                     }
    #                 report_template_id = self.env.ref('goexcel_customer_statement.report_customer_statement').render_qweb_pdf(wiz_id.id, data=data)
    #                 data_record = base64.b64encode(report_template_id[0])
    #                 ir_values = {
    #                     'name': "Statement of Account.pdf",
    #                     'type': 'binary',
    #                     'datas': data_record,
    #                     'datas_fname': "Statement of Account.pdf",
    #                     'store_fname': 'Statement of Account',
    #                     'mimetype': 'application/pdf',
    #                 }
    #                 only_soa_pdf = self.env['ir.attachment'].create(ir_values)
    #                 # overdue Invocie Created
    #                 over_due_inv = self.env['account.invoice'].search([('date_due', '<=', datetime.date.today()), ('state', '=', 'open'), ('partner_id', '=', partner.partner_id.id), ('type', '=', 'out_invoice')])
    #                 if len(over_due_inv) > 0:
    #                     # report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(over_due_inv.ids)
    #                     report_template_id = self.env.user.company_id.payment_followup_report_id.render_qweb_pdf(over_due_inv.ids)
    #                     data_record = base64.b64encode(report_template_id[0])
    #                     ir_values = {
    #                        'name': "Overdue Invoices.pdf",
    #                        'type': 'binary',
    #                        'datas': data_record,
    #                        'datas_fname': "Overdue Invoices.pdf",
    #                        'store_fname': 'Overdue Invoices',
    #                        'mimetype': 'application/pdf',
    #                     }
    #                     over_due_pdf = self.env['ir.attachment'].create(ir_values)

    #             template = False
    #             try:
    #                 if partner.max_followup_id.email_template_id:
    #                     template = partner.max_followup_id.email_template_id
    #                 else:
    #                     if partner.max_followup_id.send_type == 'soa':
    #                         template = self.env.ref('payment_followup.email_template_soa_customer_statement')
    #                     elif partner.max_followup_id.send_type == 'overdue_invoices':
    #                         template = self.env.ref('payment_followup.email_template_overdue_customer_statement')
    #                     else:
    #                         template = self.env.ref('payment_followup.email_template_soa_overdue_customer_statement')
    #             except ValueError:
    #                 template = False
    #             if template:
    #                 template.attachment_ids = False
    #                 # TS - use the
    #                 template_values = {
    #                         'email_to': partner.partner_id.followup_emails,
    #                         'email_cc': False,
    #                         'auto_delete': True,
    #                         'partner_to': False,
    #                     }
    #                 if over_due_pdf:
    #                     template.attachment_ids = [(4, over_due_pdf.id)]
    #                 if only_soa_pdf:
    #                     template.attachment_ids = [(4, only_soa_pdf.id)]
    #                 template.sudo().write(template_values)
    #                 if send_flag:
    #                     partner_data = {
    #                             'last_sent_date': datetime.datetime.now(),
    #                             'last_sent_by': self.env.uid,
    #                             'last_followup_level_id': partner.max_followup_id.id,
    #                             'last_action_type': partner.max_followup_id.action_type,
    #                             'last_send_type': partner.max_followup_id.send_type
    #                             }
    #                     partner.partner_id.write(partner_data)
    #                     template.sudo().send_mail(partner.partner_id.id, force_send=True, raise_exception=True)
    #                     template.attachment_ids = False
    #                     if over_due_pdf:
    #                         over_due_pdf.unlink()
    #                     self.env['partner.payment.followup'].create(histry_data)
