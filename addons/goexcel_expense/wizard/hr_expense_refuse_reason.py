# -*- coding: utf-8 -*-

from odoo import api, models


class HrExpenseRefuseWizard(models.TransientModel):
    _inherit = "hr.expense.refuse.wizard"

    @api.multi
    def expense_refuse_reason(self):
        res = super(HrExpenseRefuseWizard, self).expense_refuse_reason()
        for rec in self:
            if rec.hr_expense_sheet_id.user_id and rec.hr_expense_sheet_id.user_id.email:
                template_id = self.env.ref(
                    'goexcel_expense.email_template_event_refuse')
                if template_id:
                    template_id.write({
                        'email_from': rec.hr_expense_sheet_id.user_id.email,
                        'email_to': rec.hr_expense_sheet_id.employee_id.user_id.email
                    })
                    template_id.send_mail(rec.id, force_send=True)
        return res
