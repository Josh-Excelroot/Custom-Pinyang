##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import tempfile
import base64
import shutil
import os
import logging
import pytesseract
import re
import dateutil.parser as dparser
from datetime import datetime
from odoo.tools import float_round
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from PIL import Image
import PyPDF2

class InvoiceWizardAttachment(models.TransientModel):
    _name = 'invoice.wizard.attachment'

    read_invoice_id = fields.Many2one('read.invoice.wizard','Read Invoice')
    import_invoice_id = fields.Many2one('import.invoice.wizard','Read Invoice')
    color = fields.Integer(string='Color Index')
    filename = fields.Char("File name")
    image_attachment = fields.Binary("Image Attachment")


class ReadInvoiceWizard(models.TransientModel):
    _name = 'read.invoice.wizard'

    attachment_type = fields.Selection(selection=[('pdf', 'Pdf'),
                                                  ('image', 'Image')],
                                       string='Attachment Type',
                                       default='pdf')
    pdf_attachment = fields.Binary("Vendor Invoice")
    filename = fields.Char("File name")
    currency_id = fields.Many2one('res.currency', 'Attached Invoice Currency',
                                  help='Select Attached Invoice Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    invoice_type = fields.Selection(selection=[('customer', 'Customer'),
                                               ('supplier', 'Supplier')],
                                    string='Invoice Type', default='supplier')

    attachment_ids = fields.One2many('invoice.wizard.attachment',
                                     'read_invoice_id',
                                     string='Image Attachment')

    @api.model
    def _get_default_language(self):
        language = self.env['res.lang'].search([('name', '=', 'English')])
        return language

    language = fields.Many2one('res.lang', string="Language", default=_get_default_language)

    def check_pdf_file(self):
        if self.pdf_attachment:
            filename = self.filename.rsplit('.')
            #TS bug - some pdf file name come with PDF
            if filename and filename[1] != 'pdf' and filename[1] != 'PDF':
                raise UserError(_('You can attach only pdf file.'))

    def get_booking_rec_from_carrier_booking(self, carrier_booking_no):
        return 'TEST_BOOKING_NO'
        if carrier_booking_no:
            booking = self.env['freight.booking'].search([('carrier_booking_no', '=', carrier_booking_no)], limit=1)
            if booking:
                return booking.display_name
        raise UserError('Please make sure that the Carrier Booking No/BL No is in the Booking Job.')

    @api.multi
    def read_invoice(self):
        invoice_obj = self.env['account.invoice']
        ir_data_obj = self.env['ir.model.data']
        directory_name = tempfile.mkdtemp(suffix='image2txt')
        ctx = dict(self._context)

        line_list = []
        image_list = []

        try:
            self.check_pdf_file()
            file_name = directory_name + "/temppdf"
            new_file = open(file_name, 'wb')
            directory_name_new = tempfile.mkdtemp(suffix='tempimagenew')
            directory_text = tempfile.mkdtemp(suffix='temptext')
            content = base64.b64decode(self.pdf_attachment)
            new_file.write(content)
            new_file.close()

            # Call Split PDF function
            # pdf_list = invoice_obj.split_pdf(file_name, 0, 1)
            pdf_list = [r'E:\odoo\Useful\temppdf11mscmyr']
            # pdf_list = [r'E:\odoo\Useful\temppdf11yml']
            # pdf_list = [r'E:\odoo\Useful\temppdf11sealand']
            # pdf_list = [r'E:\odoo\Useful\temppdf11maersk']
            # Get First Page of PDF Only
            first_page_only = pdf_list[0]
            # Get Text in PDF
            invoice_obj.get_text(first_page_only, directory_text, False, False)
            text_file = open(first_page_only + '.txt', 'r', encoding="utf8")
            # Get Partner for first loop
            partner_template, partner = invoice_obj.get_partner(text_file)
            has_error = False
            error_message = ''
            if partner_template:
                merge_line_item = partner_template.merge_line_item
                psm_value = partner_template.page_segmentation_modes_value
                density_value = partner_template.density_value
                if partner_template.multi_page_check:
                    line_list = []
                    for i in pdf_list:
                        invoice_obj.get_text(i, directory_text, density_value, psm_value)
                        text_file_dic = (i + '.txt')
                        text_file = open(i + '.txt', 'r', encoding="utf8")
                        partner_template, partner = invoice_obj.get_partner(text_file)

                        if partner and partner_template.name in ['MEDITERRANEAN SHIPPING COMPANY (IDR)', 'MEDITERRANEAN SHIPPING COMPANY (USD)']:
                            if i == pdf_list[0]:
                                direction = 'import'
                                due_date, pol = False, False
                                pol_found, terms_found, direction_found = False, False, False
                                currency, exchange_rate_header, payment_term = False, False, False
                                container_size = '40'

                                bl_no = invoice_obj.get_bl_no(partner_template, text_file_dic)
                                bl_no = self.get_booking_rec_from_carrier_booking(bl_no)
                                curr_text = 'USD' if 'USD' in partner_template.name else 'IDR'
                                currency = self.env['res.currency'].search([('name', '=', curr_text)])
                                reference = invoice_obj.get_invoice_no(partner_template, text_file_dic)
                                date = invoice_obj.get_invoice_date(partner_template, text_file_dic)

                                text_file = open(text_file_dic, 'r', encoding="utf8")
                                for line in text_file:
                                    # text_file = open(text_file_dic, 'r', encoding="utf8")
                                    # text = text_file.read()
                                    if 'Export Invoice' in line and not direction_found:
                                        direction = 'export'

                                    if 'Cntr Details ' in line:
                                        if "40'" in line or '40HC' in line:
                                            container_size = '40'
                                        else:
                                            container_size = '20'

                                    if 'POL' in line and not pol_found:
                                        for pol_template in self.env['ocr.table.mapping.line'].search(
                                                [('line_id.name', '=', 'PORT OF LOADING'), ('type', '=', 'value')]):
                                            if pol_template.keyword.upper() in line.upper():
                                                pol = pol_template.port_of_loading_id.id
                                                # if pol_template.port_of_loading_id.country_id.name != 'MALAYSIA':
                                                #     direction = 'import'
                                                pol_found = True
                                                break

                                    if 'Terms' in line and not terms_found:
                                        for payment_term_mapping in self.env['ocr.table.mapping.line'].search(
                                                [('line_id.name', '=', 'PAYMENT TERM'), ('type', '=', 'value'), ('company_id', '=', self.env.user.company_id.id)]):
                                            if payment_term_mapping.keyword.upper() in line.upper():
                                                payment_term = payment_term_mapping.payment_term_id.id
                                                terms_found = True
                                                break

                                    # text_file = open(text_file_dic, 'r', encoding="utf8")
                                    # for line in text_file:
                                    #     ...
                                line_list = invoice_obj.get_line_list(partner_template, text_file_dic, currency, False, direction, container_size)

                        elif partner and partner_template.name == 'MEDITERRANEAN SHIPPING COMPANY (M) SDN BHD':
                            if i == pdf_list[0]:
                                invoice_basic_info_text_found, invoice_basic_info_found = False, False
                                port_of_loading_info_text_found, port_of_loading_info_found = False, False
                                direction = 'export'
                                reference, date, due_date, pol, bl_no = False, False, False, False, False
                                exchange_rate_header, payment_term = False, False
                                currency = self.env.user.company_id.currency_id

                                for line in text_file_dic:
                                    text_file = open(text_file_dic, 'r', encoding="utf8")
                                    text = text_file.read()
                                    container = re.findall(r'Container/Size Type\n(.*?)\nCharge', text, re.DOTALL)[0].split('/')
                                    container_name = container[0]
                                    # container_size = '20'
                                    container_size = ('20' in container[1] and '20') or '40'

                                    text_file = open(text_file_dic, 'r', encoding="utf8")
                                    for line in text_file:
                                        if "Invoice no: Invoice Date: Due date" in line and not invoice_basic_info_text_found:
                                            invoice_basic_info_text_found = True
                                            continue
                                        if invoice_basic_info_text_found and not invoice_basic_info_found and len(line)>3:
                                            line = line.replace('2/-','27-').replace('1/-','17-')
                                            splitted = line.strip().split()
                                            reference = splitted[1]
                                            date = splitted[2]
                                            try:
                                                date = datetime.strptime(date, '%d-%b-%Y')
                                            except ValueError:
                                                reference = splitted[1] + splitted[2]
                                                date = splitted[3]
                                                date = datetime.strptime(date, '%d-%b-%Y')
                                            due_date = splitted[-1]
                                            due_date = datetime.strptime(due_date, '%d-%b-%Y')
                                            invoice_basic_info_found= True
                                        if "Vessel : Voy : POL: POD: B/L No:" in line and not port_of_loading_info_text_found:
                                            port_of_loading_info_text_found = True
                                            continue
                                        if port_of_loading_info_text_found and not port_of_loading_info_found and len(line)>3:
                                            bl_no = line.split()[-1]
                                            for pol_template in self.env['ocr.table.mapping.line'].search([('line_id.name','=','PORT OF LOADING'),('type','=','value')]):
                                                if pol_template.keyword.upper() in line.upper():
                                                    pol = pol_template.port_of_loading_id.id
                                                    if pol_template.port_of_loading_id.country_id.name != 'MALAYSIA':
                                                        direction = 'import'
                                                    port_of_loading_info_found = True
                                                    bl_no = self.get_booking_rec_from_carrier_booking(bl_no)

                            if i == pdf_list[-1]:
                                partner_template.product_section_end = 'Total in Word'
                            line_list.extend(invoice_obj.get_line_list(partner_template, text_file_dic, currency, exchange_rate_header, direction, container_size))
                            partner_template.product_section_end == 'Continued In Next Paae'


                        elif partner_template and partner:
                            merge_line_item = partner_template.merge_line_item
                            reference = invoice_obj.get_invoice_no(partner_template, text_file_dic)
                            bl_no = invoice_obj.get_bl_no(partner_template, text_file_dic)

                            if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                                if reference:
                                    left1, right1 = reference[:3], reference[3:]
                                    right1 = right1.replace("O", "0")
                                    reference = left1 + right1
                                if bl_no:
                                    left2, right2 = bl_no[:3], bl_no[3:]
                                    right2 = right2.replace("O", "0")
                                    bl_no = left2 + right2
                            pol, direction, partner_template, partner = invoice_obj.get_pol(partner_template, text_file_dic, partner)
                            if not partner_template:
                                raise Warning(_("No Partner Template on Partner3."))
                            date = invoice_obj.get_invoice_date(partner_template, text_file_dic)
                            due_date = invoice_obj.get_due_date(partner_template, text_file_dic, date)
                            payment_term = invoice_obj.get_payment_term(partner_template, text_file_dic, date, due_date)
                            currency, exchange_rate_header = invoice_obj.get_currency(partner_template, text_file_dic)
                            container_list, container_size = invoice_obj.get_container_list(partner_template, text_file_dic)
                            line_list = invoice_obj.get_line_list(partner_template, text_file_dic, currency, exchange_rate_header, direction, container_size)
                        else:
                            raise Warning(_("No Partner Template on Partner4."))
                else:
                    if partner_template.multi_page_count > 0:
                        pdf_list = invoice_obj.split_pdf(file_name, 0, partner_template.multi_page_count)
                        final_file = pdf_list[0]
                    else:
                        final_file = file_name
                    invoice_obj.get_text(final_file, directory_text, density_value, psm_value)
                    text_command = ",'r', encoding='utf8'"
                    text_file_dic = (final_file + '.txt')
                    reference = invoice_obj.get_invoice_no(partner_template, text_file_dic)
                    bl_no = invoice_obj.get_bl_no(partner_template, text_file_dic)
                    if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                        if reference:
                            left1, right1 = reference[:3], reference[3:]
                            right1 = right1.replace("O", "0")
                            reference = left1 + right1
                        if bl_no:
                            left2, right2 = bl_no[:3], bl_no[3:]
                            right2 = right2.replace("O", "0")
                            bl_no = left2 + right2
                    pol, direction, partner_template, partner = invoice_obj.get_pol(partner_template, text_file_dic, partner)
                    # TS 1/5/2023 - check the BL No (Carrier Booking No) in the job
                    self.validate_bl_no(bl_no, partner)
                    if not partner_template:
                        raise Warning(_("No Partner Template on Partner2."))
                    merge_line_item = partner_template.merge_line_item
                    date = invoice_obj.get_invoice_date(partner_template, text_file_dic)
                    due_date = invoice_obj.get_due_date(partner_template, text_file_dic,date)
                    payment_term = invoice_obj.get_payment_term(partner_template, text_file_dic, date, due_date)
                    currency, exchange_rate_header = invoice_obj.get_currency(partner_template, text_file_dic)
                    container_list, container_size = invoice_obj.get_container_list(partner_template, text_file_dic)
                    line_list = invoice_obj.get_line_list(partner_template, text_file_dic, currency, exchange_rate_header, direction, container_size)
                    if partner_template.name == "WAN HAI LINES (M) SDN. BHD.":
                        line_list = invoice_obj.update_list_wanhai(partner_template, text_file_dic, line_list, currency, exchange_rate_header)

            else:
                raise Warning(_("No Partner Template on Partner1."))
            import wand.image as image
            with image.Image(filename=file_name, resolution=200) as img:
                img.compression_quality = 99
                img.save(filename=directory_name_new + '/page.jpg')
            dirs = os.listdir(directory_name_new)
            for pdf_to_image_file in dirs:
                with open(directory_name_new + '/' + pdf_to_image_file,
                          "rb") as imagefile:
                    str_new = base64.b64encode(imagefile.read())
                    image_list.append((0, 0,
                                       {
                                           'image_attachment':
                                               str_new or False
                                       }))
                    image_list.reverse()
            self.attachment_ids = image_list
            img_attach = self.attachment_ids and \
                self.attachment_ids[0].image_attachment
            # shutil.rmtree(directory_name_new)
            # shutil.rmtree(directory_text)

            import_form_id = ir_data_obj.get_object_reference(
                'sci_goexcel_ocr', 'import_invoice_wizard_form')[1]
            company_id = self._context.get(
                'company_id', self.env.user.company_id.id)

            journal_domain = [('type', '=', 'purchase'), ('company_id', '=', company_id)]
            type_invoice = 'in_invoice'
            journal_id = self.env['account.journal'].search(
                journal_domain, limit=1)

            attachment = self.env['ir.attachment'].create({
                'active': True,
                'name': self.filename,
                'datas': self.pdf_attachment,
                'datas_fname': self.filename,
                'type': 'binary',
            })

            if not partner:
                ctx.update({
                    'default_invoice_line_ids': line_list,
                    'default_image_attachment': img_attach,
                    'default_attachment_ids': image_list,
                    'invoice_type': self.invoice_type,
                    'default_journal_id': journal_id and journal_id.id or
                    False,
                    'default_type': type_invoice,
                    'default_filename': attachment.id,
                })
            else:
                if not currency:
                    currency = self.env.user.company_id.currency_id.id
                ctx.update({
                    'default_partner_id': partner.id,
                    'default_reference': reference,
                    'default_bl_no': bl_no,
                    'default_date': date,
                    'default_payment_term': payment_term,
                    'default_due_date': due_date,
                    'default_currency': (type(currency) == int and currency) or currency.id,
                    'default_invoice_line_ids': line_list,
                    'default_image_attachment': img_attach,
                    'default_attachment_ids': image_list,
                    'invoice_type': self.invoice_type,
                    'default_journal_id': journal_id and journal_id.id or False,
                    'default_type': type_invoice,
                    'default_port_of_loading_id': pol,
                    'default_filename': attachment.id,
                    'default_direction': direction,
                    'default_merge_line_item': merge_line_item,
                    'default_has_error': has_error,
                    'default_error_message': error_message,
                })
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'name': _('Invoice Import'),
                'view_mode': 'form',
                'res_model': 'import.invoice.wizard',
                'views': [(import_form_id, 'form')],
                'view_id': import_form_id,
                'target': 'inline',
                'context': ctx,
            }

        finally:
            img_attach = False
            #shutil.rmtree(directory_name)
            #raise Warning(_(con_text))

    # TS 1/5/2023 - check the BL No (Carrier Booking No) in the job
    def validate_bl_no(self, bl_no, partner, is_new=True):
        has_error, error_message, booking, vendor_bill = False, '', False, False
        if bl_no:
            booking = self.env['freight.booking'].search([('carrier_booking_no', '=', bl_no)], limit=1)
            if booking:
                bill_state_domain = (is_new and ['state', 'not in', ['cancel']]) or ['state', 'not in', ['open','in_payment','paid','cancel']]
                # if there is alrdy existing vendor bill with the BL No
                vendor_bill = self.env['account.invoice'].search([('freight_booking', '=', booking.id),
                                                                  ('partner_id', '=', partner.id),
                                                                  ('type', '=', 'in_invoice'),
                                                                  bill_state_domain], limit=1)
                if vendor_bill and is_new:
                    has_error = True
                    error_message = 'There is existing vendor bill %s in the job %s!' % vendor_bill.name \
                                    % booking.booking_no
                elif not vendor_bill and not is_new:
                    has_error = True
                    error_message = 'There is no existing draft vendor bill in the job %s!' % booking.booking_no

            else:
                has_error = True
                error_message = 'BL No is not found in the job!'
        else:
            has_error = True
            error_message = 'BL No cannot be empty'

        # self.has_error=has_error
        # self.error_message = error_message
        return has_error, error_message, booking, vendor_bill


