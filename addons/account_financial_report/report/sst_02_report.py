# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SST02Report(models.AbstractModel):
    _name = "report.account_financial_report.report_sst_02_report"
    #_inherit = 'account_financial_report_abstract'

    # Filters fields, used for data computation
    # company_id = fields.Many2one(comodel_name='res.company')
    # date_from = fields.Date()
    # date_to = fields.Date()
    # paid_only = fields.Selection([('paid', 'Paid SST'),
    #                               ('all', 'All')], string='Paid SST or All', required=True, default='paid')


    @api.model
    def _get_report_values(self, docids, data=None):
