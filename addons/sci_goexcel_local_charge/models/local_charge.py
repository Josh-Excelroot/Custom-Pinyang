from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import Warning


class LocalCharge(models.Model):
    _name = 'freight.local.charge'
    _description = 'Local Charge'

    name = fields.Char(string='Name', required=True)
    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange', required=True)
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange',
                                      required=True)

    currency = fields.Many2one('res.currency', string="Currency", required=True, track_visibility='onchange',
                               default=lambda self: self.env.user.company_id.currency_id.id)

    valid_to = fields.Date(string='Valid To', track_visibility='onchange', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'To Approve'),
        ('active', 'Active')], string='Status', index=True, default='draft',
        track_visibility='always', copy=False)

    approve_by = fields.Many2one(
        'res.users', string='Approve By', track_visibility='always')
    approve_date_time = fields.Datetime(string='Approved Date', track_visibility='always', copy=False)

    @api.one
    def _set_access_for_approve_reject_local_charge(self):
        list_of_user = self.env.user.company_id.local_charge_approval_user_ids
        if list_of_user:
            if self.env.user in list_of_user:
                self.approve_reject_local_charge = True
            else:
                self.approve_reject_local_charge = False
        else:
            self.approve_reject_local_charge = False

    price_thc = fields.Float(string='THC Charge', digits=(12, 2), track_visibility='onchange')
    price_doc_fee = fields.Float(string='Doc Fee Charge', digits=(12, 2), track_visibility='onchange')
    price_seal_fee = fields.Float(string='Seal Fee Charge', digits=(12, 2), track_visibility='onchange')
    price_edi = fields.Float(string='EDI Charge', digits=(12, 2), track_visibility='onchange')
    price_telex_release_charge = fields.Float(string='Telex Release Charge', digits=(12, 2),
                                              track_visibility='onchange')
    price_obl = fields.Float(string='OBL Charge', digits=(12, 2), track_visibility='onchange')
    price_communication = fields.Float(string='Communication Charge', digits=(12, 2), track_visibility='onchange')

    approve_reject_local_charge = fields.Boolean(compute="_set_access_for_approve_reject_local_charge")

    @api.multi
    def action_approval(self):
        list_of_approver = []
        action = self.env.ref('sci_goexcel_local_charge.action_configure_local_charge').id
        list_of_user = self.env.user.company_id.local_charge_notification_user_ids
        email_list = [user.email for user in list_of_user]
        if email_list:
            ctx = {}
            ctx['type'] = 'Local Charge'
            ctx['email_from'] = self.env.user.email
            ctx['partner_manager_email'] = ','.join([email for email in email_list if email])
            ctx['lang'] = self.env.user.lang
            ctx['partner_name'] = self.env.user.name

            template = self.env.ref(
                'sci_goexcel_local_charge.local_charge_validate_email_template')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ctx['action_url'] = "{}/web?db={}#id={}&action={}&view_type=form&model=freight.local.charge".format(
                base_url, self.env.cr.dbname, self.id, action)
            template.with_context(ctx).sudo().send_mail(
                self.id, force_send=True, raise_exception=False)
            self.write({'state': 'approve'})

    @api.multi
    def action_approve(self):
        self.write({
            'state': 'active',
            'approve_by': self.env.user.id,
            'approve_date_time': datetime.now(),
        })

    @api.multi
    def action_reject(self):
        self.write({'state': 'draft'})

    local_charge_line_ids = fields.One2many('freight.local.charge.line', 'local_charge_id', string="Line Item")

    @api.onchange('name', 'carrier', 'port_of_loading', 'currency', 'valid_to', 'local_charge_line_ids')
    def _onchange_product(self):
        self.state = 'draft'
        self.approve_by = False
        self.approve_date_time = False


class LocalChargeLine(models.Model):
    _name = 'freight.local.charge.line'
    _description = 'Local Charge Line'

    local_charge_id = fields.Many2one('freight.local.charge', string='Local Charge', required=True, ondelete='cascade',
                                      index=True, copy=False)

    product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    price = fields.Float(string='Selling Price', digits=(12, 2), track_visibility='onchange')
    cost_price = fields.Float(string='Cost Price', digits=(12, 2), track_visibility='onchange')

    @api.multi
    def write(self, vals):
        res = super(LocalChargeLine, self).write(vals)
        self.local_charge_id.state = 'draft'
        return res
