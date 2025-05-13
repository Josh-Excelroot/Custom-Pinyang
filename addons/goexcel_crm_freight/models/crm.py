from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class CrmContainerLine(models.Model):
    _name = 'crm.container.line'

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    size_id = fields.Many2one('product.product', 'Container Size')
    quantity = fields.Float('Container Quantity')
    weight = fields.Float('Weight (KG - Cargo Only)')
    lead_id = fields.Many2one('crm.lead')
    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    commodity_id = fields.Many2one('crm.commodity')
    commodity1_id = fields.Many2one('freight.commodity1',string="Commodity", track_visibility="onchange")
    service_id = fields.Many2one('crm.service',track_visibility="onchange")

    container_line_ids = fields.One2many('crm.container.line', 'lead_id')

    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')],track_visibility="onchange")

    # FCL Fields
    container_size_id = fields.Many2one('product.product', compute='_compute_fcl_values',track_visibility="onchange")
    container_qty = fields.Float(compute='_compute_fcl_values',track_visibility="onchange")
    teus = fields.Float('TEUS', compute='_compute_fcl_values',track_visibility="onchange")

    # @api.depends('container_line_ids')
    def _compute_fcl_values(self):
        for rec in self:
            rec.container_size_id = False
            rec.container_qty = 0
            rec.teus = 0
            if rec.container_line_ids:
                container_product = rec.container_line_ids[0].size_id  # size is technically product
                container_product_name = container_product.name
                total_qty = sum(rec.container_line_ids.mapped('quantity'))
                rec.teus = container_product_name and total_qty * (
                        ('20' in container_product_name and 1) or
                        ('40' in container_product_name and 2) or
                        0
                )
                rec.container_qty = total_qty
                rec.container_size_id = container_product

    # LCL Fields
    lcl_height = fields.Float(
        string="H (M)",
        store=True,
        help="Height in m",
        default="0.00",
        track_visibility="onchange",
        copy=False,
    )
    lcl_width = fields.Float(
        string="W (M)",
        store=True,
        help="Width in m",
        default="0.00",
        track_visibility="onchange",
        copy=False,
    )
    lcl_length = fields.Float(
        string="L (M)",
        store=True,
        help="length in m",
        default="0.00",
        track_visibility="onchange",
        copy=False,
    )
    lcl_weight = fields.Float(
        string="Gross Weight (KG) ",
        store=True,
        help="Weight in KG",
        default="0.00",
        copy=False,
        track_visibility="onchange",
    )
    lcl_quantity = fields.Float(
        string="Qty (Pcs) ",
        store=True,
        help="Quantity in numbers",
        default="1.00",
        track_visibility="onchange",
        copy=False,
    )
    chargeable_weight = fields.Float(
        string="Chargeable Weight", compute="_compute_chargeable_weight", copy=False
    )
    volumetric_weight = fields.Float(
        string="Vol. Weight", compute="_compute_vol_weight", copy=False
    )

    @api.depends("lcl_weight", "lcl_quantity", "volumetric_weight")
    def _compute_chargeable_weight(self):
        for rec in self:
            chargeable_weight = (rec.lcl_weight / 1000) * rec.lcl_quantity
            rec.chargeable_weight = chargeable_weight \
                if chargeable_weight > rec.volumetric_weight and rec.lcl_quantity \
                else rec.volumetric_weight

    @api.depends("lcl_length", "lcl_width", "lcl_height", "lcl_quantity")
    def _compute_vol_weight(self):
        for rec in self:
            rec.volumetric_weight = rec.lcl_quantity * rec.lcl_length * rec.lcl_width * rec.lcl_height

    port_of_loading = fields.Many2one('freight.ports',track_visibility="onchange")
    port_of_loading_country = fields.Many2one('res.country', related='port_of_loading.country_id',track_visibility="onchange")
    port_of_discharge = fields.Many2one('freight.ports',track_visibility="onchange")
    port_of_discharge_country = fields.Many2one('res.country', related='port_of_discharge.country_id',track_visibility="onchange")

    shipment_mode = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')],track_visibility="onchange")
    mode = fields.Selection([('import', 'Import'), ('export', 'Export'), ('local', 'Local')],track_visibility="onchange")
    incoterm = fields.Many2one(
        "freight.incoterm", string="Incoterm", track_visibility="onchange"
    )

    type_of_movement = fields.Selection(
        [('cy-cy', 'CY/CY'), ('cy-cfs', 'CY/CFS'), ('cfs-cfs', 'CFS/CFS'), ('cfs-cy', 'CFS/CY'), ('cy-ramp', 'CY-RAMP'),
         ('cy-sd', 'CY-SD')],
        string='Type Of Movement', track_visibility='onchange')
    place_of_delivery = fields.Char(string='Place of Delivery', track_visibility='onchange')


class CrmCommodity(models.Model):
    _name = 'crm.commodity'
    _description = 'CRM Commodity'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})
    full_name = fields.Char(translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CrmService(models.Model):
    _name = 'crm.service'
    _description = 'CRM Commodity'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})
    full_name = fields.Char(translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]
