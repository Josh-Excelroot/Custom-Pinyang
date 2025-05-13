from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning
from odoo.tools import float_round

class HaulageCharge(models.Model):
    _name = 'freight.haulage.charge'
    _description = 'Haulage Charge'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Name', required=True)
    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange')
    haulage_charge_line_ids = fields.One2many('freight.haulage.charge.line', 'haulage_charge_id', string="Vendor Line",
                                              copy=True)

    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange', required=True)
    haulage_rates = fields.Float(string='Haulage Rates (RM)', track_visibility='onchange')
    road_tolls = fields.Float(string='ROAD TOLLS (RM)', track_visibility='onchange')
    faf = fields.Float(string='FAF (MYR)', store=True, track_visibility='onchange')
    faf_percent = fields.Float(string='FAF(%)', store=True, digits=(12, 2), track_visibility='onchange')
    is_faf_percent = fields.Boolean(string='Is using FAF(%)', default=True, track_visibility='onchange')
    depot_gate_charges = fields.Float(string='Depot Gate Charges (DGC)', track_visibility='onchange')
    total = fields.Float(string='Total (RM)', track_visibility='onchange')

    one_ton = fields.Integer('1T', track_visibility='onchange')
    three_ton = fields.Integer('3T', track_visibility='onchange')
    three_ton_20 = fields.Integer('3T/20', track_visibility='onchange')
    five_ton = fields.Integer('5T', track_visibility='onchange')

    currency = fields.Many2one('res.currency', string="Currency", required=True, track_visibility='onchange',
                               default=lambda self: self.env.user.company_id.currency_id.id)

    valid_from = fields.Date(string='Valid From', track_visibility='onchange')
    valid_to = fields.Date(string='Valid To', track_visibility='onchange')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'To Approve'),
        ('active', 'Active')],
        string='Status', index=True, default='draft', track_visibility='always', copy=False)

    approve_by = fields.Many2one(
        'res.users', string='Approve By', track_visibility='always')
    approve_date_time = fields.Datetime(string='Approved Date', track_visibility='always', copy=False)

    @api.one
    def _set_access_for_approve_reject_haulage_charge(self):
        list_of_user = self.env.user.company_id.haulage_charge_approval_user_ids
        if list_of_user:
            if self.env.user in list_of_user:
                self.approve_reject_haulage_charge = True
            else:
                self.approve_reject_haulage_charge = False
        else:
            self.approve_reject_haulage_charge = False

    approve_reject_haulage_charge = fields.Boolean(compute="_set_access_for_approve_reject_haulage_charge")

    @api.multi
    def action_approval(self):
        list_of_approver = []
        action = self.env.ref('sci_goexcel_haulage_charge.action_configure_haulage_charge').id
        list_of_user = self.env.user.company_id.haulage_charge_notification_user_ids
        email_list = [user.email for user in list_of_user]
        if email_list:
            ctx = {}
            ctx['type'] = 'Haulage Charge'
            ctx['email_from'] = self.env.user.email
            ctx['partner_manager_email'] = ','.join([email for email in email_list if email])
            ctx['lang'] = self.env.user.lang
            ctx['partner_name'] = self.env.user.name

            template = self.env.ref(
                'sci_goexcel_haulage_charge.haulage_charge_validate_email_template')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ctx['action_url'] = "{}/web?db={}#id={}&action={}&view_type=form&model=freight.haulage.charge".format(
                base_url, self.env.cr.dbname, self.id, action)
            template.with_context(ctx).sudo().send_mail(
                self.id, force_send=True, raise_exception=False)
            self.write({'state': 'approve'})

    @api.multi
    def action_approve(self):
        for op in self:
            op.write({
                'state': 'active',
                'approve_by': self.env.user.id,
                'approve_date_time': datetime.now(),
            })

    @api.multi
    def action_reject(self):
        for op in self:
            op.write({'state': 'draft'})

    @api.onchange('name', 'port_of_loading', 'port_of_discharge','currency','valid_from','valid_to'
                  ,'haulage_rates','road_tolls','depot_gate_charges','one_ton','three_ton','three_ton_20','five_ton')
    def _onchange_product(self):
        self.state = 'draft'
        self.approve_by = False
        self.approve_date_time = False

    @api.onchange('haulage_rates', 'road_tolls', 'faf', 'depot_gate_charges')
    def onchange_total(self):
        if self.haulage_rates:
            self.faf = float_round(self.faf_percent * self.haulage_rates, 2, rounding_method='HALF-UP')
            self.total = self.haulage_rates + self.road_tolls + self.faf + self.depot_gate_charges

    @api.multi
    def action_update_faf_percent(self):
        #wiz_id = self.env['reject.reason'].create({'invoice_id': self.id})
        #if wiz_id:
        return {
            'name': _('New FAF Percent'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.faf.percent',
            'views': [(self.env.ref('sci_goexcel_haulage_charge.faf_percent_view_form').id, 'form')],
            'view_id': self.env.ref('sci_goexcel_haulage_charge.faf_percent_view_form').id,
            'target': 'new',
            #'res_id': wiz_id.id,
        }




class HaulageChargeLine(models.Model):
    _name = 'freight.haulage.charge.line'
    _description = 'Haulage Charge Line'

    haulage_charge_id = fields.Many2one('freight.haulage.charge', string='haulage charge', required=True,
                                            ondelete='cascade', index=True)

    vendor_id = fields.Many2many('res.partner', string='Vendor', track_visibility='onchange')
    rebate_rate = fields.Float(string='Rebate(%)', digits=(12, 2), default=0.00, track_visibility='onchange',
                               help='Either Follow Standard Tariff with Rebate or Different Cost Price from different vendor')
    cost_after_rebate = fields.Float(string='Cost Price After Rebate', digits=(12, 2), track_visibility='onchange',
                             help='Cost Price After Rebate')
    cost_rate = fields.Float(string='Cost Price (Non-Tariff)', digits=(12, 2), track_visibility='onchange',
                             help='Cost Price from Vendor, if different from the Standard')
    valid_from = fields.Date(string='Valid From', track_visibility='onchange')
    valid_to = fields.Date(string='Valid To', track_visibility='onchange')


    @api.onchange('rebate_rate')
    def onchange_rebate_rate(self):
        if self.rebate_rate:
            #print('>>>>>>> Total=', self.haulage_charge_id.total)
            self.cost_after_rebate = float_round(((100 - self.rebate_rate) * self.haulage_charge_id.total / 100),
                                                 2, rounding_method='HALF-UP')
            #print('>>>>>>> Cost After Rebate=', self.cost_after_rebate)



    # @api.multi
    # def write(self, vals):
    #     res = super(OceanFreightRateLine, self).write(vals)
    #     self.ocean_freight_rate_id.state = 'draft'
    #     self.ocean_freight_rate_id.approve_by = False
    #     self.ocean_freight_rate_id.approve_date_time = False
    #     return res

    # @api.onchange('margin')
    # def _onchange_margin(self):
    #     if self.margin!=0.00 and self.cost_rate:
    #         self.rate = self.cost_rate * ((100 + self.margin)/100)


