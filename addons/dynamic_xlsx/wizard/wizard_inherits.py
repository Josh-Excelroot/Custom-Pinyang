# -*- coding: utf-8 -*-

from odoo import api, models, fields
import re

from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval


class InsFinancialReport(models.TransientModel):
    _inherit = "ins.financial.report"
    _description = "Financial Reports"

    xlsx_from_js = fields.Boolean()

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        for rec in self:
            rec.xlsx_from_js = self._context.get('from_js', False)
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_financial_report_xlsx').report_action(self)

    def get_report_values(self, from_js=False):
        res = super(InsFinancialReport, self).get_report_values(from_js)

        pdf_report = self.env.ref('account_dynamic_reports.ins_financial_report_pdf').sudo()
        xlsx_report = self.env.ref('dynamic_xlsx.action_ins_financial_report_xlsx').sudo()

        fiscal_year = self.env['account.fiscal.year'].search([('date_from', '=', self.date_from), ('date_to', '=', self.date_to)], limit=1)
        if fiscal_year:
            pdf_report.name = safe_eval(f"'%s - %s' % (object.account_report_id.name,'{fiscal_year.name}')", {'object': self})
            xlsx_report.print_report_name = f"'%s - %s' % (object.account_report_id.name,'{fiscal_year.name}')"
        else:
            pdf_report.name = safe_eval("'%s - %s/%s' % (object.account_report_id.name,object.date_from,object.date_to)", {'object': self})
            xlsx_report.print_report_name = "'%s - %s/%s' % (object.account_report_id.name,object.date_from,object.date_to)"

        return res


class InsGeneralLedger(models.TransientModel):
    _inherit = "ins.general.ledger"
    _description = "General Ledger Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_general_ledger_xlsx').report_action(self)


class InsAnalyticReport(models.TransientModel):
    _inherit = "ins.analytic.report"
    _description = "Analytic Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_analytic_report_xlsx').report_action(self)


class InsPartnerLedger(models.TransientModel):
    _inherit = "ins.partner.ledger"
    _description = "Partner Ledger Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_partner_ledger_xlsx').report_action(self)


class InsPartnerPayment(models.TransientModel):
    _inherit = "ins.partner.payment"
    _description = "Partner Payment Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_partner_payment_xlsx').report_action(self)


class InsPartnerInvoice(models.TransientModel):
    _inherit = "ins.partner.invoice"
    _description = "Partner Invoice Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_partner_invoice_xlsx').report_action(self)


class InsPartnerAgeing(models.TransientModel):
    _inherit = "ins.partner.ageing"
    _description = "Partner Ageing Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_partner_ageing_xlsx').report_action(self)


class InsTrialBalance(models.TransientModel):
    _inherit = "ins.trial.balance"
    _description = "Trial Balance Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return self.env.ref(
            'dynamic_xlsx'
            '.action_ins_trial_balance_xlsx').report_action(self)