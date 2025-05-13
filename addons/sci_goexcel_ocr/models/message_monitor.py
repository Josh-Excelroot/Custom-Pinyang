from odoo import models, fields, api
from odoo.exceptions import Warning
from datetime import datetime

class MessageMonitor(models.Model):
    _name = 'message.monitor'

    name = fields.Char(string='Name', default=datetime.today())
    type = fields.Char()
    object_id = fields.Integer()
    stage = fields.Selection([('draft', 'Draft'),
                             ('in_progress', 'In Progress'),
                             ('complete', 'Complete'),
                             ], default='draft', string="Stage")
    has_attachment = fields.Boolean()
    completed_on = fields.Datetime('Completed On')

    def execute_invoice_ocr(self):
        print("execute_invoice_ocr")
        new_messages = self.env['message.monitor'].search([('stage', '=', 'draft'), ('has_attachment', '=', True)], limit = 5)
        print(new_messages)
        for message in new_messages:
            object_type = self.env[message.type]
            object = object_type.browse(message.object_id)
            object.action_get_attachment()
            message.stage = 'complete'
            message.completed_on = datetime.now()