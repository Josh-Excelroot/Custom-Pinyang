from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import xlsxwriter


class PayrollPostingWiz(models.TransientModel):

    _name = 'payroll.posting.wiz'
    _description = "Payroll Posting Wizard"

    posting = fields.Selection([('individual', 'Individual Posting'), ('group', 'Group Posting')], string="Posting")
    date_start = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    payslip_ids = fields.Many2many('hr.payslip', string="Payslip")
    journal_id = fields.Many2one('account.journal', string="Journal")
    bulk_payment_file_bank_id = fields.Many2one('res.bank', string="Select Bank to Download Bulk Payment File")

    @api.onchange('date_start', 'end_date')
    def onchange_employee_information(self):
        payslip = self.env['hr.payslip'].search([('date_from', '>=', self.date_start), ('date_to', '<=', self.end_date), ('state', '=', 'draft')])
        if payslip:
            self.payslip_ids = [(6, 0, payslip.ids)]

    @api.multi
    def generate_journal(self):
        if self.posting == 'individual':
            for rec in self.payslip_ids:
                rec.action_payslip_done()
            return {
                'name': _('Employee Payslips'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'hr.payslip',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', self.payslip_ids.ids)],
                'target': 'current',
                'context': {}
            }
        if self.posting == 'group':
            move_dict = {
                'narration': 'All Payslip from' + str(self.date_start) + ' to ' + str(self.end_date),
                'ref': str(self.date_start) + ' to ' + str(self.end_date),
                'journal_id': self.journal_id.id,
                'date': datetime.today().date(),
            }
            eis_total = 0.0
            scs_total = 0.0
            epf_total = 0.0
            gross_total = 0.0
            net_total = 0.0
            credit_sum = 0.0
            eis_gtotal = 0.0
            scs_gtotal = 0.0
            epf_gtotal = 0.0
            pcb_gtotal = 0.0
            eis_account = False
            scs_account = False
            epf_account = False
            net_account = False
            gross_account = False
            company = False
            line_ids = []
            for rec in self.payslip_ids:
                company = rec.company_id
                rec.compute_sheet()
                for line in rec.details_by_salary_rule_category:
                    if line.code == 'EISY':
                        credit_sum += line.total
                        eis_total += line.total
                        if not line.salary_rule_id.account_debit:
                            raise ValidationError(_("Please Configure Account In EIS Employer!!"))
                        eis_account = line.salary_rule_id.account_debit.id
                    if line.code == 'SCSY':
                        credit_sum += line.total
                        scs_total += line.total
                        if not line.salary_rule_id.account_debit:
                            raise ValidationError(_("Please Configure Account In SOCSO Employer!!"))
                        scs_account = line.salary_rule_id.account_debit.id
                    if line.code == 'EPF_Y_NORMAL':
                        credit_sum += line.total
                        epf_total += line.total
                        if not line.salary_rule_id.account_debit:
                            raise ValidationError(_("Please Configure Account In EPF Employer!!"))
                        epf_account = line.salary_rule_id.account_debit.id
                    if line.code == 'GROSS':
                        gross_total += line.total
                        if not line.salary_rule_id.account_debit:
                            raise ValidationError(_("Please Configure Account In Gross!!"))
                        gross_account = line.salary_rule_id.account_debit.id
                    if line.code == 'NET':
                        net_total += line.total
                        if not line.salary_rule_id.account_credit:
                            raise ValidationError(_("Please Configure Account In Net!!"))
                        net_account = line.salary_rule_id.account_credit.id
                    if line.code == 'DEPFE':
                        epf_gtotal += line.total
                    if line.code == 'SCSE':
                        scs_gtotal += line.total
                    if line.code == 'EISE':
                        eis_gtotal += line.total
                    if line.code == 'PCBCURRMONTH':
                        pcb_gtotal += line.total
            credit_account_id = company.accrual_account_id.id
            accrual_epf_id = company.accrual_epf_id.id
            accrual_socso_id = company.accrual_socso_id.id
            accrual_eis_id = company.accrual_eis_id.id
            accrual_pcb_id = company.accrual_pcb_id.id
            if not credit_account_id:
                raise ValidationError(_("Please Configure Accrual Account!!"))
            if company.accraul_type == 'diff_accrual':
                if not accrual_epf_id:
                    raise ValidationError(_("Please Add Accrual-EPF Account!!!"))
                if not accrual_socso_id:
                    raise ValidationError(_("Please Add Accrual-SOCSO Account!!!"))
                if not accrual_eis_id:
                    raise ValidationError(_("Please Add Accrual-EIS Account!!!"))
                if not accrual_pcb_id:
                    raise ValidationError(_("Please Add Accrual-PCB Account!!!"))
            if eis_total > 0:
                debit_line = (0, 0, {
                    'name': 'EIS (Employer)',
                    'account_id': eis_account,
                    'journal_id': self.journal_id.id,
                    'date': datetime.today().date(),
                    'debit': eis_total > 0.0 and eis_total or 0.0,
                    'credit': eis_total < 0.0 and -eis_total or 0.0,
                })
                line_ids.append(debit_line)
            if scs_total > 0:
                debit_line = (0, 0, {
                    'name': 'SCS (Employer)',
                    'account_id': scs_account,
                    'journal_id': self.journal_id.id,
                    'date': datetime.today().date(),
                    'debit': scs_total > 0.0 and scs_total or 0.0,
                    'credit': scs_total < 0.0 and -scs_total or 0.0,
                })
                line_ids.append(debit_line)
            if epf_total > 0:
                debit_line = (0, 0, {
                    'name': 'EPF (Employer)',
                    'account_id': epf_account,
                    'journal_id': self.journal_id.id,
                    'date': datetime.today().date(),
                    'debit': epf_total > 0.0 and epf_total or 0.0,
                    'credit': epf_total < 0.0 and -epf_total or 0.0,
                })
                line_ids.append(debit_line)
            if gross_total > 0:
                debit_line = (0, 0, {
                    'name': 'Gross',
                    'account_id': gross_account,
                    'journal_id': self.journal_id.id,
                    'date': datetime.today().date(),
                    'debit': gross_total > 0.0 and gross_total or 0.0,
                    'credit': gross_total < 0.0 and -gross_total or 0.0,
                })
                line_ids.append(debit_line)
            if net_total > 0:
                credit_line = (0, 0, {
                    'name': line.name,
                    'account_id': net_account,
                    'journal_id': self.journal_id.id,
                    'date': datetime.today().date(),
                    'debit': net_total < 0.0 and -net_total or 0.0,
                    'credit': net_total > 0.0 and net_total or 0.0,
                })
                line_ids.append(credit_line)
            if company.accraul_type == 'all_in_one':
                total = credit_sum + eis_gtotal + scs_gtotal + pcb_gtotal + epf_gtotal
                if credit_sum > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - Salary',
                        'account_id': credit_account_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': total < 0.0 and -total or 0.0,
                        'credit': total > 0.0 and total or 0.0,
                    })
                    line_ids.append(credit_line)
            if company.accraul_type == 'diff_accrual':
                if credit_account_id and credit_sum > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - Salary',
                        'account_id': credit_account_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': credit_sum < 0.0 and -credit_sum or 0.0,
                        'credit': credit_sum > 0.0 and credit_sum or 0.0,
                    })
                    line_ids.append(credit_line)
                if accrual_epf_id and epf_gtotal > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - EPF',
                        'account_id': accrual_epf_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': epf_gtotal < 0.0 and -epf_gtotal or 0.0,
                        'credit': epf_gtotal > 0.0 and epf_gtotal or 0.0,
                    })
                    line_ids.append(credit_line)
                if accrual_socso_id and scs_gtotal > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - SOCSO',
                        'account_id': accrual_socso_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': scs_gtotal < 0.0 and -scs_gtotal or 0.0,
                        'credit': scs_gtotal > 0.0 and scs_gtotal or 0.0,
                    })
                    line_ids.append(credit_line)
                if accrual_eis_id and eis_gtotal > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - EIS',
                        'account_id': accrual_eis_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': eis_gtotal < 0.0 and -eis_gtotal or 0.0,
                        'credit': eis_gtotal > 0.0 and eis_gtotal or 0.0,
                    })
                    line_ids.append(credit_line)
                if accrual_pcb_id and pcb_gtotal > 0:
                    credit_line = (0, 0, {
                        'name': 'Accrual - PCB',
                        'account_id': accrual_pcb_id,
                        'journal_id': self.journal_id.id,
                        'date': datetime.today().date(),
                        'debit': pcb_gtotal < 0.0 and -pcb_gtotal or 0.0,
                        'credit': pcb_gtotal > 0.0 and pcb_gtotal or 0.0,
                    })
                    line_ids.append(credit_line)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            move.post()
            for pay in self.payslip_ids:
                pay.write({'move_id': move.id, 'date': datetime.today().date(), 'state': 'done'})
            return {
                'name': _('Journal Entries'),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'res_id': move.id,
                'target': 'current'
            }



    def download_bank_file(self):
        if not self.payslip_ids:
            raise UserError('No Slips Selected!')

        return self.env.ref('l10n_my_payroll_report.action_bank_bulk_payment_report_xlsx').report_action(self)


