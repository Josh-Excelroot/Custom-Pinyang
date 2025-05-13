##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from collections import OrderedDict
import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
import binascii
from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils, float_round
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
import tempfile
import base64
import os
import dateutil.parser as dparser
from datetime import datetime
import PyPDF2
from PyPDF2 import PdfFileWriter, PdfFileReader
from math import floor
import pikepdf

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    ocr_ready_to_execute = fields.Boolean('OCR Ready to Execute')
    ocr_completed = fields.Boolean('OCR Completed')

    @api.onchange('date_invoice')
    def _onchange_date_invoice(self):
        if self.date_invoice:
            self.date = self.date_invoice

    @api.multi
    def action_get_attachment(self):
        attachments = self.env['ir.attachment'].search([
            ('active', '=', True),
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', self.id)
        ])
        for i in attachments:
            filename = i.name
            pdf_attachment = i.datas
            if self.partner_id.id:
                partner = self.partner_id
            else:
                partner = False
            self.read_invoice(pdf_attachment, partner, self)

    def split_pdf(self, file_name, start, end):
        pdf_list = []
        pdf = file_name

        with pikepdf.Pdf.open(pdf) as my_pdf:
            my_pdf.save(pdf+"1")
        pdf = pdf+"1"
        pdfFileObj = open(pdf, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        page_number = pdfReader.numPages
        for i in range(page_number):
            # creating pdf writer object for (i+1)th split
            pdfWriter = PyPDF2.PdfFileWriter()
            # output pdf file name
            outputpdf = pdf.split('.pdf')[0] + str(i + 1)
            # adding pages to pdf writer object
            for page in range(start, end):
                pdfWriter.addPage(pdfReader.getPage(page))
            # writing split pdf pages to pdf file
            with open(outputpdf, "wb") as f:
                pdfWriter.write(f)
            # interchanging page split start position for next split
            start = end
            end = end + 1
            pdf_list.append(outputpdf)
            if end > page_number:
                break
        # closing the input pdf file object
        pdfFileObj.close()
        return pdf_list

    def get_partner(self, text_file):
        partner_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PARTNER')])
        partner = False
        partner_template = False
        query_name = False
        count = 0
        list_text = list(text_file)
        for line in list_text:
            if len(line) > 3 and not partner:
                if 'MEDITERRANEAN SHIPPING COMPANY S.A.' in line:
                    currency_text_idx = list_text.index('Charge Description Amount\n') + 1
                    currency_text = list_text[currency_text_idx].strip()
                    currency_obj = self.env['res.currency'].search([
                        ('name','=',currency_text)
                    ])
                    mapping_line = self.env['ocr.table.mapping.line'].search([
                        ('keyword', '=', 'MEDITERRANEAN SHIPPING COMPANY S.A.'),
                        ('type', '=', 'value'),
                        ('line_id', '=', partner_keywords.id),
                        ('currency', '=',currency_obj.id ),
                    ])
                    partner = mapping_line.partner_id
                    if partner:
                        partner_template = partner.ocr_partner_template
                    return partner_template, partner

                #print(line)
                temp_names = line.split()
                partner_ids1 = False
                for temp_name in temp_names:
                    temp_name = temp_name.replace("]","")
                    if not partner and len(temp_name) > 2:
                        partner_ids = self.env['ocr.table.mapping.line'].search([
                            ('keyword', 'ilike', temp_name),
                            ('type', '=', 'value'),
                            ('line_id', '=', partner_keywords.id),
                        ])
                        if partner_ids:
                            if temp_name in partner_ids[0].keyword:
                                print("Yes")
                            else:
                                partner_ids = []
                        if len(partner_ids) == 1:
                            partner = partner_ids[0].partner_id
                        elif len(partner_ids) > 1:
                            if not query_name:
                                query_name = temp_name
                            else:
                                query_name = query_name + " " + temp_name
                            partner_ids1 = self.env['ocr.table.mapping.line'].search([
                                ('keyword', 'ilike', query_name),
                                ('type', '=', 'value'),
                                ('line_id', '=', partner_keywords.id),
                            ])
                            if len(partner_ids1) == 1:
                                partner = partner_ids1[0].partner_id
                            elif not partner_ids1:
                                partner = partner_ids[0].partner_id
                            count = count + 1
                            if count > 3:
                                partner = partner_ids[0].partner_id
                        elif not partner_ids and partner_ids1:
                            partner = partner_ids1[0].partner_id

            if partner:
                partner_template = partner.ocr_partner_template
                break
        return partner_template, partner

    def get_invoice_no(self, partner_template, text_file_dic):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        reference = False
        check_reference = False
        get_reference_next_line = False
        check_oocl_reference = False
        reference_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'REFERENCE')])
        for line in text_file:
            line = line.replace(',', '')
            line = line.replace('=', '')

            if len(line) > 3 and not check_reference:
                reference_pattern_count = 1
                reference_template_label_cma = False
                reference_pattern_cma = False
                if partner_template:
                    if partner_template.reference_pattern or partner_template.reference_template_label:
                        reference_pattern_cma = partner_template.reference_pattern
                        reference_template_label_cma = partner_template.reference_template_label
                        reference_pattern_cma = reference_pattern_cma[0:5]
                        if reference_pattern_cma in line:
                            temp_names = line.split()
                            for temp_name in temp_names:
                                if reference_pattern_cma in temp_name:
                                    reference = temp_name
                                    check_reference = True
                if get_reference_next_line:
                    reference_pattern = partner_template.reference_pattern
                    reference_pattern_text = reference_pattern.replace("NEXT LINE", "")
                    reference_pattern_text = reference_pattern_text.replace("FIRST", "")
                    reference_pattern_text = reference_pattern_text.replace("LAST", "").strip()

                    reference_pattern_count = len(reference_pattern.split()) - 2
                    if "LAST" in reference_pattern:
                        reference_pattern_count = reference_pattern_count - 1
                        reference = ' '.join(line.split()[len(line.split()) - reference_pattern_count:len(line.split())])
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                    elif "FIRST" in reference_pattern:
                        reference_pattern_count = reference_pattern_count - 1
                        reference = ' '.join(line.split()[:reference_pattern_count])
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                    else:
                        reference = line.split()[-reference_pattern_count]
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                else:
                    reference_template_label = False
                    reference_pattern = False
                    if partner_template:
                        if partner_template.reference_pattern or partner_template.reference_template_label:
                            reference_pattern = partner_template.reference_pattern
                            reference_template_label = partner_template.reference_template_label
                            reference_pattern_count = len(reference_pattern.split())
                    if reference_template_label:
                        mapping_line_ids = reference_template_label
                    else:
                        mapping_line_ids = reference_keywords.mapping_line_ids
                    for keyword in mapping_line_ids:
                        if keyword.type == 'label':
                            upper_keyword = keyword.keyword.upper()
                            upper_line = line.upper()
                            if upper_keyword in upper_line:
                                if reference_pattern:
                                    if "NEXT LINE" in reference_pattern:
                                        get_reference_next_line = True
                                        break
                                reference_raw = upper_line.partition(upper_keyword)[2]
                                if partner_template.name == "YANG MING LINE (M) SDN BHD":
                                    reference_raw = upper_line.partition("NO")[2]
                                temp_names = reference_raw.split()
                                counter = 1
                                for temp_name in temp_names:
                                    if not check_reference:
                                        if any(c.isalpha() for c in temp_name):
                                            if partner_template.name == "COSCO SHIPPING Lines (Malaysia) Sdn. Bhd.":
                                                if len(temp_name) > 5:
                                                    if counter <= reference_pattern_count:
                                                        counter += 1
                                                        if not reference:
                                                            reference = temp_name
                                                        else:
                                                            reference = reference + " " +temp_name
                                                    else:
                                                        break
                                            else:
                                                if counter <= reference_pattern_count:
                                                    counter += 1
                                                    if not reference:
                                                        reference = temp_name
                                                    else:
                                                        reference = reference + " " +temp_name
                                                else:
                                                    break
                                        elif any(c.isnumeric() for c in temp_name):
                                            if counter <= reference_pattern_count:
                                                counter += 1
                                                if not reference:
                                                    reference = temp_name
                                                else:
                                                    reference = reference + " " + temp_name
                                            else:
                                                break
                                if reference:
                                    check_reference = True
                                    break

                if partner_template.name == "Orient Overseas Container Line":
                    reference_pattern_count = len(reference_pattern.split())
                    if partner_template.reference_template_label.keyword in line:
                        check_oocl_reference = True
                    if check_oocl_reference and not check_reference:
                        line_clean = line.replace(":", "")
                        temp_names = line_clean.split()
                        empty_space = line_clean.replace(" ","")
                        if len(temp_names) == reference_pattern_count:
                            try:
                                empty_space1 = int(empty_space)
                                check_reference = True
                                reference = line_clean
                            except:
                                print("Not Number")

            if check_reference:
                break
        if not reference:
            reference = self.get_debit_note_no(partner_template, text_file_dic)
        return reference

    def get_debit_note_no(self, partner_template, text_file_dic):
        print("get_debit_note_no")
        text_file = open(text_file_dic, 'r', encoding="utf8")
        reference = False
        check_reference = False
        get_reference_next_line = False
        check_oocl_reference = False
        reference_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'REFERENCE')])
        for line in text_file:
            line = line.replace(',', '')
            line = line.replace('=', '')
            line = line.replace(':', '')
            # line = line.replace('�', '')

            if len(line) > 3 and not check_reference:
                #print(line)
                reference_pattern_count = 1
                debit_note_template_label_cma = False
                reference_pattern_cma = False
                if partner_template:
                    if partner_template.reference_pattern or partner_template.debit_note_template_label:
                        reference_pattern_cma = partner_template.reference_pattern
                        debit_note_template_label_cma = partner_template.debit_note_template_label
                        reference_pattern_cma = reference_pattern_cma[0:5]
                        if reference_pattern_cma in line:
                            temp_names = line.split()
                            for temp_name in temp_names:
                                if reference_pattern_cma in temp_name:
                                    reference = temp_name
                                    check_reference = True
                if get_reference_next_line:
                    reference_pattern = partner_template.reference_pattern
                    reference_pattern_text = reference_pattern.replace("NEXT LINE", "")
                    reference_pattern_text = reference_pattern_text.replace("FIRST", "")
                    reference_pattern_text = reference_pattern_text.replace("LAST", "").strip()

                    reference_pattern_count = len(reference_pattern.split()) - 2
                    if "LAST" in reference_pattern:
                        reference_pattern_count = reference_pattern_count - 1
                        reference = ' '.join(line.split()[len(line.split()) - reference_pattern_count:len(line.split())])
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                    elif "FIRST" in reference_pattern:
                        reference_pattern_count = reference_pattern_count - 1
                        reference = ' '.join(line.split()[:reference_pattern_count])
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                    else:
                        reference = line.split()[-reference_pattern_count]
                        if len(reference) == len(reference_pattern_text):
                            check_reference = True
                else:
                    debit_note_template_label = False
                    reference_pattern = False
                    if partner_template:
                        if partner_template.reference_pattern or partner_template.debit_note_template_label:
                            reference_pattern = partner_template.reference_pattern
                            debit_note_template_label = partner_template.debit_note_template_label
                            reference_pattern_count = len(reference_pattern.split())
                    if debit_note_template_label:
                        mapping_line_ids = debit_note_template_label
                    else:
                        mapping_line_ids = reference_keywords.mapping_line_ids
                    for keyword in mapping_line_ids:
                        if keyword.type == 'label':
                            upper_keyword = keyword.keyword.upper()
                            upper_line = line.upper()
                            if upper_keyword in upper_line:
                                if reference_pattern:
                                    if "NEXT LINE" in reference_pattern:
                                        get_reference_next_line = True
                                        break
                                reference_raw = upper_line.partition(upper_keyword)[2]
                                if partner_template.name == "YANG MING LINE (M) SDN BHD":
                                    reference_raw = upper_line.partition("NO")[2]
                                temp_names = reference_raw.split()
                                counter = 1
                                for temp_name in temp_names:
                                    if not check_reference:
                                        if any(c.isalpha() for c in temp_name):
                                            if partner_template.name == "COSCO SHIPPING Lines (Malaysia) Sdn. Bhd.":
                                                if len(temp_name) > 5:
                                                    if counter <= reference_pattern_count:
                                                        counter += 1
                                                        if not reference:
                                                            reference = temp_name
                                                        else:
                                                            reference = reference + " " +temp_name
                                                    else:
                                                        break
                                            else:
                                                if counter <= reference_pattern_count:
                                                    counter += 1
                                                    if not reference:
                                                        reference = temp_name
                                                    else:
                                                        reference = reference + " " +temp_name
                                                else:
                                                    break
                                        elif any(c.isnumeric() for c in temp_name):
                                            if counter <= reference_pattern_count:
                                                counter += 1
                                                if not reference:
                                                    reference = temp_name
                                                else:
                                                    reference = reference + " " + temp_name
                                            else:
                                                break
                                if reference:
                                    check_reference = True
                                    break

                if partner_template.name == "Orient Overseas Container Line":
                    reference_pattern_count = len(reference_pattern.split())
                    if partner_template.debit_note_template_label.keyword in line:
                        check_oocl_reference = True
                    if check_oocl_reference and not check_reference:
                        line_clean = line.replace(":", "")
                        temp_names = line_clean.split()
                        empty_space = line_clean.replace(" ","")
                        if len(temp_names) == reference_pattern_count:
                            try:
                                empty_space1 = int(empty_space)
                                check_reference = True
                                reference = line_clean
                            except:
                                print("Not Number")

            if check_reference:
                break
        return reference

    def get_bl_no(self, partner_template, text_file_dic):
        text_file = open(text_file_dic, 'r', encoding="utf8")

        bl_no = False
        check_bl_no = False
        get_bl_no_next_line = False
        bl_no_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'BL NO')], limit=1)
        for line in text_file:
            if len(line) > 3 and not check_bl_no:
                bl_no_pattern_count = 1
                if get_bl_no_next_line:
                    bl_no_pattern = partner_template.bl_no_pattern
                    bl_no_pattern_count = len(bl_no_pattern.split()) - 2
                    if "LAST" in bl_no_pattern:
                        bl_no_pattern_count = bl_no_pattern_count - 1
                        bl_no = line.split()[-bl_no_pattern_count]
                        check_bl_no = True
                    elif "FIRST" in bl_no_pattern:
                        bl_no = line.split()[0]
                        check_bl_no = True
                    else:
                        bl_no = line.split()[-bl_no_pattern_count]
                        check_bl_no = True
                else:
                    bl_no_pattern = False
                    bl_no_template_label = False
                    if partner_template:
                        if partner_template.bl_no_pattern or partner_template.bl_no_template_label:
                            bl_no_pattern = partner_template.bl_no_pattern
                            bl_no_template_label = partner_template.bl_no_template_label
                            bl_no_pattern_count = len(bl_no_pattern.split())
                    if bl_no_template_label:
                        mapping_line_ids = bl_no_template_label
                    else:
                        mapping_line_ids = bl_no_keywords.mapping_line_ids
                    for keyword in mapping_line_ids:
                        if keyword.type == 'label':
                            upper_keyword = keyword.keyword.upper()
                            upper_line = line.upper()
                            if upper_keyword in upper_line:
                                if bl_no_pattern:
                                    if "NEXT LINE" in bl_no_pattern:
                                        get_bl_no_next_line = True
                                        break

                                bl_no_raw = upper_line.partition(upper_keyword)[2]
                                temp_names = bl_no_raw.split()
                                counter = 1
                                for temp_name in temp_names:
                                    if any(c.isalpha() for c in temp_name):
                                        if counter <= bl_no_pattern_count:
                                            counter += 1
                                            if not bl_no:
                                                bl_no = temp_name
                                            else:
                                                bl_no = bl_no + " " + temp_name
                                        else:
                                            break
                                    elif any(c.isnumeric() for c in temp_name):
                                        if counter <= bl_no_pattern_count:
                                            counter += 1
                                            if not bl_no:
                                                bl_no = temp_name
                                            else:
                                                bl_no = bl_no + " " + temp_name
                                        else:
                                            break
                                if bl_no:
                                    check_bl_no = True
                                    break
            if check_bl_no:
                break

        return bl_no

    def get_pol_id(self, pol_text):
        pol = False
        pol_text = pol_text.replace(",", "")
        pol_ids = self.env['ocr.table.mapping.line'].search([
            ('keyword', 'ilike', pol_text),
            ('type', '=', 'value'),
            ('category', '=', 'PORT OF LOADING'),
        ], limit=1)
        return pol_ids

    def get_pol(self, partner_template, text_file_dic, partner):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        direction = False
        pol = False
        pol_id = False
        check_pol = False
        get_pol_next_line = False
        check_pol_counter = 10
        pol_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PORT OF LOADING')])
        for line in text_file:
            if len(line) > 3 and not check_pol:
                pol_pattern_count = 1
                if get_pol_next_line and check_pol_counter > 0:
                    check_pol_counter = check_pol_counter - 1
                    pol_pattern = partner_template.bl_no_pattern
                    pol_pattern_count = len(pol_pattern.split()) - 2
                    if "LAST" in pol_pattern:
                        pol_pattern_count = pol_pattern_count - 1
                        pol_text = line.split()[-pol_pattern_count]
                        pol_id = self.get_pol_id(pol_text)
                        if pol_id:
                            check_pol = True
                    elif "FIRST" in pol_pattern:
                        pol_text = line.split()[0]
                        pol_id = self.get_pol_id(pol_text)
                        if pol_id:
                            check_pol = True
                    else:
                        pol_text = line.split()[-pol_pattern_count]
                        pol_id = self.get_pol_id(pol_text)
                        if pol_id:
                            check_pol = True
                else:
                    pol_pattern = False
                    pol_template_label = False
                    if partner_template:
                        if partner_template.pol_pattern or partner_template.pol_template_label:
                            pol_pattern = partner_template.pol_pattern
                            pol_template_label = partner_template.pol_template_label
                    if pol_template_label:
                        mapping_line_ids = pol_template_label
                    else:
                        mapping_line_ids = pol_keywords.mapping_line_ids

                    for keyword in mapping_line_ids:
                        if keyword.type == 'label':
                            upper_keyword = keyword.keyword.upper()
                            upper_line = line.upper()

                            if upper_keyword in upper_line:
                                if pol_pattern:
                                    if "NEXT LINE" in pol_pattern:
                                        get_pol_next_line = True
                                        break
                                pol_raw = upper_line.partition(upper_keyword)[2]
                                temp_names = pol_raw.split()

                                for temp_name in temp_names:
                                    if any(c.isalpha() for c in temp_name):
                                        if not pol_id:
                                            if not pol:
                                                pol = temp_name
                                                pol = re.sub('[^a-zA-Z0-9 \n\.]', '', pol)
                                                pol_id = self.get_pol_id(pol)
                                            else:
                                                pol = pol + " " + temp_name
                                                pol = re.sub('[^a-zA-Z0-9 \n\.]', '', pol)
                                                pol_id = self.get_pol_id(pol)
                                        else:
                                            break
                                if pol:
                                    check_pol = True
                port_of_loading_id = False
                if pol_id:
                    port_of_loading_id = pol_id.port_of_loading_id.id
                    mapping_line = self.env['ocr.table.mapping.line'].search([
                        ('type', '=', 'value'),
                        ('partner_id', '=', partner.id),
                    ], limit=1)
                    partner_ids = self.env['ocr.table.mapping.line'].search([
                        ('type', '=', 'value'),
                        ('keyword', '=', mapping_line.keyword),
                        ('port_of_loading_id', '=', port_of_loading_id),
                    ])
                    if partner_ids:
                        partner = partner_ids[0].partner_id
                        partner_template = partner.ocr_partner_template
                else:
                    pol = False
                    ## Validation to check pol not maintained
                if port_of_loading_id:
                    port = self.env['freight.ports'].browse(port_of_loading_id)
                    if port.country_id.name == 'Malaysia':
                        direction = "export"
                    else:
                        direction = "import"
                else:
                    direction = "export"
                if check_pol_counter < 1:
                    break
            if check_pol:
                break
        """"
        mapping_line = self.env['ocr.table.mapping.line'].search([
            ('type', '=', 'value'),
            ('partner_id', '=', partner.id),
        ], limit=1)
        partner_ids = self.env['ocr.table.mapping.line'].search([
            ('type', '=', 'value'),
            ('keyword', '=', mapping_line.keyword),
            ('user_id', '=', self.env.user.id),
        ])
        if partner_ids:
            partner = partner_ids[0].partner_id
            partner_template = partner.ocr_partner_template
        """
        return port_of_loading_id, direction, partner_template, partner

    def get_invoice_date(self, partner_template, text_file_dic):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        date = False
        check_date = False
        get_date_next_line = False
        date_pattern_ori = False
        check_oocl_date = False
        date_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'DATE')])
        for line in text_file:
            if len(line) > 3 and not check_date:
                oocl_upper_line = line.upper()
                date_pattern = False
                date_in_line = False
                month_in_line = False
                year_in_line = False
                month = "01"
                if get_date_next_line:
                    string = line.split()
                    for i in string:
                        if "-" in i and "-" in date_pattern_ori:
                            date_pattern = re.sub(r'[^\w]', ' ', date_pattern_ori)
                            date_pattern = date_pattern.replace(" ", "")
                            date_raw = i.upper()
                            date_raw = re.sub(r'[^\w]', ' ', date_raw)
                            date_raw = date_raw.replace(" ", "")
                            if "JAN" in date_raw:
                                month = "01"
                            if "FEB" in date_raw:
                                month = "02"
                            if "MAR" in date_raw:
                                month = "03"
                            if "APR" in date_raw:
                                month = "04"
                            if "MAY" in date_raw:
                                month = "05"
                            if "JUN" in date_raw:
                                month = "06"
                            if "JUL" in date_raw:
                                month = "07"
                            if "AUG" in date_raw:
                                month = "08"
                            if "SEP" in date_raw:
                                month = "09"
                            if "OCT" in date_raw:
                                month = "10"
                            if "NOV" in date_raw:
                                month = "11"
                            if "DEC" in date_raw:
                                month = "12"
                            if date_pattern:
                                if 'DD' in date_pattern:
                                    date_index_start = date_pattern.index('DD')
                                    date_index_end = date_index_start + 2
                                    date_in_line = date_raw[date_index_start:date_index_end]
                                if 'YY' in date_pattern:
                                    year_index_start = date_pattern.index('YY')
                                    year_index_end = year_index_start + 2
                                    year_in_line = date_raw[year_index_start:year_index_end]
                                if 'YYYY' in date_pattern:
                                    year_index_start = date_pattern.index('YYYY')
                                    year_index_end = year_index_start + 4
                                    year_in_line = date_raw[year_index_start:year_index_end]
                                if 'MM' in date_pattern:
                                    month_index_start = date_pattern.index('MM')
                                    month_index_end = month_index_start + 2
                                    month_in_line = date_raw[month_index_start:month_index_end]
                                if 'MMM' in date_pattern:
                                    month_in_line = month
                                date_final = date_in_line + "-" + month_in_line + "-" + year_in_line
                                try:
                                    date = datetime.strptime(date_final, '%d-%m-%Y').date()
                                    check_date = True
                                    get_date_next_line = False
                                except:
                                    get_date_next_line = True
                            continue
                if partner_template:
                    if partner_template.date_format:
                        date_pattern = partner_template.date_format.upper()
                        date_pattern_ori = date_pattern
                        date_pattern = re.sub(r'[^\w]', ' ', date_pattern)
                        date_pattern = date_pattern.replace(" ", "")
                for keyword in date_keywords.mapping_line_ids:
                    upper_keyword = keyword.keyword.upper()
                    upper_line = line.upper()
                    if upper_keyword in upper_line:
                        date_raw = upper_line.partition(upper_keyword)[2]
                        date_raw = date_raw.upper()
                        date_raw = re.sub(r'[^\w]', ' ', date_raw)
                        date_raw = date_raw.replace(" ", "")
                        if "JAN" in date_raw:
                            month = "01"
                        if "FEB" in date_raw:
                            month = "02"
                        if "MAR" in date_raw:
                            month = "03"
                        if "APR" in date_raw:
                            month = "04"
                        if "MAY" in date_raw:
                            month = "05"
                        if "JUN" in date_raw:
                            month = "06"
                        if "JUL" in date_raw:
                            month = "07"
                        if "AUG" in date_raw:
                            month = "08"
                        if "SEP" in date_raw:
                            month = "09"
                        if "OCT" in date_raw:
                            month = "10"
                        if "NOV" in date_raw:
                            month = "11"
                        if "DEC" in date_raw:
                            month = "12"
                        if date_pattern:
                            if 'DD' in date_pattern:
                                date_index_start = date_pattern.index('DD')
                                date_index_end = date_index_start + 2
                                date_in_line = date_raw[date_index_start:date_index_end]
                            if 'YY' in date_pattern:
                                year_index_start = date_pattern.index('YY')
                                year_index_end = year_index_start + 2
                                year_in_line = date_raw[year_index_start:year_index_end]
                            if 'YYYY' in date_pattern:
                                year_index_start = date_pattern.index('YYYY')
                                year_index_end = year_index_start + 4
                                year_in_line = date_raw[year_index_start:year_index_end]
                            if 'MM' in date_pattern:
                                month_index_start = date_pattern.index('MM')
                                month_index_end = month_index_start + 2
                                month_in_line = date_raw[month_index_start:month_index_end]
                            if 'MMM' in date_pattern:
                                month_in_line = month
                            date_final = date_in_line + "-" + month_in_line + "-" + year_in_line
                            try:
                                if partner_template.name in ['MEDITERRANEAN SHIPPING COMPANY (IDR)', 'MEDITERRANEAN SHIPPING COMPANY (USD)']:
                                    date = datetime.strptime(date_final, '%d-%m-%y').date()
                                else:
                                    date = datetime.strptime(date_final, '%d-%m-%Y').date()
                            except:
                                get_date_next_line = True

                        else:
                            temp_names = date_raw.split()
                            for temp_name in temp_names:
                                if any(c.isnumeric() for c in temp_name):
                                    date = temp_name
                                    date = dparser.parse(date, fuzzy=True).date()
                                    if date:
                                        break
                        if not get_date_next_line:
                            check_date = True
                if get_date_next_line:
                    continue
            if check_date:
                break
        if not date and partner_template.name == "Orient Overseas Container Line":
            oocl_upper_keyword = partner_template.date_template_label.keyword.upper()
            date_pattern = partner_template.date_format.upper()
            text_file1 = open(text_file_dic, 'r', encoding="utf8")
            for line in text_file1:
                if len(line) > 3:
                    oocl_upper_line = line.upper()
                    oocl_upper_line = oocl_upper_line.replace(": ","")
                    if oocl_upper_keyword in oocl_upper_line:
                        check_oocl_date = True
                    if check_oocl_date:
                        if ' JAN ' in oocl_upper_line or ' FEB ' in oocl_upper_line or ' MAR ' in oocl_upper_line or \
                                ' APR ' in oocl_upper_line or ' MAY ' in oocl_upper_line or ' JUN ' in oocl_upper_line or \
                                ' JUL ' in oocl_upper_line or ' AUG ' in oocl_upper_line or ' SEP ' in oocl_upper_line or \
                                ' OCT ' in oocl_upper_line or ' NOV ' in oocl_upper_line or ' DEC ' in oocl_upper_line:
                            if "JAN" in oocl_upper_line:
                                month = "01"
                            if "FEB" in oocl_upper_line:
                                month = "02"
                            if "MAR" in oocl_upper_line:
                                month = "03"
                            if "APR" in oocl_upper_line:
                                month = "04"
                            if "MAY" in oocl_upper_line:
                                month = "05"
                            if "JUN" in oocl_upper_line:
                                month = "06"
                            if "JUL" in oocl_upper_line:
                                month = "07"
                            if "AUG" in oocl_upper_line:
                                month = "08"
                            if "SEP" in oocl_upper_line:
                                month = "09"
                            if "OCT" in oocl_upper_line:
                                month = "10"
                            if "NOV" in oocl_upper_line:
                                month = "11"
                            if "DEC" in oocl_upper_line:
                                month = "12"
                            if date_pattern:
                                if 'DD' in date_pattern:
                                    date_index_start = date_pattern.index('DD')
                                    date_index_end = date_index_start + 2
                                    date_in_line = oocl_upper_line[date_index_start:date_index_end]
                                if 'YY' in date_pattern:
                                    year_index_start = date_pattern.index('YY')
                                    year_index_end = year_index_start + 2
                                    year_in_line = oocl_upper_line[year_index_start:year_index_end]
                                if 'YYYY' in date_pattern:
                                    year_index_start = date_pattern.index('YYYY')
                                    year_index_end = year_index_start + 4
                                    year_in_line = oocl_upper_line[year_index_start:year_index_end]
                                if 'MM' in date_pattern:
                                    month_index_start = date_pattern.index('MM')
                                    month_index_end = month_index_start + 2
                                    month_in_line = oocl_upper_line[month_index_start:month_index_end]
                                if 'MMM' in date_pattern:
                                    month_in_line = month
                                date_final = date_in_line + "-" + month_in_line + "-" + year_in_line
                                try:
                                    date = datetime.strptime(date_final, '%d-%m-%Y').date()
                                    break
                                except:
                                    print("Not Date")
        return date

    def get_due_date(self, partner_template, text_file_dic, date):
        text_file = open(text_file_dic, 'r', encoding="utf8")

        due_date = False
        check_due_date = False
        check_oocl_date = False
        due_date_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'DUE DATE')])

        for line in text_file:
            if len(line) > 3 and not check_due_date:
                date_pattern = False
                date_in_line = False
                month_in_line = False
                year_in_line = False
                month = "01"
                if partner_template:
                    if partner_template.date_format:
                        date_pattern = partner_template.date_format.replace(" ", "")
                for keyword in due_date_keywords.mapping_line_ids:
                    if keyword.keyword in line:
                        due_date_raw = line.partition(keyword.keyword)[2]
                        date_raw = due_date_raw.upper()
                        date_raw = re.sub(r'[^\w]', ' ', date_raw)
                        date_raw = date_raw.replace(" ", "")
                        if "JAN" in date_raw:
                            month = "01"
                        if "FEB" in date_raw:
                            month = "02"
                        if "MAR" in date_raw:
                            month = "03"
                        if "APR" in date_raw:
                            month = "04"
                        if "MAY" in date_raw:
                            month = "05"
                        if "JUN" in date_raw:
                            month = "06"
                        if "JUL" in date_raw:
                            month = "07"
                        if "AUG" in date_raw:
                            month = "08"
                        if "SEP" in date_raw:
                            month = "09"
                        if "OCT" in date_raw:
                            month = "10"
                        if "NOV" in date_raw:
                            month = "11"
                        if "DEC" in date_raw:
                            month = "12"
                        if date_pattern:
                            if 'DD' in date_pattern:
                                date_index_start = date_pattern.index('DD')
                                date_index_end = date_index_start + 2
                                date_in_line = date_raw[date_index_start:date_index_end]
                            if 'YY' in date_pattern:
                                year_index_start = date_pattern.index('YY')
                                year_index_end = year_index_start + 2
                                year_in_line = date_raw[year_index_start:year_index_end]
                                year_in_line = '20' + year_in_line
                            if 'YYYY' in date_pattern:
                                year_index_start = date_pattern.index('YYYY')
                                year_index_end = year_index_start + 4
                                year_in_line = date_raw[year_index_start:year_index_end]
                            if 'MM' in date_pattern:
                                month_index_start = date_pattern.index('MM')
                                month_index_end = month_index_start + 2
                                month_in_line = date_raw[month_index_start:month_index_end]
                            if 'MMM' in date_pattern:
                                month_in_line = month
                            date_final = date_in_line + "-" + month_in_line + "-" + year_in_line
                            try:
                                due_date = datetime.strptime(date_final, '%d-%m-%Y').date()
                                print("111")
                            except:
                                due_date = False
                                print("222")
                        else:
                            temp_names = due_date_raw.split()
                            for temp_name in temp_names:
                                if any(c.isnumeric() for c in temp_name):
                                    due_date = temp_name
                                    due_date = dparser.parse(due_date, fuzzy=True).date()
                                    break
                        check_due_date = True
            if check_due_date:
                break
        if not due_date and partner_template.name == "Orient Overseas Container Line":
            oocl_upper_keyword = partner_template.due_date_template_label.keyword.upper()
            date_pattern = partner_template.date_format.upper()
            text_file1 = open(text_file_dic, 'r', encoding="utf8")
            for line in text_file1:
                if len(line) > 3:
                    oocl_upper_line = line.upper()
                    oocl_upper_line = oocl_upper_line.replace(": ","")
                    if oocl_upper_keyword in oocl_upper_line:
                        check_oocl_date = True
                    if check_oocl_date:
                        if ' JAN ' in oocl_upper_line or ' FEB ' in oocl_upper_line or ' MAR ' in oocl_upper_line or \
                                ' APR ' in oocl_upper_line or ' MAY ' in oocl_upper_line or ' JUN ' in oocl_upper_line or \
                                ' JUL ' in oocl_upper_line or ' AUG ' in oocl_upper_line or ' SEP ' in oocl_upper_line or \
                                ' OCT ' in oocl_upper_line or ' NOV ' in oocl_upper_line or ' DEC ' in oocl_upper_line:
                            if "JAN" in oocl_upper_line:
                                month = "01"
                            if "FEB" in oocl_upper_line:
                                month = "02"
                            if "MAR" in oocl_upper_line:
                                month = "03"
                            if "APR" in oocl_upper_line:
                                month = "04"
                            if "MAY" in oocl_upper_line:
                                month = "05"
                            if "JUN" in oocl_upper_line:
                                month = "06"
                            if "JUL" in oocl_upper_line:
                                month = "07"
                            if "AUG" in oocl_upper_line:
                                month = "08"
                            if "SEP" in oocl_upper_line:
                                month = "09"
                            if "OCT" in oocl_upper_line:
                                month = "10"
                            if "NOV" in oocl_upper_line:
                                month = "11"
                            if "DEC" in oocl_upper_line:
                                month = "12"
                            if date_pattern:
                                if 'DD' in date_pattern:
                                    date_index_start = date_pattern.index('DD')
                                    date_index_end = date_index_start + 2
                                    date_in_line = oocl_upper_line[date_index_start:date_index_end]
                                if 'YY' in date_pattern:
                                    year_index_start = date_pattern.index('YY')
                                    year_index_end = year_index_start + 2
                                    year_in_line = oocl_upper_line[year_index_start:year_index_end]
                                if 'YYYY' in date_pattern:
                                    year_index_start = date_pattern.index('YYYY')
                                    year_index_end = year_index_start + 4
                                    year_in_line = oocl_upper_line[year_index_start:year_index_end]
                                if 'MM' in date_pattern:
                                    month_index_start = date_pattern.index('MM')
                                    month_index_end = month_index_start + 2
                                    month_in_line = oocl_upper_line[month_index_start:month_index_end]
                                if 'MMM' in date_pattern:
                                    month_in_line = month
                                date_final = date_in_line + "-" + month_in_line + "-" + year_in_line
                                try:
                                    due_date = datetime.strptime(date_final, '%d-%m-%Y').date()

                                    if due_date != date:
                                        break
                                    else:
                                        due_date = False
                                except:
                                    print("Not Date")
        return due_date

    def get_payment_term(self, partner_template, text_file_dic, date, due_date):
        text_file = open(text_file_dic, 'r', encoding="utf8")

        payment_term = False
        check_payment_term = False
        payment_term_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PAYMENT TERM')])

        for line in text_file:
            if len(line) > 3 and not check_payment_term:
                for keyword in payment_term_keywords.mapping_line_ids:
                    if keyword.type == 'label':
                        if keyword.keyword in line:
                            payment_term_raw = line.partition(keyword.keyword)[2]
                            temp_names = payment_term_raw.split()
                            for temp_name in temp_names:
                                if any(c.isalpha() for c in temp_name):
                                    if not payment_term:
                                        payment_term = temp_name
                                    else:
                                        payment_term = payment_term + " " + temp_name
                                elif any(c.isnumeric() for c in temp_name):
                                    if not payment_term:
                                        payment_term = temp_name
                                    else:
                                        payment_term = payment_term + " " + temp_name
                            check_payment_term = True
            if check_payment_term:
                break
        payment_term_id = False

        if payment_term:
            payment_term_keyword_value = self.env['ocr.table.mapping.line'].search([
                ('line_id', '=', payment_term_keywords.id),
                ('type', '=', 'value'),
                ('keyword', '=', payment_term),
            ])
            if payment_term_keyword_value:
                payment_term_id = payment_term_keyword_value.payment_term_id.id

        if not payment_term:
            if date and due_date:
                delta = due_date - date
                payment_term_ids = self.env['account.payment.term.line'].search([
                    ('value', '=', 'balance'),
                    ('option', '=', 'day_after_invoice_date'),
                    ('days', '=', delta.days),
                ], limit=1)
                payment_term_id = payment_term_ids.payment_id.id

        return payment_term_id

    def get_currency(self, partner_template, text_file_dic):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        get_exchange_rate_next_line = False
        currency = False
        exchange_rate_header = False
        line_item_start = False
        currency_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'CURRENCY')])
        exchange_rate_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'EXCHANGE RATE')])

        for line in text_file:
            if len(line) > 3:
                if partner_template.product_section_end and partner_template.product_section_end in line:
                    line_item_start = False

                if not line_item_start and not currency:
                    for keyword in currency_keywords.mapping_line_ids:
                        upper_keyword = keyword.keyword.upper()
                        upper_line = line.upper()
                        upper_line = re.sub(r'[^\w]', ' ', upper_line)
                        if upper_keyword in upper_line:
                            currency_keyword_value = self.env['ocr.table.mapping.line'].search([
                                ('line_id', '=', currency_keywords.id),
                                ('type', '=', 'value'),
                                ('keyword', '=', upper_keyword),
                            ])
                            if currency_keyword_value:
                                currency = currency_keyword_value.currency.id

                if not line_item_start and not exchange_rate_header:
                    exchange_rate_pattern_count = 1
                    if get_exchange_rate_next_line:
                        exchange_rate_pattern = partner_template.exchange_rate_pattern
                        exchange_rate_pattern_count = len(exchange_rate_pattern.split()) - 2
                        if "LAST" in exchange_rate_pattern:
                            exchange_rate_pattern_count = exchange_rate_pattern_count - 1
                            exchange_rate_header = line.split()[-exchange_rate_pattern_count]
                        else:
                            temp_names = line.split()
                            for temp_name in temp_names:
                                if any(c.isnumeric() for c in temp_name):
                                    if float(temp_name) > 1:
                                        exchange_rate_header = temp_name
                                        break
                    else:
                        exchange_rate_pattern = False
                        exchange_rate_template_label = False
                        if partner_template:
                            if partner_template.exchange_rate_pattern or partner_template.exchange_rate_template_label:
                                exchange_rate_pattern = partner_template.exchange_rate_pattern
                                exchange_rate_template_label = partner_template.exchange_rate_template_label
                                exchange_rate_pattern_count = len(exchange_rate_pattern.split())
                        if exchange_rate_template_label:
                            mapping_line_ids = exchange_rate_template_label
                        else:
                            mapping_line_ids = exchange_rate_keywords.mapping_line_ids
                        for keyword in mapping_line_ids:
                            if keyword.type == 'label':
                                upper_keyword = keyword.keyword.upper()
                                upper_line = line.upper()
                                if upper_keyword in upper_line:
                                    if exchange_rate_pattern:
                                        if "NEXT LINE" in exchange_rate_pattern:
                                            get_exchange_rate_next_line = True
                                            break

                                    exchange_rate_raw = upper_line.partition(upper_keyword)[2]
                                    temp_names = exchange_rate_raw.split()
                                    counter = 1

                                    for temp_name in temp_names:
                                        if any(c.isnumeric() for c in temp_name):
                                            if float(temp_name) > 1:
                                                if counter <= exchange_rate_pattern_count:
                                                    counter += 1
                                                    if not exchange_rate_header:
                                                        exchange_rate_header = temp_name
                                                    else:
                                                        exchange_rate_header = exchange_rate_header + " " + temp_name
                                                else:
                                                    break
                        if exchange_rate_header:
                            break
                if partner_template.product_section_start and partner_template.product_section_start in line:
                    line_item_start = True
            if currency and exchange_rate_header:
                break
        return currency, exchange_rate_header

    def get_line_list(self, partner_template, text_file_dic, currency, exchange_rate_header, direction, container_size):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        line_list = []
        currency_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'CURRENCY')])
        product_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PRODUCT')], limit=1)
        product_exclusion_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PRODUCT EXCLUSION')], limit=1)
        line_item_start = False
        line_item_pattern = partner_template.line_item_pattern
        x2nd_line_item_pattern = partner_template.x2nd_line_item_pattern
        for line in text_file:
            if len(line) > 3:
                #print(line)
                if partner_template.name == 'MEDITERRANEAN SHIPPING COMPANY (M) SDN BHD':
                    line = line.replace(r'I\/I', 'M').replace('U51)', 'USD')
                line_item_pattern = partner_template.line_item_pattern
                if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                    if 'OCEAN FREIGHT' in line:
                        line_item_pattern = 'QTY UPI TOTAL'

                if partner_template.product_section_end and partner_template.product_section_end in line:
                    line_item_start = False
                x = 0
                if line_item_start:
                    product_excluded = False
                    product = False
                    product_name = False
                    product_desc = False
                    currency_line_id = False
                    price_list = False
                    price = 0
                    foreign_price = 0
                    currency_rate = 1.000000
                    quantity = 1
                    total = 0

                    line_item_pattern_count = 1
                    x2nd_line_item_pattern_count = 1
                    if partner_template.complex_line:
                        complex_line_pattern = partner_template.complex_line_pattern
                        line_item_pattern_count = len(complex_line_pattern.split())
                        complex_line_pattern_space = complex_line_pattern
                        complex_line_pattern_space = complex_line_pattern_space.replace("NIL", "")
                        complex_line_pattern_space = complex_line_pattern_space.replace("QTY", "")
                        complex_line_pattern_space = complex_line_pattern_space.replace("RTE", "")
                        complex_line_pattern_space = complex_line_pattern_space.replace("PFC", "")
                        complex_line_pattern_space = complex_line_pattern_space.replace("UPI", "")
                        complex_line_pattern_space = complex_line_pattern_space.replace("TOTAL", "")
                        counter = 0
                        list_pattern = []
                        for char in complex_line_pattern_space:
                            start = counter
                            end = complex_line_pattern.index(char)
                            list_pattern.append(complex_line_pattern[start:end])
                            counter = complex_line_pattern.index(char) + 1
                        list_pattern.append(complex_line_pattern[counter:len(complex_line_pattern)])
                        list_price = []
                        temp_names = line.split()
                        check_price = False
                        check_complex_item = False
                        product_desc = False
                        line_item_with_exchange_rate = False

                        # Get Currency in Line
                        currency_id_lines = self.env['ocr.table.mapping.line'].search(
                            [('type', '=', 'value'),
                             ('line_id', '=', currency_keywords.id)])
                        for currency_id_line in currency_id_lines:
                            if currency_id_line.keyword in line and not currency_line_id:
                                currency_line_id = currency_id_line.currency.id

                        if currency and currency_line_id:
                            if currency_line_id != currency:
                                line_item_pattern_count = len(
                                    partner_template.line_item_pattern_with_exchange_rate.split()) - 1
                                line_item_with_exchange_rate = True
                                line_item_pattern = partner_template.line_item_pattern_with_exchange_rate
                        line_item_pattern_counter = 1
                        for temp_name in temp_names:
                            if line_item_pattern_counter <= line_item_pattern_count:
                                if any(char.isdigit() for char in temp_name):
                                    check_price = True
                                    raw_line = temp_name.upper()
                                    counter = 0
                                    if not check_complex_item:
                                        for char in complex_line_pattern_space:
                                            start = counter
                                            try:
                                                end = raw_line.index(char)
                                                counter = raw_line.index(char) + 1

                                            except:
                                                end = len(raw_line)
                                            list_price.append(raw_line[start:end])
                                            check_complex_item = True
                                    list_price.append(raw_line[counter:len(raw_line)])
                                    line_item_pattern_counter = line_item_pattern_counter + 1
                            else:
                                break

                            if not check_price:
                                # Get Product Name
                                if not product_name:
                                    if len(temp_name) > 1:
                                        product_name = temp_name
                                else:
                                    if len(temp_name) > 1:
                                        product_name = product_name + " " + temp_name
                                # Get Raw Product Description
                                if not product_desc:
                                    product_desc = temp_name
                                else:
                                    product_desc = product_desc + " " + temp_name
                                if not product:
                                    product_ids = self.env['ocr.table.mapping.line'].search(
                                        [('keyword', 'ilike', product_name),
                                         ('type', '=', 'value'),
                                         ('line_id', '=', product_keywords.id),
                                         ('direction', '=', direction),
                                         ('container_size', '=', container_size)
                                         ])
                                    if len(product_ids) == 1:
                                        product = product_ids[0]
                                    elif len(product_ids) > 1:
                                        product_ids = self.env['ocr.table.mapping.line'].search(
                                            [('keyword', '=', product_name),
                                             ('type', '=', 'value'),
                                             ('line_id', '=', product_keywords.id),
                                             ('direction', '=', direction),
                                             ('container_size', '=', container_size)
                                             ])
                                        if len(product_ids) == 1:
                                            product = product_ids[0]
                                    else:
                                        product_name = False
                        counter = 0
                        if line_item_with_exchange_rate:
                            list_pattern = partner_template.line_item_pattern_with_exchange_rate.split()
                        for item in list_pattern:
                            try:
                                price_list = re.findall('\d+\.\d{2,6}|\d+', list_price[counter])
                            except:
                                price_list = []
                            if len(price_list) > 0:
                                x = 1
                                if "QTY" in item:
                                    qty_index = item.index('QTY')
                                    if qty_index > 0:
                                        qty_index = int(qty_index / 4)
                                        quantity = float(price_list[qty_index])
                                    else:
                                        quantity = float(price_list[0])
                                if "PFC" in item:
                                    foreign_price_index = item.index('PFC')
                                    if foreign_price_index > 0:
                                        foreign_price_index = int(foreign_price_index / 4)
                                        foreign_price = float(price_list[foreign_price_index])
                                    else:
                                        foreign_price = float(price_list[0])

                                if "RTE" in item:
                                    currency_rate_index = item.index('RTE')
                                    if currency_rate_index > 0:
                                        currency_rate_index = int(currency_rate_index / 4)
                                        currency_rate = float(price_list[currency_rate_index])
                                    else:
                                        currency_rate = float(price_list[0])
                                if "UPI" in item:
                                    price_index = item.index('UPI')
                                    if price_index > 0:
                                        price_index = int(price_index / 4)
                                        price = float(price_list[price_index])
                                    else:
                                        price = float(price_list[0])
                            counter = counter + 1

                        if price == 0 and foreign_price > 0:
                            price = round(foreign_price * currency_rate, 6)
                            # TODO
                        if currency and currency_line_id:
                            if currency_line_id != currency:
                                if "RTE" not in line_item_pattern:
                                    currency_rate = exchange_rate_header
                                    if foreign_price == 0 and price > 0:
                                        foreign_price = price
                                        price = round(foreign_price * exchange_rate_header, 6)
                                else:
                                    if currency_rate == 1 and total > 0 and quantity > 0:
                                        if foreign_price > 0:
                                            currency_rate = total / foreign_price
                                        if price > 0:
                                            currency_rate = total / price
                                        currency_rate = currency_rate / quantity

                                    if foreign_price == 0 and price > 0:
                                        foreign_price = price
                                        price = round(foreign_price * currency_rate, 6)

                    else:
                        line_with_price = line.replace(',', '')
                        line_with_price = line_with_price.lstrip('0123456789.- ')
                        price_list_raw = re.findall('\d+\.\d{2,6}|\d+', line_with_price)
                        price_list = price_list_raw[-len(line_item_pattern.split()):]
                        if len(price_list) == 5 and partner_template.name == 'MEDITERRANEAN SHIPPING COMPANY (M) SDN BHD':
                            line_item_pattern = line_item_pattern.replace('NIL ','')
                        x = floor(len(line_item_pattern) / 4)
                        if x2nd_line_item_pattern:
                            y = floor(len(x2nd_line_item_pattern) / 4)
                            if len(price_list) == y:
                                line_item_pattern = x2nd_line_item_pattern
                                x = y
                        if 0 < len(price_list) == x:
                            # Get Product Info
                            product_desc = False
                            if "TOTAL" in line_item_pattern:
                                # Get Currency in Line
                                if partner_template.name in ['MEDITERRANEAN SHIPPING COMPANY (IDR)', 'MEDITERRANEAN SHIPPING COMPANY (USD)']:
                                    currency_line_id = currency.id
                                else:
                                    currency_id_lines = self.env['ocr.table.mapping.line'].search(
                                        [('type', '=', 'value'),
                                         ('line_id', '=', currency_keywords.id)])
                                    for currency_id_line in currency_id_lines:
                                        if currency_id_line.keyword in line and not currency_line_id:
                                            currency_line_id = currency_id_line.currency.id
                                if partner_template.with_exchange_rate:
                                    if currency and currency_line_id:
                                        if currency != currency_line_id:
                                            line_item_pattern = partner_template.line_item_pattern_with_exchange_rate
                                            price_list = price_list_raw[-len(line_item_pattern.split()):]
                                line_remove_comma = line.replace(',', '')
                                if not partner_template.name == "WESTPORTS MALAYSIA SDN BHD":
                                    line_remove_comma = line_remove_comma.replace('-', ' ')
                                temp_names = line_remove_comma.split()
                                for temp_name in temp_names:
                                    if not temp_name.isdecimal() and (
                                            len(temp_name) > 2 or (partner_template.name == 'MEDITERRANEAN SHIPPING COMPANY (M) SDN BHD' and temp_name == 'BL')
                                    ):
                                        if '.' not in temp_name:
                                            # Get Product Name
                                            if not product_name:
                                                if len(temp_name) > 1:
                                                    product_name = temp_name
                                            else:
                                                if len(temp_name) > 1:
                                                    product_name = product_name + " " + temp_name
                                            # Get Raw Product Description
                                            if not product_desc:
                                                product_desc = temp_name
                                            else:
                                                product_desc = product_desc + " " + temp_name
                                            product_exclusion_ids = self.env['ocr.table.mapping.line'].search(
                                                [('keyword', 'ilike', product_name),
                                                 ('line_id', '=', product_exclusion_keywords.id),
                                                 ])
                                            if len(product_exclusion_ids) > 0:
                                                product_excluded = True
                                            if not product:
                                                product_ids = self.env['ocr.table.mapping.line'].search(
                                                    [('keyword', 'ilike', product_name),
                                                     ('type', '=', 'value'),
                                                     ('line_id', '=', product_keywords.id),
                                                     ('direction', '=', direction),
                                                     ('container_size', '=', container_size)
                                                     ])
                                                #print(product_ids)
                                                if len(product_ids) == 1:
                                                    product = product_ids[0]
                                                elif len(product_ids) > 1:
                                                    product_ids = self.env['ocr.table.mapping.line'].search(
                                                        [('keyword', '=', product_name),
                                                         ('type', '=', 'value'),
                                                         ('line_id', '=', product_keywords.id),
                                                         ('direction', '=', direction),
                                                         ('container_size', '=', container_size)
                                                         ])
                                                    if len(product_ids) == 1:
                                                        product = product_ids[0]
                                                else:
                                                    product_name = False
                                if len(price_list) > 1:
                                    if "QTY" in line_item_pattern:
                                        qty_index = line_item_pattern.index('QTY')
                                        if qty_index > 0:
                                            qty_index = int(qty_index / 4)
                                            quantity = float(price_list[qty_index])
                                        else:
                                            quantity = float(price_list[0])
                                    if "PFC" in line_item_pattern:
                                        foreign_price_index = line_item_pattern.index('PFC')
                                        if foreign_price_index > 0:
                                            foreign_price_index = int(foreign_price_index / 4)
                                            foreign_price = float(price_list[foreign_price_index])
                                        else:
                                            foreign_price = float(price_list[0])

                                    if "RTE" in line_item_pattern:
                                        currency_rate_index = line_item_pattern.index('RTE')
                                        if currency_rate_index > 0:
                                            currency_rate_index = int(currency_rate_index / 4)
                                            currency_rate = float(price_list[currency_rate_index])
                                        else:
                                            currency_rate = float(price_list[0])
                                    if "UPI" in line_item_pattern:
                                        price_index = line_item_pattern.index('UPI')
                                        if price_index > 0:
                                            price_index = int(price_index / 4)
                                            price = float(price_list[price_index])
                                        else:
                                            price = float(price_list[0])
                                    if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                                        if 'OCEAN FREIGHT' in line:
                                            price = price/ quantity
                                    if "TOTAL" in line_item_pattern:
                                        total_index = line_item_pattern.index('TOTAL')
                                        if total_index > 0:
                                            total_index = int(total_index / 4)
                                            total = float(price_list[total_index])
                                        else:
                                            total = float(price_list[0])
                                if price == 0 and foreign_price > 0:
                                    price = round(foreign_price * currency_rate, 6)
                                    # TODO
                                if currency and currency_line_id:
                                    if currency_line_id != currency:
                                        if "RTE" not in line_item_pattern:
                                            currency_rate = exchange_rate_header
                                            if foreign_price == 0 and price > 0:
                                                foreign_price = price
                                                price = round(float(foreign_price) * float(exchange_rate_header), 6)
                                        else:
                                            if currency_rate == 1 and total > 0 and quantity > 0:
                                                if foreign_price > 0:
                                                    currency_rate = total / foreign_price
                                                if price > 0:
                                                    currency_rate = total / price
                                                currency_rate = currency_rate / quantity

                                            if foreign_price == 0 and price > 0:
                                                foreign_price = price
                                                price = round(foreign_price * currency_rate, 6)

                                company_currency = self.env.ref('base.main_company').currency_id.id
                    if x == len(price_list) and not product_excluded:
                        if quantity < 1000:
                            if product:
                                if partner_template.name in ['MEDITERRANEAN SHIPPING COMPANY (IDR)', 'MEDITERRANEAN SHIPPING COMPANY (USD)']:
                                    line_amount_total = total
                                    price = total / quantity
                                    currency_rate = 1
                                else:
                                    line_amount_total = float_round(price * quantity, 2, rounding_method='HALF-UP') or 0.0
                                dic = {
                                    'product_id': product.product_id.id or False,
                                    'name': product.product_id.name or False,
                                    'temp_name': product_desc or '',
                                    'quantity': quantity,
                                    'price_unit': price,
                                    'line_amount': line_amount_total,
                                    'foreign_price': foreign_price,
                                    'currency_rate': currency_rate,
                                    'currency': currency_line_id,
                                    'invoice_line_tax_ids': False,
                                }
                                line_list.append(dic)
                            else:
                                dic = {
                                    'product_id': False,
                                    'name': product_desc or '',
                                    'temp_name': product_desc or '',
                                    'quantity': quantity,
                                    'price_unit': price,
                                    'line_amount': float_round(price * quantity, 2, rounding_method='HALF-UP') or 0.0,
                                    'foreign_price': foreign_price,
                                    'currency_rate': currency_rate,
                                    'currency': currency_line_id,
                                    'invoice_line_tax_ids': False,
                                }
                                line_list.append(dic)

                if partner_template.product_section_start and partner_template.product_section_start in line:
                    line_item_start = True

        return line_list

    def get_container_list(self, partner_template, text_file_dic):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        line_list = []
        line_list_wp = []
        container_size = 40
        line_item_start = False
        for line in text_file:
            if len(line) > 3:
                if not container_size:
                    if '40HQ' in line or '40GP' in line or '40\'' in line or '40/' in line or '40H' in line or '40!' in line:
                        container_size = 40
                    if '20HQ' in line or '20GP' in line or '20\'' in line or '20/' in line or '20H' in line or '20!' in line:
                        container_size = 20
                if partner_template.container_section_end and partner_template.container_section_end in line:
                    line_item_start = False
                if line_item_start:
                    temp_names = line.split()
                    name = ""
                    for temp_name in temp_names:
                        temp_name = re.sub(r'[^\w]', ' ', temp_name).replace(" ", "")
                        if len(temp_name) < 11:
                            name = name + temp_name
                        else:
                            name = temp_name
                        if len(name) == 11:
                            numbers = sum(c.isdigit() for c in name)
                            letters = sum(c.isalpha() for c in name)
                            spaces = sum(c.isspace() for c in name)
                            if numbers == 7 and letters == 4:
                                line_list.append(name)
                            name = ""
                        elif len(name) > 11:
                            name = ""
                        else:
                            name = temp_name
                if partner_template.container_section_start and partner_template.container_section_start in line:
                    line_item_start = True
        mylist = list(dict.fromkeys(line_list))
        return mylist, container_size

    def update_list_wanhai(self, partner_template, text_file_dic, line_list_ids, currency, exchange_rate_header):
        print("update_list_wanhai")
        text_file = open(text_file_dic, 'r', encoding="utf8")
        container_line_list = []
        line_item_start = False
        line_list_last = []
        found_quantity = False
        quantity_new = 1
        exchange_rate = 1
        for line in text_file:
            if len(line) > 3:
                if found_quantity:
                    test = line.split()
                    test.reverse()
                    for x in test:
                        x = x.replace("*","")
                        if x.isdigit():
                            quantity_new = x
                            break
                    #quantity = ''.join(c for c in test[0] if c.isdigit())
                    found_quantity = False
                if 'HQ' in line:
                    found_quantity = True
            if "EXCHANGE RATE" in line:
                exchange_rate_ids = re.findall('\d+\.\d{2,6}|\d+', line)
                #print(exchange_rate_ids)
                if exchange_rate_ids:
                    exchange_rate = exchange_rate_ids[0]
        for line_list in line_list_ids:
            product_id = line_list.get('product_id')
            name = line_list.get('name')
            quantity = line_list.get('quantity')
            price_unit = line_list.get('price_unit')
            line_amount = line_list.get('line_amount')
            foreign_price = line_list.get('foreign_price')
            currency_rate = line_list.get('currency_rate')
            if product_id:
                product = self.env['product.product'].browse(product_id)
                if product.uom_id.name == "CNTR":
                    if quantity_new != 1:
                        quantity = quantity_new
                        price_unit = float(line_amount) / float(quantity)
                    if exchange_rate != 1:
                        currency_rate = exchange_rate
                        foreign_price = float(price_unit) / float(currency_rate)

            if not currency:
                currency = line_list.get('currency')
            """
            if quantity_new != 1:
                quantity = quantity_new
                price_unit = float(line_amount) / float(quantity)
            if exchange_rate != 1:
                currency_rate = exchange_rate
                foreign_price = float(price_unit) / float(currency_rate)
            """


            dic = {
                'product_id': product_id,
                'name': name,
                'quantity': quantity,
                'price_unit': price_unit,
                'line_amount': line_amount,
                'foreign_price': foreign_price,
                'currency_rate': currency_rate,
                'currency': currency,
                'invoice_line_tax_ids': False,
                'freight_booking': False,
            }
            line_list_last.append(dic)

        return line_list_last


    def update_list_westport(self, partner_template, text_file_dic, line_list_ids):

        text_file = open(text_file_dic, 'r', encoding="utf8")
        container_line_list = []
        line_item_start = False
        line_list_last = []
        special_term = False
        for line in text_file:
            if len(line) > 3:
                if partner_template.container_section_end in line:
                    line_item_start = False
                if line_item_start:
                    temp_names = line.split()
                    name = ""
                    try:
                        try:
                            special_term = line.split(" 20 ", 1)[1].replace('F', '').strip()

                        except:
                            special_term = line.split(" 40 ", 1)[1].replace('F', '').strip()
                    except:
                        special_term = special_term

                    if not 'Number Of Container' in line:
                        for temp_name in temp_names:
                            if len(temp_name) < 11:
                                name = name + temp_name
                            else:
                                name = temp_name
                            if len(name) == 11:
                                numbers = sum(c.isdigit() for c in name)
                                letters = sum(c.isalpha() for c in name)
                                spaces = sum(c.isspace() for c in name)
                                if numbers == 7 and letters == 4:
                                    container_line_list.append(name)
                                name = ""
                            elif len(name) > 11:
                                name = ""
                            else:
                                name = temp_name
                    else:
                        curr_product_line_list = []
                        booking_list = []
                        booking_unique_list = []
                        for line_list in line_list_ids:
                            if line_list.get('quantity') == len(container_line_list):
                                curr_product_line_list.append(line_list)

                        if len(curr_product_line_list) == 1:
                            cur_curr_product_line_list = curr_product_line_list[0]
                            product_id = cur_curr_product_line_list.get('product_id')
                            name = cur_curr_product_line_list.get('name')
                            quantity = cur_curr_product_line_list.get('quantity')
                            price_unit = cur_curr_product_line_list.get('price_unit')
                            line_amount = cur_curr_product_line_list.get('line_amount')
                            foreign_price = cur_curr_product_line_list.get('foreign_price')
                            currency_rate = cur_curr_product_line_list.get('currency_rate')
                            currency = cur_curr_product_line_list.get('currency')
                            for container in container_line_list:
                                operation_line = self.env['freight.operations.line'].search(
                                    [('container_no', '=', container)], order='write_date desc')
                                if operation_line:
                                    booking_list.append(operation_line[0].operation_id)

                            [booking_unique_list.append(x) for x in booking_list if x not in booking_unique_list]
                            curr_list = cur_curr_product_line_list

                            for i in booking_unique_list:
                                booking_count = booking_list.count(i)
                                dic = {
                                    'product_id': product_id,
                                    'name': name,
                                    'quantity': booking_count,
                                    'price_unit': price_unit,
                                    'line_amount': line_amount,
                                    'foreign_price': foreign_price,
                                    'currency_rate': currency_rate,
                                    'currency': currency,
                                    'invoice_line_tax_ids': False,
                                    'freight_booking': i.id,
                                }
                                quantity = quantity - booking_count
                                line_list_last.append(dic)
                            if quantity > 0:
                                dic = {
                                    'product_id': product_id,
                                    'name': name,
                                    'quantity': quantity,
                                    'price_unit': price_unit,
                                    'line_amount': line_amount,
                                    'foreign_price': foreign_price,
                                    'currency_rate': currency_rate,
                                    'currency': currency,
                                    'invoice_line_tax_ids': False,
                                    'freight_booking': False,
                                }
                                line_list_last.append(dic)

                        elif len(curr_product_line_list) > 1:
                            found_special_term = False

                            for cur_curr_product_line_list in curr_product_line_list:
                                product_id = cur_curr_product_line_list.get('product_id')
                                name = cur_curr_product_line_list.get('name')
                                temp_name = cur_curr_product_line_list.get('temp_name')
                                quantity = cur_curr_product_line_list.get('quantity')
                                price_unit = cur_curr_product_line_list.get('price_unit')
                                line_amount = cur_curr_product_line_list.get('line_amount')
                                foreign_price = cur_curr_product_line_list.get('foreign_price')
                                currency_rate = cur_curr_product_line_list.get('currency_rate')
                                currency = cur_curr_product_line_list.get('currency')
                                booking_list = []
                                if special_term in temp_name and special_term != "":
                                    found_special_term = True
                                    for container in container_line_list:
                                        operation_line = self.env['freight.operations.line'].search(
                                            [('container_no', '=', container)], order='write_date desc')
                                        if operation_line:
                                            booking_list.append(operation_line[0].operation_id)
                                    [booking_unique_list.append(x) for x in booking_list if
                                     x not in booking_unique_list]

                                    for i in booking_unique_list:
                                        booking_count = booking_list.count(i)
                                        dic = {
                                            'product_id': product_id,
                                            'name': name,
                                            'quantity': booking_count,
                                            'price_unit': price_unit,
                                            'line_amount': line_amount,
                                            'foreign_price': foreign_price,
                                            'currency_rate': currency_rate,
                                            'currency': currency,
                                            'invoice_line_tax_ids': False,
                                            'freight_booking': i.id,
                                        }
                                        quantity = quantity - booking_count
                                        line_list_last.append(dic)
                                    if quantity > 0:
                                        dic = {
                                            'product_id': product_id,
                                            'name': name,
                                            'quantity': quantity,
                                            'price_unit': price_unit,
                                            'line_amount': line_amount,
                                            'foreign_price': foreign_price,
                                            'currency_rate': currency_rate,
                                            'currency': currency,
                                            'invoice_line_tax_ids': False,
                                            'freight_booking': False,
                                        }
                                        line_list_last.append(dic)
                            if not found_special_term:
                                cur_curr_product_line_list = curr_product_line_list[0]
                                product_id = cur_curr_product_line_list.get('product_id')
                                name = cur_curr_product_line_list.get('name')
                                quantity = cur_curr_product_line_list.get('quantity')
                                price_unit = cur_curr_product_line_list.get('price_unit')
                                line_amount = cur_curr_product_line_list.get('line_amount')
                                foreign_price = cur_curr_product_line_list.get('foreign_price')
                                currency_rate = cur_curr_product_line_list.get('currency_rate')
                                currency = cur_curr_product_line_list.get('currency')
                                for container in container_line_list:
                                    operation_line = self.env['freight.operations.line'].search(
                                        [('container_no', '=', container)], order='write_date desc')
                                    if operation_line:
                                        booking_list.append(operation_line[0].operation_id)
                                [booking_unique_list.append(x) for x in booking_list if x not in booking_unique_list]
                                curr_list = cur_curr_product_line_list

                                for i in booking_unique_list:
                                    booking_count = booking_list.count(i)
                                    dic = {
                                        'product_id': product_id,
                                        'name': name,
                                        'quantity': booking_count,
                                        'price_unit': price_unit,
                                        'line_amount': line_amount,
                                        'foreign_price': foreign_price,
                                        'currency_rate': currency_rate,
                                        'currency': currency,
                                        'invoice_line_tax_ids': False,
                                        'freight_booking': i.id,
                                    }
                                    quantity = quantity - booking_count
                                    line_list_last.append(dic)
                                if quantity > 0:
                                    dic = {
                                        'product_id': product_id,
                                        'name': name,
                                        'quantity': quantity,
                                        'price_unit': price_unit,
                                        'line_amount': line_amount,
                                        'foreign_price': foreign_price,
                                        'currency_rate': currency_rate,
                                        'currency': currency,
                                        'invoice_line_tax_ids': False,
                                        'freight_booking': False,
                                    }
                                    line_list_last.append(dic)

                        container_line_list = []
                        special_term = False
                if partner_template.container_section_start in line:
                    line_item_start = True

        return line_list_last

    def get_list_sing_chuan(self, partner_template, text_file_dic, currency, exchange_rate_header):
        text_file = open(text_file_dic, 'r', encoding="utf8")
        container_list = []
        line_list = []
        container_size = 40
        line_item_start = False
        product_line_item_start = False
        line_item_pattern = partner_template.line_item_pattern
        product_pattern = partner_template.container_inline_product_pattern
        product_pattern = product_pattern.split()
        container_no = False
        product_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'PRODUCT')], limit=1)
        currency_keywords = self.env['ocr.table.mapping'].search([('name', '=', 'CURRENCY')])
        other_product_ids = self.env['ocr.table.mapping.line'].search(
            [('keyword', '=', 'OTHERS'),
             ('type', '=', 'value'),
             ('line_id', '=', product_keywords.id),
             ], limit=1)
        if other_product_ids:
            other_product = other_product_ids.product_id
        else:
            other_product = False
        for line in text_file:
            if len(line) > 3:
                if not container_size:
                    if '40HQ' in line or '40GP' in line or '40\'' in line or '40/' in line or '40H' in line or '40!' in line:
                        container_size = 40
                    if '20HQ' in line or '20GP' in line or '20\'' in line or '20/' in line or '20H' in line or '20!' in line:
                        container_size = 20
                if partner_template.container_section_end in line:
                    line_item_start = False
                if partner_template.product_section_end in line:
                    product_line_item_start = False
                if line_item_start:
                    temp_names = line.split()
                    name = ""
                    for temp_name in temp_names:
                        temp_name = re.sub(r'[^\w]', ' ', temp_name).replace(" ", "")
                        if len(temp_name) < 11:
                            name = name + temp_name
                        else:
                            name = temp_name
                        if len(name) == 11:
                            numbers = sum(c.isdigit() for c in name)
                            letters = sum(c.isalpha() for c in name)
                            spaces = sum(c.isspace() for c in name)
                            if numbers == 7 and letters == 4:
                                container_list.append(name)
                                container_no = name
                            name = ""
                        elif len(name) > 11:
                            name = ""
                        else:
                            name = temp_name
                    line_with_price = line.replace(',', '')
                    line_with_price = line_with_price.lstrip('0123456789.- ')
                    price_list_raw = re.findall('\d+\.\d{2,6}|\d+ . \d{2}', line_with_price)
                    if container_no:
                        operation_line = self.env['freight.operations.line'].search(
                            [('container_no', '=', container_no)], order='write_date desc')
                        if operation_line:
                            booking = operation_line[0].operation_id.id
                        else:
                            booking = False
                        if len(price_list_raw) > 1:
                            for index, i in enumerate(price_list_raw):
                                if product_pattern[index] != 'REBATE' and product_pattern[index] != 'TOTAL':
                                    product_ids = self.env['ocr.table.mapping.line'].search(
                                        [('keyword', '=', product_pattern[index]),
                                         ('type', '=', 'value'),
                                         ('line_id', '=', product_keywords.id),
                                         ], limit=1)
                                    if product_ids:
                                        product = product_ids.product_id
                                    else:
                                        product = False
                                    if float(i) > 0:
                                        dic = {
                                            'product_id': product.id or False,
                                            'name': product.name or False,
                                            'quantity': 1,
                                            'price_unit': float(i),
                                            'line_amount': float(i),
                                            'foreign_price': float(i),
                                            'currency_rate': 1.00,
                                            'currency': currency,
                                            'invoice_line_tax_ids': False,
                                            'freight_booking': booking or False,
                                        }
                                        line_list.append(dic)

                        elif len(price_list_raw) == 1:

                            dic = {
                                'product_id': other_product.id or False,
                                'name': other_product.name or False,
                                'quantity': 1,
                                'price_unit': float(price_list_raw[0]),
                                'line_amount': float(price_list_raw[0]),
                                'foreign_price': float(price_list_raw[0]),
                                'currency_rate': 1.00,
                                'currency': currency,
                                'invoice_line_tax_ids': False,
                                'freight_booking': booking or False,
                            }
                            line_list.append(dic)
                            container_no = False
                if product_line_item_start:
                    product = False
                    product_name = False
                    product_desc = False
                    currency_line_id = False
                    price = 0
                    foreign_price = 0
                    currency_rate = 1.000000
                    quantity = 1
                    total = 0
                    line_with_price = line.replace(',', '')
                    line_with_price = line_with_price.lstrip('0123456789.- ')
                    price_list_raw = re.findall('\d+\.\d{2}', line_with_price)
                    try:
                        price_list = price_list_raw[-len(line_item_pattern.split()):]
                    except:
                        price_list =[]
                    if len(price_list) > 1:
                        # Get Product Info
                        product_desc = False
                        if "TOTAL" in line_item_pattern:
                            # Get Currency in Line
                            currency_id_lines = self.env['ocr.table.mapping.line'].search(
                                [('type', '=', 'value'),
                                 ('line_id', '=', currency_keywords.id)])
                            for currency_id_line in currency_id_lines:
                                if currency_id_line.keyword in line and not currency_line_id:
                                    currency_line_id = currency_id_line.currency.id
                            if partner_template.with_exchange_rate:
                                if currency and currency_line_id:
                                    if currency != currency_line_id:
                                        line_item_pattern = partner_template.line_item_pattern_with_exchange_rate
                                        price_list = price_list_raw[-len(line_item_pattern.split()):]
                            line_remove_comma = line.replace(',', '')
                            line_remove_comma = line.replace('-', ' ')
                            temp_names = line_remove_comma.split()
                            for temp_name in temp_names:
                                if not temp_name.isdecimal():
                                    if '.' not in temp_name:
                                        # Get Product Name
                                        if not product_name:
                                            if len(temp_name) > 1:
                                                product_name = temp_name
                                        else:
                                            if len(temp_name) > 1:
                                                product_name = product_name + " " + temp_name
                                        # Get Raw Product Description
                                        if not product_desc:
                                            product_desc = temp_name
                                        else:
                                            product_desc = product_desc + " " + temp_name
                                        if not product:
                                            product_ids = self.env['ocr.table.mapping.line'].search(
                                                [('keyword', 'ilike', product_name),
                                                 ('type', '=', 'value'),
                                                 ('line_id', '=', product_keywords.id),
                                                 ], limit=1)
                                            if product_ids:
                                                product = product_ids[0]
                                            else:
                                                product_name = False
                            if len(price_list) > 1:
                                if "QTY" in line_item_pattern:
                                    qty_index = line_item_pattern.index('QTY')
                                    if qty_index > 0:
                                        qty_index = int(qty_index / 4)
                                        quantity = float(price_list[qty_index])
                                    else:
                                        quantity = float(price_list[0])
                                if "PFC" in line_item_pattern:
                                    foreign_price_index = line_item_pattern.index('PFC')
                                    if foreign_price_index > 0:
                                        foreign_price_index = int(foreign_price_index / 4)
                                        foreign_price = float(price_list[foreign_price_index])
                                    else:
                                        foreign_price = float(price_list[0])

                                if "RTE" in line_item_pattern:
                                    currency_rate_index = line_item_pattern.index('RTE')
                                    if currency_rate_index > 0:
                                        currency_rate_index = int(currency_rate_index / 4)
                                        currency_rate = float(price_list[currency_rate_index])
                                    else:
                                        currency_rate = float(price_list[0])
                                if "UPI" in line_item_pattern:
                                    price_index = line_item_pattern.index('UPI')
                                    if price_index > 0:
                                        price_index = int(price_index / 4)
                                        price = float(price_list[price_index])
                                    else:
                                        price = float(price_list[0])
                                if "TOTAL" in line_item_pattern:
                                    total_index = line_item_pattern.index('TOTAL')
                                    if total_index > 0:
                                        total_index = int(total_index / 4)
                                        total = float(price_list[total_index])
                                    else:
                                        total = float(price_list[0])
                            if price == 0 and foreign_price > 0:
                                price = foreign_price * currency_rate
                                # TODO
                            if currency and currency_line_id:
                                if currency_line_id != currency:
                                    if "RTE" not in line_item_pattern:
                                        currency_rate = exchange_rate_header
                                        if foreign_price == 0 and price > 0:
                                            foreign_price = price
                                            price = foreign_price * exchange_rate_header
                                    else:
                                        if currency_rate == 1 and total > 0 and quantity > 0:
                                            if foreign_price > 0:
                                                currency_rate = total / foreign_price
                                            if price > 0:
                                                currency_rate = total / price
                                            currency_rate = currency_rate / quantity

                                        if foreign_price == 0 and price > 0:
                                            foreign_price = price
                                            price = foreign_price * currency_rate

                            company_currency = self.env.ref('base.main_company').currency_id.id

                        if product:
                            dic = {
                                'product_id': product.product_id.id or False,
                                'name': product.product_id.name or False,
                                'temp_name': product_desc or '',
                                'quantity': quantity,
                                'price_unit': price,
                                'line_amount': float_round(price * quantity, 2, rounding_method='HALF-UP') or 0.0,
                                'foreign_price': foreign_price,
                                'currency_rate': currency_rate,
                                'currency': currency_line_id,
                                'invoice_line_tax_ids': False,
                            }
                            line_list.append(dic)
                        else:
                            dic = {
                                'product_id': False,
                                'name': product_desc or '',
                                'temp_name': product_desc or '',
                                'quantity': quantity,
                                'price_unit': price,
                                'line_amount': float_round(price * quantity, 2, rounding_method='HALF-UP') or 0.0,
                                'foreign_price': foreign_price,
                                'currency_rate': currency_rate,
                                'currency': currency_line_id,
                                'invoice_line_tax_ids': False,
                            }
                            line_list.append(dic)
                if partner_template.container_section_start in line:
                    line_item_start = True
                if partner_template.product_section_start in line:
                    product_line_item_start = True
        mylist = list(dict.fromkeys(container_list))
        return mylist, container_size, line_list

    def get_text(self, file_name, directory_text, density, psm):
        if density:
            density_value = density
        else:
            density_value = '700'

        if psm:
            psm_value = psm + ' '
        else:
            psm_value = ' '
        command_convert = 'convert -density ' + density_value + ' '+ file_name + \
                          ' -depth 8 -alpha off ' + \
                          file_name + '.tiff'
        os.system(command_convert)
        language = self.env['res.lang'].search([('name', '=', 'English')])
        iso_369_3_code = language.iso_369_3_code

        con_text = '"C:\\Program Files\\Tesseract-OCR\\tesseract.exe" ' + psm_value + \
                   file_name + '.tiff ' + \
                   file_name + \
                   ' -l ' + iso_369_3_code + ' '
        os.system('ECHO ' + con_text + ' > ' + directory_text + '/temp.txt')
        os.system(con_text)
        if not os.path.exists(file_name + '.txt'):
            con_text = 'tesseract ' + psm_value + \
                       file_name + '.tiff ' + \
                       file_name + \
                       ' -l ' + iso_369_3_code + ' '
            os.system(con_text)
            if not os.path.exists(file_name + '.txt'):
                raise Warning(
                    _("Selected language not matched with tesseract-ocr\
                                     package."
                      "\nInstall related package!"
                      "\nFor Reference find in: invoice_import_ocr > doc\
                       > User Reference.txt"))

    def check_invoice(self, bill, reference, filename):
        child_invoice = False
        invoice = self.env['account.invoice'].search([('reference', '=', reference)], limit=1)

        if invoice:
            child_invoice = invoice
        else:
            child_invoice = self.env['account.invoice'].create({
                'type': 'in_invoice',
                'state': 'draft',
                'reference': reference,
                #'account_id': account_id_header,
                'company_id': self.env.user.company_id.id,
            })

        with open(filename, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        attachment = self.env['ir.attachment'].create({
            'active': True,
            'name': reference or 'None',
            'datas': encoded_string,
            'datas_fname': reference,
            'type': 'binary',
            'res_model': 'account.invoice',
            'res_id': child_invoice.id,
        })

        return child_invoice

    def upsert_invoice(self, bill, partner, reference, date, due_date, payment_term, line_list):
        value = []
        account_id = False
        for line in line_list:
            try:
                booking = line['freight_booking']
            except:
                booking = False
            product = self.env['product.product'].browse(line['product_id'])
            if product:
                if product.property_account_expense_id:
                    account_id = product.property_account_expense_id
                elif product.categ_id.property_account_expense_categ_id:
                    account_id = product.categ_id.property_account_expense_categ_id
                if account_id:
                    group_product_desc_invoice = self.env['ir.config_parameter'].sudo().get_param(
                        'product_description.group_product_desc_invoice')
                    value.append([0, 0, {
                        'account_id': account_id.id,
                        'product_id': product.id or False,
                        'name': product.name or '',
                        'freight_currency': line['currency'],
                        'freight_foreign_price': line['foreign_price'],
                        'freight_currency_rate': line['currency_rate'],
                        'quantity': line['quantity'],
                        'price_unit': line['price_unit'],
                        'uom_id': product.uom_id and product.uom_id.id or False,
                        'freight_booking': booking,
                    }])
                else:
                    raise Warning(_("No Account Id in Item."))
        if bill:
            bill.write({
                'partner_id': partner.id,
                'reference': reference,
                'date_invoice': date,
                'payment_term_id': payment_term,
                'date_due': due_date,
                'invoice_line_ids': value,
            })

    @api.multi
    def read_invoice(self, pdf_attachment, partner, bill):
        directory_name = tempfile.mkdtemp(suffix='image2txt')
        line_list = []
        partner = False
        partner_template = False
        try:
            file_name = directory_name + "/temppdf"
            new_file = open(file_name, 'wb')
            directory_text = tempfile.mkdtemp(suffix='temptext')
            content = base64.b64decode(pdf_attachment)
            new_file.write(content)
            new_file.close()

            # Get Partner & Template
            pdf_list = self.split_pdf(file_name, 0, 1)
            first_page_only = pdf_list[0]
            invoice_no_previous = False
            PdfMerger = PyPDF2.PdfFileMerger()
            self.get_text(first_page_only, directory_text, False, False)
            text_file = open(first_page_only + '.txt', 'r', encoding="utf8")
            partner_template, partner = self.get_partner(text_file)
            psm_value = False
            density_value = False
            if partner_template:
                psm_value = partner_template.page_segmentation_modes_value
                density_value = partner_template.density_value
                if partner_template.multi_page_check:
                    if len(pdf_list) > 1:
                        for i in pdf_list:
                            child_invoice = self.env['account.invoice'].create({
                                'type': 'in_invoice',
                                'state': 'draft',
                                # 'account_id': account_id_header,
                                'company_id': self.env.user.company_id.id,
                            })
                            binary_file = open(i, "rb")
                            encoded_string = base64.b64encode(binary_file.read())
                            new_file_name = "Test.pdf"
                            attachment = self.env['ir.attachment'].create({
                                'active': True,
                                'name': new_file_name,
                                'datas': encoded_string,
                                'datas_fname': "PDF",
                                'type': 'binary',
                                'res_model': 'account.invoice',
                                'res_id': child_invoice.id,
                            })
                            message_monitor = self.env['message.monitor'].create({
                                'type': 'account.invoice',
                                'object_id': child_invoice.id,
                                'has_attachment': True,
                            })
                    else:
                        for i in pdf_list:
                            self.get_text(i, directory_text, density_value, psm_value)
                            text_file_dic = (i + '.txt')
                            text_file = open(i + '.txt', 'r', encoding="utf8")
                            partner_template, partner = self.get_partner(text_file)

                            if partner_template and partner:
                                reference = self.get_invoice_no(partner_template, text_file_dic)
                                bl_no = self.get_bl_no(partner_template, text_file_dic)
                                if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                                    if reference:
                                        left1, right1 = reference[:3], reference[3:]
                                        right1 = right1.replace("O", "0")
                                        reference = left1 + right1
                                    if bl_no:
                                        left2, right2 = bl_no[:3], bl_no[3:]
                                        right2 = right2.replace("O", "0")
                                        bl_no = left2 + right2
                                pol, direction, partner_template, partner = self.get_pol(partner_template,
                                                                                         text_file_dic, partner)
                                date = self.get_invoice_date(partner_template, text_file_dic)
                                due_date = self.get_due_date(partner_template, text_file_dic)
                                payment_term = self.get_payment_term(partner_template, text_file_dic, date, due_date)
                                currency, exchange_rate_header = self.get_currency(partner_template, text_file_dic)
                                if partner_template.name == "SING CHUAN AIK TRANSPORT SDN BHD":
                                    container_list, container_size, line_list = self.get_list_sing_chuan(
                                        partner_template, text_file_dic, currency, exchange_rate_header)
                                else:
                                    container_list, container_size = self.get_container_list(partner_template,
                                                                                             text_file_dic)
                                    line_list = self.get_line_list(partner_template, text_file_dic, currency,
                                                                   exchange_rate_header, direction, container_size)

                                #new_invoice = self.check_invoice(bill, reference, i)
                                new_invoice = bill
                                self.upsert_invoice(new_invoice, partner, reference, date, due_date, payment_term,
                                                    line_list)


                else:
                    if partner_template.multi_page_count > 0:
                        pdf_list = self.split_pdf(file_name, 0, partner_template.multi_page_count)
                        final_file = pdf_list[0]
                    else:
                        final_file = file_name
                    self.get_text(final_file, directory_text, density_value, psm_value)
                    text_command = ",'r', encoding='utf8'"
                    text_file_dic = (final_file + '.txt')
                    #text_file = open(pdf_list[0] + '.txt', 'r', encoding="utf8")
                    reference = self.get_invoice_no(partner_template, text_file_dic)
                    bl_no = self.get_bl_no(partner_template, text_file_dic)
                    if partner_template.name == "CMA CGM Asia Shipping Pte. Ltd":
                        if reference:
                            left1, right1 = reference[:3], reference[3:]
                            right1 = right1.replace("O", "0")
                            reference = left1 + right1
                        if bl_no:
                            left2, right2 = bl_no[:3], bl_no[3:]
                            right2 = right2.replace("O", "0")
                            bl_no = left2 + right2
                    pol, direction, partner_template, partner = self.get_pol(partner_template, text_file_dic, partner)
                    date = self.get_invoice_date(partner_template, text_file_dic)
                    due_date = self.get_due_date(partner_template, text_file_dic)
                    payment_term = self.get_payment_term(partner_template, text_file_dic, date, due_date)
                    currency, exchange_rate_header = self.get_currency(partner_template, text_file_dic)
                    container_list, container_size = self.get_container_list(partner_template, text_file_dic)
                    line_list = self.get_line_list(partner_template, text_file_dic, currency, exchange_rate_header, direction, container_size)
                    if partner_template.name == "WESTPORTS MALAYSIA SDN BHD":
                        line_list = self.update_list_westport(partner_template, text_file_dic, line_list)

                    self.upsert_invoice(bill, partner, reference, date, due_date, payment_term, line_list)
            """
            if bl_no:
                freight_booking = self.env['freight.booking'].search([('carrier_booking_no', 'like', bl_no)], limit=1)
            """


        finally:
            img_attach = False
            # shutil.rmtree(directory_name)
            # raise Warning(_(con_text))
