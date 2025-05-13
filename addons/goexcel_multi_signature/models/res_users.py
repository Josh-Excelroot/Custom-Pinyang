from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.depends('company_id', 'user_sign_ids')
    @api.onchange('company_id', 'user_sign_ids')
    def onchange_company(self):
        for res in self:
            print ("res", res.company_id.name)
            user_sign = self.env['user.signature'].search([('company_id', '=', res.company_id.id), ('use_for_gen', '=', True)], limit=1)
            if user_sign and user_sign.signature_image:
                res.signature_image = user_sign.signature_image

    #signature = fields.Html(compute="onchange_company", readonly=False)
    signature_image = fields.Binary("Signature", compute="onchange_company")
    user_sign_ids = fields.One2many('user.signature', 'user_id', string="User Signature", track_visibility='onchange')

    def write(self, value):
        if 'company_id' in value:
            #print (">>>>>>>>>", value, self.signature)
            user_sign = self.env['user.signature'].search([('company_id', '=', value['company_id']), ('use_for_gen', '=', True)], limit=1)
            if user_sign and user_sign.signature_image:
                value['signature_image'] = user_sign.signature_image
        res = super(ResUsers, self).write(value)
        return res


class UserSignature(models.Model):
    _name = 'user.signature'
    _description = "User Signature"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    #signature = fields.Html('Signature', required=True)
    user_id = fields.Many2one('res.users', string='User')
    sequence = fields.Integer(default=10)
    use_for_gen = fields.Boolean(string="Use For Report")
    signature_image = fields.Binary("Signature")
