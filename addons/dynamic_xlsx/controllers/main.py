# Copyright (C) 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo.addons.web.controllers import main as report
from odoo.http import content_disposition, route, request
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime

import json
import time
import werkzeug


class ReportController(report.ReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == 'xlsx':
            try:
                report = request.env['ir.actions.report']._get_report_from_name(
                    reportname)
                context = dict(request.env.context)
                if docids:
                    docids = [int(i) for i in docids.split(',')]
                if data.get('options'):
                    data.update(json.loads(data.pop('options')))
                if data.get('context'):
                    # Ignore 'lang' here, because the context in data is the one
                    # from the webclient *but* if the user explicitely wants to
                    # change the lang, this mechanism overwrites it.
                    data['context'] = json.loads(data['context'])
                    if data['context'].get('lang'):
                        del data['context']['lang']
                    context.update(data['context'])
                xlsx = report.with_context(context).render_xlsx(
                    docids, data=data
                )[0]
                report_name = report.report_file
                if report.print_report_name and not len(docids) > 1:
                    obj = request.env[report.model].browse(docids[0])
                    report_name = safe_eval(report.print_report_name,
                                            {'object': obj, 'time': time})

                if reportname == 'dynamic_xlsx.ins_financial_report_xlsx':
                    account_report_name = request.env[report.model_id.model] \
                        .search([('id', '=', docids)]) \
                        .account_report_id.name
                    # if account_report_name == 'BALANCE SHEET':
                    #     report_name = 'Balance Sheet' + datetime.now().strftime(' %d-%m-%Y')

                elif reportname == 'dynamic_xlsx.ins_partner_ledger_xlsx':
                    report_name = 'Partner Ledger' + datetime.now().strftime(' %d-%m-%Y')

                elif reportname == 'dynamic_xlsx.ins_trial_balance_xlsx':
                    report_name = 'Trial Balance' + datetime.now().strftime(' %d-%m-%Y')

            except (UserError, ValidationError) as odoo_error:
                raise werkzeug.exceptions.HTTPException(
                    description='{error_name}. {error_value}'.format(
                        error_name=odoo_error.name,
                        error_value=odoo_error.value,
                    ))
            xlsxhttpheaders = [
                ('Content-Type', 'application/vnd.openxmlformats-'
                                 'officedocument.spreadsheetml.sheet'),
                ('Content-Length', len(xlsx)),
                (
                    'Content-Disposition',
                    content_disposition(report_name + '.xlsx')
                )
            ]
            return request.make_response(xlsx, headers=xlsxhttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data
        )
