# -*- coding: utf-8 -*-

import json
import time
from odoo.addons.web.controllers.main import ReportController
from odoo.http import request, content_disposition, serialize_exception as _serialize_exception
from odoo import http
from werkzeug.urls import url_decode
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval


@http.route(['/report/download'], type='http', auth="user")
def report_download(self, data, token):
    """This function is used by 'action_manager_report.js' in order to trigger the download of
    a pdf/controller report.

    :param data: a javascript array JSON.stringified containg report internal url ([0]) and
    type [1]
    :returns: Response with a filetoken cookie and an attachment header
    """
    requestcontent = json.loads(data)
    url, type = requestcontent[0], requestcontent[1]
    try:
        if type in ['qweb-pdf', 'qweb-text']:
            converter = 'pdf' if type == 'qweb-pdf' else 'text'
            extension = 'pdf' if type == 'qweb-pdf' else 'txt'

            pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
            reportname = url.split(pattern)[1].split('?')[0]
            docids = None
            if '/' in reportname:
                reportname, docids = reportname.split('/')

            if docids:
                # Generic report:
                response = self.report_routes(reportname, docids=docids, converter=converter)
            else:
                # Particular report:
                data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
                response = self.report_routes(reportname, converter=converter, **dict(data))

            report = request.env['ir.actions.report']._get_report_from_name(reportname)
            filename = "%s.%s" % (report.name, extension)

            if docids:
                ids = [int(x) for x in docids.split(",")]
                obj = request.env[report.model].browse(ids)
                if report.print_report_name and not len(obj) > 1:
                    report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                    filename = "%s.%s" % (report_name, extension)
            if reportname == 'goexcel_customer_statement.cust_statement_template':
                pattern = 'form%22%3A%5B'
                wiz_ids = url.split(pattern)[1].split('%5D')[0]
                partners = request.env['res.partner'].browse(int(wiz_ids))
                report_name = safe_eval(report.print_report_name, {'object': partners, 'time': time})
                filename = "%s.%s" % (report_name, extension)
            response.headers.add('Content-Disposition', content_disposition(filename))
            response.set_cookie('fileToken', token)
            return response
        else:
            return
    except Exception as e:
        se = _serialize_exception(e)
        error = {
            'code': 200,
            'message': "Odoo Server Error",
            'data': se
        }
        return request.make_response(html_escape(json.dumps(error)))


ReportController.report_download = report_download
