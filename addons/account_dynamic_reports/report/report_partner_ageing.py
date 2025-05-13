# -*- coding: utf-8 -*-

from odoo import api, models


class InsReportPartnerAgeing(models.AbstractModel):
    _name = 'report.account_dynamic_reports.partner_ageing'

    @api.model
    def _get_report_values(self, docids, data=None):
        # If it is a call from Js window
        if self.env.context.get('from_js'):
            if data.get('js_data'):
                ageing_lines = data.get('js_data')[1]
                filters = data.get('js_data')[0]
                part_list = list(ageing_lines.keys())
                partner_list = [key[1] for key in filters['partners_list'] if key[0] in part_list] or []
                partner_list = list(set(partner_list))
                partner_list.sort()
                partner_list.append('Total')
                data.update({'Ageing_data': data.get('js_data')[1],
                             'Filters': data.get('js_data')[0],
                             'Period_Dict': data.get('js_data')[2],
                             'partner_list': partner_list,
                             'Period_List': data.get('js_data')[3],
                             'currency_id': self.env['res.currency'].browse(data.get('js_data')[0]['currency_id'])
                             })
        return data
