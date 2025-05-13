from odoo import models, fields, api
from odoo.exceptions import Warning


class OCRTableMapping(models.Model):
    _name = 'ocr.table.mapping.expense'
    _description = 'OCR Table Mapping'

    sequence = fields.Integer(string="sequence")
    name = fields.Char(string='Name')
    type = fields.Selection([('shop_name', 'Shop Name'),
                             ('date', 'Date'),
                             ('tax', 'Tax'),
                             ('currency', 'Currency Type'),
                             ('total', 'Total Amount'),
                             ], default='shop_name', string="Type")
    mapping_line_ids = fields.One2many('ocr.table.mapping.line.expense', 'line_id', string="Mapping Line", copy=True,
                                       auto_join=True)

    date_format = fields.Selection([('year_month_day', 'YYYY/MM/DD'),
                                    ('month_day_year', 'MM/DD/YYYY'),
                                    ('day_month_year', 'DD/MM/YYYY')], string="Date Format")


class OCRTableMappingLine(models.Model):
    _name = 'ocr.table.mapping.line.expense'
    _description = 'OCR Table Mapping Line'

    sequence = fields.Integer(string="sequence")
    line_id = fields.Many2one('ocr.table.mapping.expense', string='Mapping', required=True, ondelete='cascade',
                              index=True, copy=False)



    name = fields.Char(string='Name')
    category = fields.Char(string='Category')
    type_c = fields.Selection([('label', 'Label'),
                             ], default='label', string="Type")

    # type_d = fields.Selection([('shop_name', 'Shop Name'),
    #                            ('date', 'Date'),
    #                            ('currency', 'Currency'),
    #                            ('total', 'Total Amount'),
    #                            ('currency_type', 'Currency Type'),
    #                            ], default='shop_name', related='line_id.type')


    user_id = fields.Many2one('res.users', string='User')
    keyword = fields.Char(string='Keyword')

    @api.model
    def create(self, value):
        header = self.env['ocr.table.mapping.expense'].browse(value.get("line_id"))
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

