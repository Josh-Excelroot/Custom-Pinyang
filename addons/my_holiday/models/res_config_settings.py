from odoo import api, fields, models, _

#kashif 1 sept 23: updates code to store users for leave notify
class Company(models.Model):
    _inherit = 'res.company'

    request_leave_recipients = fields.Many2many('res.users','request_user_default_rel',string="Request Leave Notification Recipient")
    approve_leave_recipients = fields.Many2many('res.users','approve_user_default_rel', string="Approve Leave Notification Recipient")



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    request_leave_recipients = fields.Many2many('res.users',string="Request Leave Notification Recipient",readonly=False
                                               ,related='company_id.request_leave_recipients')
    approve_leave_recipients = fields.Many2many('res.users', string="Approve Leave Notification Recipient",readonly=False
                                               ,related='company_id.approve_leave_recipients')

#end