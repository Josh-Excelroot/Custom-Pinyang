# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models


class RefuseLeave(models.TransientModel):

    _name = 'refuse.leave'
    _description = "Refuse Leave"

    reason = fields.Text('Reason')

    @api.multi
    def add_reason(self):
        context = dict(self._context)
        if not context.get('active_id'):
            return {}
        user_data = self.env['res.users'].browse(self._uid)
        holiday = self.env['hr.leave'
                           ].browse(context.get('active_id'))
        manager = self.env['hr.employee'
                           ].search([('user_id', '=', self.env.uid)], limit=1)
        for data in self:
            if data.reason:
                new_data = "Leave Refused Reason. (%s) \n-------------" \
                    "------------------------------------------------------" \
                    "---------" % user_data.name
                orignal_note = ''
                if holiday.notes:
                    orignal_note = holiday.notes
                reason = orignal_note + "\n\n" + new_data + \
                    "\n\n" + data.reason or ''
                if holiday.state == 'validate1':
                    holiday.write({'state': 'refuse', 'manager_id': manager.id,
                                   'notes': reason, 'rejection': data.reason})
                else:
                    holiday.write({'state': 'refuse', 'manager_id2': manager.id,
                                   'notes': reason, 'rejection': data.reason})
                # Delete the meeting
                if holiday.meeting_id:
                    holiday.meeting_id.unlink()
                # If a category that created several holidays, cancel
                # all related
                holiday.linked_request_ids.action_refuse()
                holiday._remove_resource_leave()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