class ImportInvoiceWizard(models.TransientModel):
    _name = 'import.invoice.wizard'

    partner_id = fields.Many2one('res.partner', "Partner")
    partner = fields.Char("Partner")
    image_attachment = fields.Binary("Image Attachment")
    invoice_line_ids = fields.One2many('import.invoice.line.wizard',
                                       'invoice_wizard_id', 'Invoice Line')
    new_partner = fields.Boolean('Create New Partner')
    attachment_ids = fields.One2many('invoice.wizard.attachment',
                                     'import_invoice_id',
                                     string='Image Attachment')
    count_image = fields.Integer('Count Image')
    #TS - change the Reference to Vendor Invoice No and Date
    reference = fields.Char(string="Vendor Invoice No")
    date = fields.Date(string='Invoice Date')
    payment_term = fields.Many2one('account.payment.term', string='Payment Term')
    due_date = fields.Date(string='Due Date')
    currency = fields.Many2one('res.currency', string='Currency')
    bl_no = fields.Char("BL No")
    port_of_loading_id = fields.Many2one('freight.ports', string='Port of Loading')
    #TS Add the total
    total_amount = fields.Float(string='Total', compute='_compute_total')
    filename = fields.Char("File name")

    direction = fields.Char(string="Direction")
    container = fields.Char(string="Container")

    merge_line_item = fields.Boolean('Merge Line Item')
    has_error = fields.Boolean(string='Has Error', default=False)
    error_message = fields.Char(string="Error Message")

    @api.one
    @api.depends('invoice_line_ids.line_amount')
    def _compute_total(self):
        # _logger.warning('onchange_pivot_sale_total')
        for service in self.invoice_line_ids:
            if service.line_amount:
                self.total_amount = service.line_amount + self.total_amount

    @api.multi
    def create_partner(self):
        if self._context.get('invoice_type') == 'customer':
            customer = True
            supplier = False
        else:
            customer = False
            supplier = True
        if not self.partner_id:
            partner_rec = self.env['res.partner'].create(
                {
                    'name': self.partner, 'type': "contact",
                    'customer': customer, 'supplier': supplier
                })
            return partner_rec

    @api.multi
    def next_image(self):
        invoice_line_list = [attachment.image_attachment for attachment in
                             self.attachment_ids]
        for rec in self:
            rec.count_image += 1
            if len(invoice_line_list) == rec.count_image:
                rec.count_image = 0
            rec.image_attachment = invoice_line_list[rec.count_image]

    @api.multi
    def previous_image(self):
        invoice_line_list = [attachment.image_attachment for attachment in
                             self.attachment_ids]
        for rec in self:
            rec.count_image -= 1
            if rec.count_image < 0:
                rec.count_image = 0
            rec.image_attachment = invoice_line_list[rec.count_image]

    @api.multi
    def import_invoice(self):
        account_invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']
        form_view_ref = False
        ctx = dict(self._context)
        if ctx.get('invoice_type') == 'customer':
            form_view_ref = self.env.ref(
                'account.invoice_form', False).id
        elif ctx.get('invoice_type') == 'supplier':
            form_view_ref = self.env.ref(
                'account.invoice_supplier_form', False).id
        #TS - add the freight booking reference from the BL no by search carrier booking no
        #booking = False
        freight_booking = self.env['freight.booking'].search([('carrier_booking_no', 'like', self.bl_no)], limit=1)
        if self.new_partner:
            partner_rec = self.with_context(ctx).create_partner()
            ctx.update({
                'default_partner_id': partner_rec.id,
                'default_id': False,
                'default_date_invoice': self.date,
                'default_reference': self.reference,
                'default_payment_term_id': self.payment_term.id or False,
                'default_currency_id': self.currency.id or False,
                'default_date_due': self.due_date,
                'default_freight_booking': freight_booking.id if freight_booking else False,
            })
        else:
            ctx.update({
                'default_partner_id': self.partner_id.id,
                'default_id': False,
                'default_date_invoice': self.date,
                'default_reference': self.reference,
                'default_payment_term_id': self.payment_term.id or False,
                'default_exchange_rate_inverse': 0.000000,
                'default_currency_id': self.currency.id or False,
                'default_date_due': self.due_date,
                'default_freight_booking': freight_booking.id if freight_booking else False,
            })
        invoice_line_list = []
        for invoice_line in self.invoice_line_ids:
            journal = account_invoice_obj._default_journal()
            account_id = invoice_line_obj.with_context({
                'journal_id': journal.id,
                'type': ctx.get('invoice_type') == 'customer' and 'out_invoice'
            })._default_account()
            line_vals = {
                'product_id': invoice_line.product_id.id or False,
                'name': invoice_line.product_id.name or invoice_line.name,
                'quantity': invoice_line.quantity,
                'freight_currency': invoice_line.currency.id,
                'freight_foreign_price': invoice_line.foreign_price,
                'freight_currency_rate': invoice_line.currency_rate,
                'price_unit': invoice_line.price_unit,
                'account_id': account_id,
                'uom_id': invoice_line.product_id.uom_id and invoice_line.product_id.uom_id.id or False,
                'invoice_line_tax_ids': [
                    (6, 0, invoice_line.invoice_line_tax_ids.ids)]
            }
            invoice_line_list.append(line_vals)
            ctx.update({'default_invoice_line_ids': invoice_line_list})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(form_view_ref, 'form')],
            'view_id': form_view_ref,
            'context': ctx,
        }

    @api.multi
    def discard_invoice(self):
        tee_view_ref = self.env.ref('account.invoice_tree', False)
        form_view_ref = self.env.ref('account.invoice_form', False)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'target': 'main',
            'views': [(tee_view_ref.id, 'tree'),
                      (form_view_ref.id, 'form')],
        }

    @api.multi
    def import_invoice1(self):
        has_err, err_msg, freight_booking, vendor_bill = self.env['read.invoice.wizard'].validate_bl_no(self.bl_no, self.partner_id)
        self.has_error = has_err
        if has_err:
            self.error_message = err_msg
            return False

        form_view_ref = self.env.ref('account.invoice_supplier_form', False).id

        account_invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']

        form_view_ref = False
        ctx = dict(self._context)

        if self.new_partner:
            partner_rec = self.with_context(ctx).create_partner()
            account_id_header = False
        else:
            partner_rec = self.partner_id
            if self.partner_id.property_account_payable_id:
                account_id_header = self.partner_id.property_account_payable_id[0].id
            else:
                account_id_header = False

        value = []

        for invoice_line in self.invoice_line_ids:
            account_id = False
            if invoice_line.product_id:
                if invoice_line.product_id.property_account_expense_id:
                    account_id = invoice_line.product_id.property_account_expense_id
                elif invoice_line.product_id.categ_id.property_account_expense_categ_id:
                    account_id = invoice_line.product_id.categ_id.property_account_expense_categ_id
                if account_id:
                    group_product_desc_invoice = self.env['ir.config_parameter'].sudo().get_param(
                        'product_description.group_product_desc_invoice')
                    if group_product_desc_invoice:
                        name1 = " "
                        product_desc = invoice_line.product_id.name
                    else:
                        name1 = invoice_line.product_id.name
                        product_desc = ""
                    found_line_product = False
                    if self.merge_line_item:
                        for i in value:
                            freight_foreign_price = i[2].get('freight_foreign_price')
                            price_unit = i[2].get('price_unit')
                            if invoice_line.product_id.id == i[2].get('product_id'):
                                found_line_product = True
                                freight_foreign_price = freight_foreign_price + invoice_line.foreign_price
                                price_unit = price_unit + invoice_line.price_unit
                                curr_account_id = i[2].get('account_id')
                                curr_product_id = i[2].get('product_id')
                                curr_name = i[2].get('name')
                                curr_product_desc = i[2].get('product_desc')
                                curr_freight_currency = i[2].get('freight_currency')
                                curr_freight_currency_rate = i[2].get('freight_currency_rate')
                                curr_quantity = i[2].get('quantity')
                                curr_uom_id = i[2].get('uom_id')

                                i[2] = {
                                            'account_id': curr_account_id,
                                            'product_id': curr_product_id,
                                            'name': curr_name,
                                            'product_desc': curr_product_desc,
                                            'freight_currency': curr_freight_currency,
                                            'freight_foreign_price': freight_foreign_price,
                                            'freight_currency_rate': curr_freight_currency_rate,
                                            'quantity': curr_quantity,
                                            'price_unit': price_unit,
                                            'uom_id': curr_uom_id,
                                        }

                    if not found_line_product:
                        value.append([0, 0, {
                            'account_id': account_id.id or False,
                            'product_id': invoice_line.product_id.id or False,
                            'name': name1 or '',
                            'product_desc': product_desc or '',
                            'freight_currency': invoice_line.currency.id,
                            'freight_foreign_price': invoice_line.foreign_price,
                            'freight_currency_rate': invoice_line.currency_rate,
                            'quantity': invoice_line.quantity,
                            'price_unit': invoice_line.price_unit,
                            'uom_id': invoice_line.product_id.uom_id and invoice_line.product_id.uom_id.id or False,
                        }])
                else:
                    raise Warning(_("No Account Id in Item."))
        if self.currency:
            currency_id = self.currency.id
        else:
            currency_id = self.env.user.company_id.currency_id.id

        vendor_bill = account_invoice_obj.create({
            'type': 'in_invoice',
            'invoice_line_ids': value,
            'state': 'draft',
            'partner_id': partner_rec.id or False,
            'date_invoice': self.date,
            'reference': self.reference,
            'payment_term_id': self.payment_term.id or False,
            'exchange_rate_inverse': 1.000000,
            'currency_id': currency_id or False,
            'date_due': self.due_date,
            'freight_booking': freight_booking.id if freight_booking else False,
            'origin': freight_booking.booking_no if freight_booking else False,
            'account_id': account_id_header,
            'company_id': self.env.user.company_id.id,
        })
        if self.filename:
            attachment = self.env['ir.attachment'].search([('id', '=', self.filename)])
            attachment.write({
                'res_model': 'account.invoice',
                'res_id': vendor_bill.id,
            })

        if freight_booking:
            if not freight_booking.analytic_account_id:
                values = {
                    'partner_id': freight_booking.customer_name.id,
                    'name': '%s' % freight_booking.booking_no,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                freight_booking.write({'analytic_account_id': analytic_account.id,
                                       })
                account_analytic_id = analytic_account.id
            else:
                account_analytic_id = freight_booking.analytic_account_id.id

            for invoice_line in vendor_bill.invoice_line_ids:
                cost_price = 0
                if invoice_line.freight_foreign_price > 0:
                    cost_price = invoice_line.freight_foreign_price
                else:
                    cost_price = invoice_line.price_unit
                check_booking = False
                for cost_profit_line in freight_booking.cost_profit_ids:
                    if cost_profit_line.product_id == invoice_line.product_id:
                        booking_line_id = cost_profit_line
                        check_booking = True
                        if invoice_line.price_unit and (
                                invoice_line.price_unit > 0 or invoice_line.price_unit < 0):

                            # Vendor Bill
                            if cost_profit_line.vendor_bill_ids:
                                if len(cost_profit_line.vendor_bill_ids) > 1:
                                    total_qty = 0
                                    for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                        account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=', vendor_bill_line.id)])
                                        for invoice_line_item in account_invoice_line:
                                            if (invoice_line_item.product_id == cost_profit_line.product_id) and (invoice_line_item.freight_booking.id == freight_booking.id):
                                                total_qty = total_qty + invoice_line_item.quantity
                                        if not account_invoice_line or len(account_invoice_line) == 0:
                                            total_qty = total_qty + invoice_line.quantity
                                    if total_qty > 0:
                                        cost_profit_line.write(
                                            {
                                                'cost_qty': total_qty or False,
                                                'invoiced': True,
                                                'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                                'vendor_bill_ids': [(4, vendor_bill.id)],
                                            })
                                else:
                                    cost_profit_line.write({
                                        'cost_price': cost_price,
                                        'cost_qty': invoice_line.quantity,
                                        'invoiced': True,
                                        'vendor_id': vendor_bill.partner_id.id,
                                        'vendor_bill_id': vendor_bill.id,
                                        'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                        'vendor_bill_ids': [(4, vendor_bill.id)],
                                        'cost_currency': invoice_line.freight_currency.id,
                                        'cost_currency_rate': invoice_line.freight_currency_rate,
                                    })

                            else:
                                cost_profit_line.write({
                                    'cost_price': cost_price,
                                    'cost_qty': invoice_line.quantity,
                                    'invoiced': True,
                                    'vendor_id': vendor_bill.partner_id.id,
                                    'vendor_bill_id': vendor_bill.id,
                                    'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                    'vendor_bill_ids': [(4, vendor_bill.id)],
                                    'cost_currency': invoice_line.freight_currency.id,
                                    'cost_currency_rate': invoice_line.freight_currency_rate,
                                })
                # if check_booking:
                # If product did not exist
                if not check_booking:
                    values = {
                        'booking_id': freight_booking.id,
                        # Please check
                        'booking_line_id_temp': freight_booking.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.product_id.name,
                        'cost_price': cost_price,
                        'cost_qty': invoice_line.quantity,
                        'invoiced': True,
                        'vendor_id': vendor_bill.partner_id.id,
                        'vendor_bill_id': vendor_bill.id,
                        'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                        'vendor_bill_ids': [(4, vendor_bill.id)],
                        'cost_currency': invoice_line.freight_currency.id,
                        'cost_currency_rate': invoice_line.freight_currency_rate,
                    }
                    booking_line_id = self.env['freight.cost_profit'].sudo().create(values)

                invoice_line.write({
                    'account_analytic_id': account_analytic_id,
                    'booking_line_id': booking_line_id.id,
                    'origin': freight_booking.booking_no,
                    'freight_booking': freight_booking.id,
                    'carrier_booking_no': freight_booking.carrier_booking_no,
                })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(form_view_ref, 'form')],
            'view_id': form_view_ref,
            'res_id': vendor_bill.id or False,
        }

    @api.multi
    def update_invoice_ocr(self):
        has_err, err_msg, freight_booking, vendor_bill = self.env['read.invoice.wizard'].validate_bl_no(self.bl_no, self.partner_id)
        self.has_error = has_err
        if has_err:
            self.error_message = err_msg
            return False

        form_view_ref = self.env.ref('account.invoice_supplier_form', False).id

        value = []

        for invoice_line in self.invoice_line_ids:
            account_id = False
            if invoice_line.product_id:
                if invoice_line.product_id.property_account_expense_id:
                    account_id = invoice_line.product_id.property_account_expense_id
                elif invoice_line.product_id.categ_id.property_account_expense_categ_id:
                    account_id = invoice_line.product_id.categ_id.property_account_expense_categ_id
                if account_id:
                    group_product_desc_invoice = self.env['ir.config_parameter'].sudo().get_param(
                        'product_description.group_product_desc_invoice')
                    if group_product_desc_invoice:
                        name1 = " "
                        product_desc = invoice_line.product_id.name
                    else:
                        name1 = invoice_line.product_id.name
                        product_desc = ""
                    found_line_product = False
                    if self.merge_line_item:
                        for i in value:
                            freight_foreign_price = i[2].get('freight_foreign_price')
                            price_unit = i[2].get('price_unit')
                            if invoice_line.product_id.id == i[2].get('product_id'):
                                found_line_product = True
                                freight_foreign_price = freight_foreign_price + invoice_line.foreign_price
                                price_unit = price_unit + invoice_line.price_unit
                                curr_account_id = i[2].get('account_id')
                                curr_product_id = i[2].get('product_id')
                                curr_name = i[2].get('name')
                                curr_product_desc = i[2].get('product_desc')
                                curr_freight_currency = i[2].get('freight_currency')
                                curr_freight_currency_rate = i[2].get('freight_currency_rate')
                                curr_quantity = i[2].get('quantity')
                                curr_uom_id = i[2].get('uom_id')

                                i[2] = {
                                    'account_id': curr_account_id,
                                    'product_id': curr_product_id,
                                    'name': curr_name,
                                    'product_desc': curr_product_desc,
                                    'freight_currency': curr_freight_currency,
                                    'freight_foreign_price': freight_foreign_price,
                                    'freight_currency_rate': curr_freight_currency_rate,
                                    'quantity': curr_quantity,
                                    'price_unit': price_unit,
                                    'uom_id': curr_uom_id,
                                }

                    if not found_line_product:
                        value.append([0, 0, {
                            'account_id': account_id.id or False,
                            'product_id': invoice_line.product_id.id or False,
                            'name': name1 or '',
                            'product_desc': product_desc or '',
                            'freight_currency': invoice_line.currency.id,
                            'freight_foreign_price': invoice_line.foreign_price,
                            'freight_currency_rate': invoice_line.currency_rate,
                            'quantity': invoice_line.quantity,
                            'price_unit': invoice_line.price_unit,
                            'uom_id': invoice_line.product_id.uom_id and invoice_line.product_id.uom_id.id or False,
                        }])
                else:
                    raise Warning(_("No Account Id in Item."))

        value_temp = [[5,0,0]]
        value_temp.extend(value)
        vendor_bill.invoice_line_ids = value_temp

        if freight_booking:
            for invoice_line in vendor_bill.invoice_line_ids:
                cost_price = 0
                if invoice_line.freight_foreign_price > 0:
                    cost_price = invoice_line.freight_foreign_price
                else:
                    cost_price = invoice_line.price_unit
                check_booking = False
                for cost_profit_line in freight_booking.cost_profit_ids:
                    if cost_profit_line.product_id == invoice_line.product_id:
                        booking_line_id = cost_profit_line
                        check_booking = True
                        if invoice_line.price_unit and (
                                invoice_line.price_unit > 0 or invoice_line.price_unit < 0):

                            # Vendor Bill
                            if cost_profit_line.vendor_bill_ids:
                                if len(cost_profit_line.vendor_bill_ids) > 1:
                                    total_qty = 0
                                    for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                        account_invoice_line = self.env['account.invoice.line'].search(
                                            [('invoice_id', '=', vendor_bill_line.id)])
                                        for invoice_line_item in account_invoice_line:
                                            if (invoice_line_item.product_id == cost_profit_line.product_id) and (
                                                    invoice_line_item.freight_booking.id == freight_booking.id):
                                                total_qty = total_qty + invoice_line_item.quantity
                                        if not account_invoice_line or len(account_invoice_line) == 0:
                                            total_qty = total_qty + invoice_line.quantity
                                    if total_qty > 0:
                                        cost_profit_line.write(
                                            {
                                                'cost_qty': total_qty or False,
                                                'invoiced': True,
                                                'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                                'vendor_bill_ids': [(4, vendor_bill.id)],
                                            })
                                else:
                                    cost_profit_line.write({
                                        'cost_price': cost_price,
                                        'cost_qty': invoice_line.quantity,
                                        'invoiced': True,
                                        'vendor_id': vendor_bill.partner_id.id,
                                        'vendor_bill_id': vendor_bill.id,
                                        'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                        'vendor_bill_ids': [(4, vendor_bill.id)],
                                        'cost_currency': invoice_line.freight_currency.id,
                                        'cost_currency_rate': invoice_line.freight_currency_rate,
                                    })

                            else:
                                cost_profit_line.write({
                                    'cost_price': cost_price,
                                    'cost_qty': invoice_line.quantity,
                                    'invoiced': True,
                                    'vendor_id': vendor_bill.partner_id.id,
                                    'vendor_bill_id': vendor_bill.id,
                                    'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                                    'vendor_bill_ids': [(4, vendor_bill.id)],
                                    'cost_currency': invoice_line.freight_currency.id,
                                    'cost_currency_rate': invoice_line.freight_currency_rate,
                                })
                # if check_booking:
                # If product did not exist
                if not check_booking:
                    values = {
                        'booking_id': freight_booking.id,
                        # Please check
                        'booking_line_id_temp': freight_booking.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.product_id.name,
                        'cost_price': cost_price,
                        'cost_qty': invoice_line.quantity,
                        'invoiced': True,
                        'vendor_id': vendor_bill.partner_id.id,
                        'vendor_bill_id': vendor_bill.id,
                        'vendor_id_ids': [(4, vendor_bill.partner_id.id)],
                        'vendor_bill_ids': [(4, vendor_bill.id)],
                        'cost_currency': invoice_line.freight_currency.id,
                        'cost_currency_rate': invoice_line.freight_currency_rate,
                    }
                    booking_line_id = self.env['freight.cost_profit'].sudo().create(values)

                invoice_line.write({
                    'account_analytic_id': account_analytic_id,
                    'booking_line_id': booking_line_id.id,
                    'origin': freight_booking.booking_no,
                    'freight_booking': freight_booking.id,
                    'carrier_booking_no': freight_booking.carrier_booking_no,
                })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(form_view_ref, 'form')],
            'view_id': form_view_ref,
            'res_id': vendor_bill.id or False,
        }





