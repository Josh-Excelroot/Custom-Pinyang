# Copyright 2014 Therp BV (<http://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# id="preview_report_invoice_view"
import collections
import logging
import mimetypes
import os.path

from odoo import models, api,fields
import base64
import logging
import mimetypes
_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # url_drive = fields.Char(string="Url",compute='set_url_attachment',store=True)
    #
    # @api.depends('url')
    # def set_url_attachment(self):
    #     for rec in self:
    #         rec.url_drive = rec.url
    @api.model
    def invoice_attachments(self, domain=None, fields=None, args=None):
        # record = self.search([('res_id', '=', domain[2]), ('res_model', '=', 'account.invoice')])
        # record.unlink()
        # Yulia 14032025 fixed error logic
        config_invoice_preview = self.env['ir.config_parameter'].sudo().get_param('account.invoice_preview_field')
        config_vendor_preview = self.env['ir.config_parameter'].sudo().get_param('account.vendor_preview_field')
        if not config_invoice_preview and not config_vendor_preview:
            return []

        record = False
        if record:
            domain = [('id', '=', record[0].id)]
            record = self.env['ir.attachment'].search_read(domain,
                                                           fields=['id', 'name', 'datas_fname', 'url', 'mimetype'])

        else:
            report_template_id = self.env.ref('account.account_invoices').render_qweb_pdf(
                domain[2])
            data_record = base64.b64encode(report_template_id[0])
            if domain[2]:
                config = self.env['res.config.settings'].sudo().search([], limit=1)
                invoice_id = self.env['account.invoice'].search([('id', '=', domain[2])])
                show_attachment = invoice_id.show_attachment
                if invoice_id.type in ['out_invoice', 'out_refund']:
                    config_invoice_preview = self.env['ir.config_parameter'].sudo().get_param(
                        'account.invoice_preview_field')
                    if config_invoice_preview == 'True':
                        if invoice_id.state in ['approve', 'open', 'paid', 'in_payment']:
                            ir_values = {
                                'name': "account_invoice.pdf",
                                'type': 'binary',
                                'datas': data_record,
                                'datas_fname': "account_invoice.pdf",
                                'store_fname': 'Invoice',
                                'mimetype': 'application/pdf',
                                'res_id': domain[2],
                                'res_model': 'account.invoice'
                            }
                            payslip_pdf = self.env['ir.attachment'].create(ir_values)
                            domain = [('id', '=', payslip_pdf.id)]
                            record = self.env['ir.attachment'].search_read(domain,
                                                                           fields=['id', 'name', 'datas_fname', 'url',
                                                                                   'mimetype'])
                if invoice_id.type in ['in_invoice', 'in_refund']:
                    config_vendor_preview = self.env['ir.config_parameter'].sudo().get_param(
                        'account.vendor_preview_field')
                    if config_vendor_preview == 'True' or show_attachment:
                        if invoice_id.state in ['approve', 'open', 'paid', 'in_payment']:
                            ir_values = {
                                'name': "account_invoice.pdf",
                                'type': 'binary',
                                'datas': data_record,
                                'datas_fname': "account_invoice.pdf",
                                'store_fname': 'Invoice',
                                'mimetype': 'application/pdf',
                                'res_id': domain[2],
                                'res_model': 'account.invoice'
                            }
                            payslip_pdf = self.env['ir.attachment'].create(ir_values)
                            domain = [('id', '=', payslip_pdf.id)]
                            record = self.env['ir.attachment'].search_read(domain,
                                                                           fields=['id', 'name', 'datas_fname', 'url',
                                                                                   'mimetype'])

        return record




    @api.model
    def get_binary_extension(self, model, ids, binary_field,
                             filename_field=None):
        result = {}
        ids_to_browse = ids if isinstance(ids, collections.Iterable) else [ids]

        # First pass: load fields in bin_size mode to avoid loading big files
        #  unnecessarily.
        if filename_field:
            for this in self.env[model].with_context(
                    bin_size=True).browse(ids_to_browse):
                #kashif 2nov23: add condition to work only or ir attachemnt model
                if not this.id or not model == 'ir.attachment':
                    result[this.id] = False
                    continue
                extension = ''
                if this[filename_field]:
                    filename, extension = os.path.splitext(
                        this[filename_field])
                if (this[binary_field] or this['store_fname']) and extension:
                    result[this.id] = extension
                    _logger.debug('Got extension %s from filename %s',
                                  extension, this[filename_field])
        # Second pass for all attachments which have to be loaded fully
        #  to get the extension from the content
        ids_to_browse = [_id for _id in ids_to_browse if _id not in result]
        if model == 'ir.attachment':
            for this in self.env[model].with_context(
                    bin_size=True).browse(ids_to_browse):
                if not this[binary_field] and this.url == False :
                    result[this.id] = False
                    continue
                try:
                    import magic
                    if model == self._name and binary_field == 'datas'\
                            and this.store_fname:
                        mimetype = magic.from_file(
                            this._full_path(this.store_fname), mime=True)
                        _logger.debug('Magic determined mimetype %s from file %s',
                                      mimetype, this.store_fname)
                    elif this.url == False:
                        mimetype = magic.from_buffer(
                            this[binary_field], mime=True)
                        _logger.debug('Magic determined mimetype %s from buffer',
                                      mimetype)
                    elif this.url:
                        mimetype =  this.mimetype
                except ImportError:
                    (mimetype, encoding) = mimetypes.guess_type(
                        'data:;base64,' + this[binary_field], strict=False)
                    _logger.debug('Mimetypes guessed type %s from buffer',
                                  mimetype)
                if this.url ==  False:
                    extension = mimetypes.guess_extension(
                        mimetype.split(';')[0], strict=False)
                else:
                    extension = '.pdf'
                result[this.id] = extension
        for _id in result:
            result[_id] = (result[_id] or '').lstrip('.').lower()
        if filename_field:
            return result if isinstance(ids, collections.Iterable) else result[ids]
        else:
            return []

    @api.model
    def get_attachment_extension(self, ids):
        return self.get_binary_extension(
            self._name, ids, 'datas', 'datas_fname')
