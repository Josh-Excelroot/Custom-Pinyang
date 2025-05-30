# -*- coding: utf-8 -*-

import time
import json

from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta

class PrintPreviewController(http.Controller):

    @http.route(['/pdf_print_preview/get_report_name'], type='json', auth="user")
    def get_report_name(self, report_name=False, data={}):
        file_name = False

        if not report_name:
            return file_name

        report = request.env['ir.actions.report']._get_report_from_name(
            report_name
        )

        if not report:
            return file_name

        print_report_name = report.print_report_name
        #print('>>>>>>>>>>>> get_report_name pdf_print_preview=', print_report_name)
        data = json.loads(data)
        # if report_name == 'goexcel_customer_statement.cust_statement_template':
        #     ids = data.get('active_id', [])
        # else:
        #     ids = data.get('active_ids', [])
        ids = data.get('active_ids', [])
        if report_name == 'goexcel_customer_statement.cust_statement_template':
            wiz_ids = request.env['customer.statement'].browse(ids)
            data['active_ids'] = wiz_ids.partner_ids.ids
        ids = data.get('active_ids', [])
        records = request.env[report.model].browse(ids)
        if print_report_name and not len(records) > 1:
            file_name = safe_eval(
                print_report_name, {'object': records, 'time': time})
            # TS Bug - print invoice without the invoice no, will have error
            file_name = file_name and file_name or 'False' + ' ' + datetime.today().strftime("%d-%m-%Y")
            return {
                'file_name': file_name,
                'wkhtmltopdf_state': request.env['ir.actions.report'].get_wkhtmltopdf_state()
            }
        else:
            return file_name