class ImportInvoiceLineWizard(models.TransientModel):
    _name = 'import.invoice.line.wizard'

    invoice_wizard_id = fields.Many2one('import.invoice.wizard',
                                       "Invoice Wizard Ref")
    product_id = fields.Many2one('product.product', "Product")
    name = fields.Char('Description')
    price_unit = fields.Float('Price Unit')
    currency = fields.Many2one('res.currency', string='Cur')
    #TS - change the decimal point
    quantity = fields.Float('Qty', digits=(12, 3))
    foreign_price = fields.Float(string='Price')
    currency_rate = fields.Float(string='Exc. Rate', default="1.000000", digits=(12,6))
    invoice_line_tax_ids = fields.Many2many(comodel_name='account.tax',
                                            string='Taxes',
                                            )
    line_amount = fields.Float(string='Amt', digits=(12,2))
    freight_currency_rate = fields.Float(string='Exchange Rate', default="1.000000", track_visibility='onchange', digits=(12,6))
    price_unit = fields.Float(string='U.Price', digits=(12, 6))

    # @api.depends('price_unit', 'quantity')
    # def _compute_line_amount(self):
    #     for service in self:
    #         if service.price_unit:
    #             service.line_amount = float_round(service.price_unit * service.quantity, 2, rounding_method='HALF-UP') or 0.0
