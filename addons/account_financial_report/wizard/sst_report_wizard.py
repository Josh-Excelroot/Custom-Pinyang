# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import ValidationError


class SSTReportWizard(models.TransientModel):
    _name = "sst.report.wizard"
    _description = "SST Report Wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    # date_range_id = fields.Many2one(
    #     comodel_name='date.range',
    #     string='Date range'
    # )
    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    paid_only = fields.Selection([('all', 'All'), ('paid', 'Paid SST'), ('unpaid', 'Unpaid SST')], string='SST', required=True,
                                 default='all')
    type_of_tax = fields.Selection([('Sales Tax', 'Sales Tax'), ('Service Tax', 'Service Tax'), ], string='Type of Tax',
                                   required=True, default='Sales Tax')
    is_b2b_exemption = fields.Boolean(string="Include B2B Exemption", default=True)

    # based_on = fields.Selection([('taxtags', 'Tax Tags'),
    #                              ('taxgroups', 'Tax Groups')],
    #                             string='Based On',
    #                             required=True,
    #                             default='taxtags')
    # tax_detail = fields.Boolean('Detail Taxes')

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     # if self.company_id and self.date_range_id.company_id and \
    #     #         self.date_range_id.company_id != self.company_id:
    #         #self.date_range_id = False
    #     res = {}
    #     res = {'domain': {'account_ids': [],
    #                       'partner_ids': []}}
    #     if not self.company_id:
    #         return res
    #     else:
    #         res['domain'] += [
    #             '|', ('company_id', '=', self.company_id.id),
    #             ('company_id', '=', False)]
    #     return res

    # @api.onchange('date_range_id')
    # def onchange_date_range_id(self):
    #     """Handle date range change."""
    #     self.date_from = self.date_range_id.date_start
    #     self.date_to = self.date_range_id.date_end

    # @api.multi
    # @api.constrains('company_id', 'date_range_id')
    # def _check_company_id_date_range_id(self):
    #     for rec in self.sudo():
    #         if rec.company_id and rec.date_range_id.company_id and\
    #                 rec.company_id != rec.date_range_id.company_id:
    #             raise ValidationError(
    #                 _('The Company in the SST Report Wizard and in '
    #                   'Date Range must be the same.'))

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref('account_financial_report.action_report_sst_report')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_sst_report']
        report = model.create(self._prepare_sst_report())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_sst_02_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        model = self.env['report_sst_s2_report']
        report = model.create(self._prepare_sst_report())
        report.compute_data_for_report()
        return report.print_report(report_type)
        # return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_sst_report(self):
        self.ensure_one()
        # self.date_validation()
        return {
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'paid_only': self.paid_only,
            'is_b2b_exemption': self.is_b2b_exemption,
            'type_of_tax': self.type_of_tax,
            # 'tax_detail': self.tax_detail,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_sst_report']
        report = model.create(self._prepare_sst_report())
        report.compute_data_for_report()
        return report.print_report(report_type)

    def date_validation(self):
        if self.paid_only == 'paid':
            payment_dates = self.payment_date_to or self.payment_date_from
            invoice_dates = self.date_to or self.date_from
            if payment_dates and invoice_dates:
                raise ValidationError("You can either use invoice date or payment date, not both.")
            elif (self.date_to and not self.date_from) or (self.date_from and not self.date_to):
                raise ValidationError("Missing Invoice Date Range Filter")
            elif (self.payment_date_to and not self.payment_date_from) or (
                    self.payment_date_from and not self.payment_date_to):
                raise ValidationError("Missing Payment Date Range Filter")

    def export_to_sst_second(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export_second(report_type)

    def _export_second(self, report_type):
        """Default export is PDF."""
        model = self.env['report_sst_report']
        report = model.create(self._prepare_sst_report())
        report.with_context(sst_02=True).compute_data_for_report()
        return report.print_report_sst(report_type)