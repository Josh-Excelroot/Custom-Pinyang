from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import Warning


class OceanFreightRate(models.Model):
    _name = 'freight.ocean.freight.rate'
    _description = 'Ocean Freight Rate'

    name = fields.Char(string='Name', required=True)
    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange', required=True)

    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange', required=True)
    #port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange', required=True)
    #port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', track_visibility='onchange', required=True)

    port_pair = fields.Many2many('freight.port.pair', string='Port Pair', track_visibility='onchange', required=True)

    @api.multi
    def _get_default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')])
        if currency:
            return currency.id

    currency = fields.Many2one('res.currency', string="Currency", required=True, track_visibility='onchange',
                               default=_get_default_currency)
    #ocean_freight_rate_product_id = fields.Many2one('product.product', string='Ocean Freight Rate Product', track_visibility='onchange')


    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'To Approve'),
        ('active', 'Active')],
        string='Status', index=True, default='draft', track_visibility='always', copy=False)

    approve_by = fields.Many2one(
        'res.users', string='Approve By', track_visibility='always')
    approve_date_time = fields.Datetime(string='Approved Date', track_visibility='always', copy=False)

    @api.one
    def _set_access_for_approve_reject_ocean_freight_rate(self):
        list_of_user = self.env.user.company_id.ocean_freight_rate_approval_user_ids
        if list_of_user:
            if self.env.user in list_of_user:
                self.approve_reject_ocean_freight_rate = True
            else:
                self.approve_reject_ocean_freight_rate = False
        else:
            self.approve_reject_ocean_freight_rate = False

    approve_reject_ocean_freight_rate = fields.Boolean(compute="_set_access_for_approve_reject_ocean_freight_rate")

    @api.multi
    def action_approval(self):
        list_of_approver = []
        action = self.env.ref('sci_goexcel_ocean_freight_rate.action_configure_ocean_freight_rate').id
        list_of_user = self.env.user.company_id.ocean_freight_rate_notification_user_ids
        email_list = [user.email for user in list_of_user]
        if email_list:
            ctx = {}
            ctx['type'] = 'Ocean Freight Rate'
            ctx['email_from'] = self.env.user.email
            ctx['partner_manager_email'] = ','.join([email for email in email_list if email])
            ctx['lang'] = self.env.user.lang
            ctx['partner_name'] = self.env.user.name

            template = self.env.ref(
                'sci_goexcel_ocean_freight_rate.ocean_freight_rate_validate_email_template')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ctx['action_url'] = "{}/web?db={}#id={}&action={}&view_type=form&model=freight.ocean.freight.rate".format(
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

    @api.onchange('name', 'carrier', 'container_product_id', 'port_pair', 'currency')
    def _onchange_product(self):
        self.state = 'draft'
        self.approve_by = False
        self.approve_date_time = False

    ocean_freight_rate_line_ids = fields.One2many('freight.ocean.freight.rate.line', 'ocean_freight_rate_id', string="Line Item")


class OceanFreightRateLine(models.Model):
    _name = 'freight.ocean.freight.rate.line'
    _description = 'Ocean Freight Rate Line'

    ocean_freight_rate_id = fields.Many2one('freight.ocean.freight.rate', string='Ocean Freight Rate', required=True,
                                            ondelete='cascade', index=True, copy=False)

    customer = fields.Many2many('res.partner', string='Customer', track_visibility='onchange')
    rate = fields.Float(string='Rate', digits=(12, 2), track_visibility='onchange')

    cost_rate = fields.Float(string='Cost', digits=(12, 2), track_visibility='onchange')
    margin = fields.Float(string='Margin (%)', digits=(12, 2), default=0.00, track_visibility='onchange', help="Margin Rate")
    valid_from = fields.Date(string='Valid From', track_visibility='onchange', required=True)
    valid_to = fields.Date(string='Valid To', track_visibility='onchange', required=True)
    # CR5 - Canon
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name')
    carrier_booking_no = fields.Char(string='Carrier Booking No')

    @api.multi
    def write(self, vals):
        res = super(OceanFreightRateLine, self).write(vals)
        self.ocean_freight_rate_id.state = 'draft'
        self.ocean_freight_rate_id.approve_by = False
        self.ocean_freight_rate_id.approve_date_time = False
        return res

    @api.onchange('margin')
    def _onchange_margin(self):
        if self.margin!=0.00 and self.cost_rate:
            self.rate = self.cost_rate * ((100 + self.margin)/100)


class PortPair(models.Model):
    _name = 'freight.port.pair'
    _description = 'Port Pair'

    name = fields.Char(string='Name', required=True)
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', required=True)
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', required=True)
