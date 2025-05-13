# See LICENSE file for full copyright and licensing details

from odoo import fields, models


class HrPayrollConfiguration(models.TransientModel):

    _inherit = 'res.config.settings'

    module_l10n_my_payroll_report = fields.Boolean(
        'Generate Payroll Reports',
        help="This help to Generate payroll reports")
    module_my_pf_report = fields.Boolean(
        "Generate PF Reports",
        help="This help to generate PF report")
    module_socso_report = fields.Boolean(
        "Generate SOCSO Report",
        help="This help to generate socso report")
    day_of_generate_payslip = fields.Selection(
        related='company_id.day_of_generate_payslip', string="Month-End Payslip Generation Day", readonly=False)
    accrual_account_id = fields.Many2one(related='company_id.accrual_account_id', string='Accrual-Salary', readonly=False)
    accrual_epf_id = fields.Many2one(related='company_id.accrual_epf_id', string='Accrual-EPF', readonly=False)
    accrual_socso_id = fields.Many2one(related='company_id.accrual_socso_id', string='Accrual-SOCSO', readonly=False)
    accrual_eis_id = fields.Many2one(related='company_id.accrual_eis_id', string='Accrual-EIS', readonly=False)
    accrual_pcb_id = fields.Many2one(related='company_id.accrual_pcb_id', string='Accrual-PCB', readonly=False)
    enable_pro_data_sal = fields.Boolean(related='company_id.enable_pro_data_sal', string="Enable Pro Rata Salary", readonly=False)
    working_days_month = fields.Selection(related='company_id.working_days_month', string="Working Days In a Month", readonly=False)
    public_holiday_paid = fields.Boolean(related='company_id.public_holiday_paid', string="Public holidays are not paid", readonly=False)
    accraul_type = fields.Selection(related='company_id.accraul_type', string="Accrual Type", readonly=False)
    specific_day = fields.Selection([(str(i), str(i)) for i in range(1, 31)]
                                    , default="1", string='Specific Day',
                                    config_parameter='l10n_my_payroll.specific_day')

    frequency_payslip = fields.Selection([('last_working_day', 'Last Working Day of Month'),
                                          ('last_month_day', 'Last Day of Month'),
                                          ('next_1st_day', '1st Day of Next Month')
                                             , ('next_scnd_day', '2nd day of next month')
                                             , ('thrd_day_nxt_mnth', '3RD Day of Next Month'),
                                          ('forth_day_nxt_mnth', '4th Day of Next Month'),
                                          ('fifth_next_month', '5th Day of the Next Month'),
                                          ('specific', 'Specific Day')]
                                         , default="specific", string='Frequency',
                                         config_parameter='l10n_my_payroll.frequency_payslip')
