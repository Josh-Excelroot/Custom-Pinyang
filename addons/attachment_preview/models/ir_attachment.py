# Copyright 2014 Therp BV (<http://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    def payslip_attachments(self,domain=None,fields=None,args=None):
        record=False
        if domain:
            res = domain[2]
            record=self.search([('res_id','=',int(res)),('res_model','=','hr.payslip')])
            if record:
                # domain = [('id', '=', record[0].id)]
                # record = self.env['ir.attachment'].search_read(domain,
                #                                                fields=['id', 'name', 'datas_fname', 'url', 'mimetype'])
                record.sudo().unlink()


            report_template_id = self.env.ref('l10n_my_payroll_report.hr_payslip_details_report').render_qweb_pdf(
                res)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "payslip.pdf",
                'type': 'binary',
                'datas': data_record,
                'datas_fname': "payslip.pdf",
                'store_fname': 'Payslip',
                'mimetype': 'application/pdf',
                'res_id':res,
                'res_model':'hr.payslip'

            }
            payslip_pdf = self.env['ir.attachment'].with_context(noupload=True).create(ir_values)
            domain = [('id', '=', payslip_pdf.id)]

            record = self.env['ir.attachment'].search_read(domain, fields=['id', 'name', 'datas_fname','url','mimetype'])
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
