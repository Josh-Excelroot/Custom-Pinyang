# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CostCenter(models.Model):
    _name = 'cost.center'
    _description = "Cost Center"

    name = fields.Char('Name', size=64, required=True)


class ProductCategory(models.Model):
    _inherit = "product.category"

    cost_center_id = fields.Many2one('cost.center', 'Cost center')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    branch_id = fields.Char("Branch ID", size=48)


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread','mail.activity.mixin']

    @api.multi
    def send_payslip_mail(self):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'l10n_my_payroll_report', 'email_temp_emp_payslip')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'hr.payslip',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_subject': self.name,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            'force_email': True
        }
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
    def send_quick_payslip_mail(self):
        mail_obj = self.env["ir.mail_server"]
        for rec in self:
            mail_server_id = mail_obj.search([], limit=1)
            if mail_server_id and mail_server_id.smtp_user and rec.employee_id and rec.employee_id.work_email:
                template_id = self.env.ref(
                    'l10n_my_payroll_report.email_temp_emp_payslip')
                if template_id:
                    email_from = template_id.email_from
                    email_to = template_id.email_to
                    subject = template_id.subject
                    template_id.write({
                        'email_from': mail_server_id.smtp_user,
                        'email_to': rec.employee_id.work_email,
                        'subject': rec.name,
                    })
                    template_id.send_mail(rec.id, force_send=True)
                    template_id.write({
                        'email_from': email_from,
                        'email_to': email_to,
                        'subject': subject,
                    })

    @api.multi
    def compute_sheet(self):
        if not self.employee_id.pcb_number and not self.employee_id.is_non_permanent_employee:
            raise ValidationError('Please fill in PCB number in the Employee -> Statutory Requirements Tab')
        if self.employee_id.is_non_permanent_employee and not self.contract_id.rate_per_hour:
            raise ValidationError('Please fill in Hourly Wage Per Hour In Contract -> Salary Information Tab')
        return super(HrPayslip,self).compute_sheet()

    @api.multi
    def _get_all_allowance(self):
        if self.contract_id:
            return self.contract_id.contract_allowance_id
        return None
