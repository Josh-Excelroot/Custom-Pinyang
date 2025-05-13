# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    unece_type_id = fields.Many2one(
        'unece.code.list', string='UNECE Tax Type',
        domain=[('type', '=', 'tax_type')], ondelete='restrict',
        help="Select the Tax Type Code of the official "
        "nomenclature of the United Nations Economic "
        "Commission for Europe (UNECE), DataElement 5153",
        default = lambda self: self.env.ref('account_tax_unece.tax_type_sale').id,
        compute='_compute_unece_type_id',
    )
    unece_type_code = fields.Char(
        related='unece_type_id.code', store=True, readonly=True,
        string='UNECE Type Code')
    unece_categ_id = fields.Many2one(
        'unece.code.list', string='Tax Category',
        domain=[('type', '=', 'tax_categ')], ondelete='restrict',
        help="Select the Tax Category Code ")
    unece_categ_code = fields.Char(
        related='unece_categ_id.code', store=True, readonly=True,
        string='UNECE Category Code')
    unece_due_date_id = fields.Many2one(
        'unece.code.list', string='UNECE Due Date',
        domain=[('type', '=', 'date')], ondelete='restrict',
        help="Select the due date of that tax from the official "
        "nomenclature of the United Nations Economic "
        "Commission for Europe (UNECE), DataElement 2005. For a "
        "sale VAT tax, it is the date on which that VAT is due to the "
        "fiscal administration. For a purchase VAT tax, it is the date "
        "on which that VAT can be deducted.")
    unece_due_date_code = fields.Char(
        related='unece_due_date_id.code', store=True, readonly=True,
        string='UNECE Due Date Code')

    @api.depends('unece_type_id')
    def _compute_unece_type_id(self):
        default_unece_type = self.env['unece.code.list'].search([('type', '=', 'tax_type'), ('code', '=', '02')],
                                                                limit=1)
        for record in self:
            if not record.unece_type_id and default_unece_type:
                record.unece_type_id = default_unece_type


