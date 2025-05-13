# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

import logging
_logger = logging.getLogger(__name__)

from odoo.http import request
from odoo import http, SUPERUSER_ID


class RecentlyViewedRecord(http.Controller):

    @http.route(['/recently/view/records'], type='json', auth='public', csrf=False)
    def recently_view_record(self, name=False, url=False, record_id=False, model=False, action=False, **post):
        result = {'status': True}
        #check if there is existing records.
        records = request.env['recently.viewed.record'].search([('record_id', '=', record_id), ('model', '=', model), ('user_id', '=', request._uid)], limit=1)
        if not records:
            if name and record_id and model:
                if not action:
                    action_name = request.env['ir.actions.act_window'].search([('res_model', '=', model), ('view_type', '=', 'form'), ('type', '=', 'ir.actions.act_window')], limit=1).name
                else:
                    action_name = request.env['ir.actions.act_window'].browse(action).name
                if action_name:
                    request.env['recently.viewed.record'].create({'name': action_name + '/' + name, 'url': url, 'record_id': record_id, 'model': model, 'user_id': request._uid})
            else:
                return {}
        else:
            records.write({'url': url, })
            result['status'] = False
        request._cr.commit()
        if result['status']:
            result['records_list'] = self._get_recently_record()
        return result

    @http.route(['/get/recently/view/records'], type='json', auth='public', csrf=False)
    def get_recently_view_record(self, **post):
        return self._get_recently_record()

    def _get_recently_record(self):
        # TS - bugs - recently_viewed_limit is False in the config_vals, may be not load properly
        #config_vals = request.env['res.config.settings'].sudo().get_values()
        #print('config_vals =', config_vals )
        #viewed_limit = config_vals.get('recently_viewed_limit')
        #print('viewed_limit=', viewed_limit)
        viewed_limit = 10
        #records = request.env['recently.viewed.record'].search([('user_id', '=', request._uid)], limit=viewed_limit)
        records = request.env['recently.viewed.record'].search([('user_id', '=', request._uid)])
        if records and len(records) > viewed_limit:
            #print('len record=', str(len(records)))
            count = 0
            records_list = []
            sorted_records = records.sorted(key=lambda r: r.id, reverse=True)
            for record in sorted_records:
                count += 1
                #if more than 10 records, delete.
                if count > viewed_limit:
                    #print('delete record name=', record.name, ' model=', record.model)
                    record.sudo().unlink()
                else:
                    #print('record name=', record.name, ' model=', record.model)
                    record_dict = {'name': record.name, 'id': record.record_id, 'model': record.model,
                                   'url': record.url}
                    records_list.append(record_dict)
            return records_list

        else:
            records_list = []
            for record in records:
                record_dict = {'name': record.name, 'id': record.record_id, 'model': record.model, 'url': record.url}
                records_list.append(record_dict)
            return records_list
