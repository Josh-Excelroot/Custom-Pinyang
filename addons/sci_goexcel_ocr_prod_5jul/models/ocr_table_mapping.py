from odoo import models, fields, api
from odoo.exceptions import Warning


class OCRTableMapping(models.Model):
    _name = 'ocr.table.mapping'
    _description = 'OCR Table Mapping'

    sequence = fields.Integer(string="sequence")
    name = fields.Char(string='Name')
    type = fields.Selection([('default', 'Default'),
                             ('payment_term', 'Payment Term'),
                             ('currency', 'Currency'),
                             ('product', 'Product'),
                             ('partner', 'Partner'),
                             ('pol', 'Port of Loading'),
                             ], default='default', string="Type")
    mapping_line_ids = fields.One2many('ocr.table.mapping.line', 'line_id', string="Mapping Line", copy=True,
                                       auto_join=True)


class OCRTableMappingLine(models.Model):
    _name = 'ocr.table.mapping.line'
    _description = 'OCR Table Mapping Line'

    sequence = fields.Integer(string="sequence")
    line_id = fields.Many2one('ocr.table.mapping', string='Mapping', required=True, ondelete='cascade',
                              index=True, copy=False)
    name = fields.Char(string='Name')
    category = fields.Char(string='Category')
    type = fields.Selection([('label', 'Label'),
                             ('value', 'Value')], default='label', string="Type")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    currency = fields.Many2one('res.currency', string='Currency')
    product_id = fields.Many2one('product.product', string='Product')
    direction = fields.Selection([("import", "Import"), ("export", "Export")], default="export", string="Direction")
    container_size = fields.Selection([("20", "20"), ("40", "40")], default="40", string="Container Size")
    partner_id = fields.Many2one('res.partner', string='Partner')
    port_of_loading_id = fields.Many2one('freight.ports', string='Port of Loading')
    user_id = fields.Many2one('res.users', string='User')
    keyword = fields.Char(string='Keyword')
    company_id = fields.Many2one('res.company')

    @api.model
    def create(self, value):
        header = self.env['ocr.table.mapping'].browse(value.get("line_id"))
        value.update({'category': header.name,
                      'name': value.get("keyword"),
                      })
        return super(OCRTableMappingLine, self).create(value)

    def write(self, value):
        if value.get("keyword"):
            value.update({'name': value.get("keyword")})
        res = super(OCRTableMappingLine, self).write(value)
        return res
"""
class OCRDateFormat(models.Model):
    _name = 'ocr.date.format'
    _description = 'OCR Date Format'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    date_format = fields.Char(string='Date Format')

    @api.onchange('date_format')
    def _onchange_date_format(self):
        self.name = self.date_format
"""


class OCRPartnerTemplate(models.Model):
    _name = 'ocr.partner.template'
    _description = 'OCR Partner Template'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    merge_line_item = fields.Boolean('Merge Line Item')

    page_segmentation_modes_value = fields.Char(string='Page Segmentation Modes')
    density_value = fields.Char(string='Density')

    date_format = fields.Char(string='Date Format')
    reference_pattern = fields.Char(string='Reference Pattern', help="")
    bl_no_pattern = fields.Char(string='BL No. Pattern', help="")
    exchange_rate_pattern = fields.Char(string='Exchange Rate Pattern', help="NEXT LINE; LAST")

    date_template_label = fields.Many2one('ocr.table.mapping.line', string='Date')
    due_date_template_label = fields.Many2one('ocr.table.mapping.line', string='Due Date')
    reference_template_label = fields.Many2one('ocr.table.mapping.line', string='Reference')
    debit_note_template_label = fields.Many2one('ocr.table.mapping.line', string='Debit Note')

    bl_no_template_label = fields.Many2one('ocr.table.mapping.line', string='BL No')
    exchange_rate_template_label = fields.Many2one('ocr.table.mapping.line', string='Exchange Rate')

    payment_term_template_label = fields.Many2one('ocr.table.mapping.line', string='Payment Term')
    currency_template_label = fields.Many2one('ocr.table.mapping.line', string='Currency')
    pol_template_label = fields.Many2one('ocr.table.mapping.line', string='POL')

    product_section_start = fields.Char(string='Product Section Start')
    product_section_end = fields.Char(string='Product Section End')
    line_item_pattern = fields.Char(string='Line Item Pattern',
                                    help="NIL - None; QTY - Quantity; RTE – Conversion Rate; "
                                         "PFC – Unit Price (Foreign Currency); UPI – Unit Price; "
                                         "TOTAL - Total")
    x2nd_line_item_pattern = fields.Char(string='2nd Line Item Pattern')
    line_item_pattern_with_exchange_rate = fields.Char(string='Line Item Pattern With Exchange Rate')
    with_exchange_rate = fields.Boolean(string="With Exchange Rate")
    complex_line = fields.Boolean(string="Complex Line")
    complex_line_pattern = fields.Char(string='Complex Line Pattern')

    pol_pattern = fields.Char(string='POL Pattern')

    #container_template_label = fields.Many2one('ocr.table.mapping.line', string='Container')
    #container_pattern = fields.Char(string='Container Pattern')

    multi_page_check = fields.Boolean("With Multi Page")
    multi_page_count = fields.Integer("Multi Page Count")

    container_section_start = fields.Char(string='Container Section Start')
    container_section_end = fields.Char(string='Container Section End')

    container_inline_product = fields.Boolean("Container Inline Product")
    container_inline_product_pattern = fields.Char(string='Container Inline Product Pattern')


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.name = self.partner_id.name
        if self.partner_id:
            partner = self.env['res.partner'].browse(self.partner_id.id)
            partner.write({"ocr_partner_template": self._origin.id})