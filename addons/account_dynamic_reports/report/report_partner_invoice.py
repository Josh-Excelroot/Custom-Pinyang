# -*- coding: utf-8 -*-

from odoo import api, models


class InsReportPartnerInvoice(models.AbstractModel):
    _name = 'report.account_dynamic_reports.partner_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):

        # If it is a call from Js window
        if self.env.context.get('from_js'):
            if data.get('js_data'):
                data.update({'Ledger_data': data.get('js_data')[1],
                             'Filters': data.get('js_data')[0],
                             })
        return data
