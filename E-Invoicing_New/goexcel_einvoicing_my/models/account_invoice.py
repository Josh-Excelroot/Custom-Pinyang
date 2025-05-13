from odoo import api, fields, models, exceptions
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
import requests
import json
from .send_e_invoice import send_invoice
import datetime
from datetime import timedelta
from lxml import etree, html
from odoo.tools import float_is_zero, float_round
import base64
import json
import hashlib

# from openpyxl import load_workbook
import  csv

from odoo.http import request
import qrcode
import base64
from io import BytesIO
import xml.etree.ElementTree as ET

class AccountInvoice(models.Model):
    # _inherit = "account.invoice"
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'base.ubl']

    e_invoice_version = fields.Char(string="E-Invoice#")
    original_e_invoice_no  = fields.Char(string="Original e-Invoice #")

    reference_number = fields.Char(string="Reference Number")
    validation_datetime = fields.Datetime(string="Validation Date", track_visibility='always',  copy=False)
    cancelation_datetime = fields.Datetime(string="Cancelation Date", track_visibility='always', copy=False)
    irbm_unique_no = fields.Char(string="IRBM Unique Identifier Number")

    tax_exemption_details = fields.Char(string="Details of Tax Exemption",help="Description of tax exemption applicable (e.g., ")
    amount_exempted_from_Tax= fields.Char(string="Buyer’s sales tax exemption",help="Buyer’s sales tax exemption certificate number, special exemption as per gazette orders, etc.) ")
    einvoice_sending_time = fields.Datetime(string="Sending time" , track_visibility='always', copy=False)

    enable_e_invoice = fields.Boolean(string="Enable E-invoice",compute='check_einvoice_enable')

    e_invoice_status = fields.Selection([('Valid', 'Valid'),
                                         ('Invalid', 'Invalid'),
                                         ('Submitted','Submitted'),
                                         ('In_Progress', 'In Progress'),
                                         ('Cancelled', 'Cancelled')] , track_visibility='always', copy=False)

    e_invoice_cancel_reason = fields.Char(string="Cancel Reason", track_visibility='always', copy=False)
    e_invoice_validation_response = fields.Text(string='Validation Response', copy=False)

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code', track_visibility='always', copy=False)
    # qr_image = fields.Binary("QR Code")
    qr_in_report = fields.Boolean('Show QR in Report')

    submissionUid = fields.Char(string="SubmissionUid", track_visibility='always', copy=False)
    uuid = fields.Char(string="UUID", track_visibility='always', copy=False)
    longid = fields.Char(string="Long ID", track_visibility='always', copy=False)

    e_invois_url = fields.Char(string="E-Invois URL", track_visibility='always', copy=False , compute='set_e_invois_url')
    # e_invois_url = fields.Char(string="E-Invois URL", store=True, copy=False)

    status_check_limit = fields.Integer("Status Check Limit" , default=0 ,  copy=False)

    e_invoice_type = fields.Selection([
                                         ('Consolidate', 'Consolidate')
                                      ],readonly=False , track_visibility='always', copy=False)
    consolidate_invoice = fields.Boolean('Consolidate Invoice' ,readonly=False , track_visibility='always', copy=False)

    consolidate_msic_code = fields.Selection([
        ('00000','NOT APPLICABLE'),
        ('47111', 'Provision stores'),
        ('47112', 'Supermarket'),
        ('47113', 'Mini market'),
        ('47114', 'Convenience stores'),
        ('47191', 'Department stores'),
        ('47192', 'Department stores and supermarket'),
        ('47193', 'Hypermarket'),
        ('47194', 'News agent and miscellaneous goods store'),
        ('47199', 'Other retail sale in non-specialized stores n.e.c.')
                                       ] , track_visibility='always' , copy=False)

    consolidate_msic_code_value = fields.Char(compute='_compute_consolidate_msic_code_value', string="MSIC Code" , track_visibility='always' ,  copy=False)
    consolidate_msic_code_name = fields.Char(compute='_compute_consolidate_msic_code_name', string="MSIC Name" , track_visibility='always', copy=False)

    buyer_tin_no = fields.Char(string="Buyers TIN", related="partner_id.buyer_tin_no", track_visibility='always')
    brn_no = fields.Char(string="BRN Number", related="partner_id.brn_no", track_visibility='always')

    e_invoice_refund_note = fields.Boolean('E-Invoice Refund Note', readonly=False, track_visibility='always',
                                           copy=False)
    uuid_readonly = fields.Boolean(
        compute='_compute_uuid_readonly',
        string="UUID Readonly",
        store=False
    )

    vaildate_tin_status = fields.Char(string="TIN Status",related="partner_id.vaildate_tin_status" ,track_visibility='always',copy=False)

    @api.depends('user_id')
    def _compute_uuid_readonly(self):
        for record in self:
            record.uuid_readonly = not self.env.user.has_group('goexcel_einvoicing_my.group_admin_only')
    @api.onchange('partner_id')
    def _onchange_consolidated_general_public(self):
        if self.partner_id.consolidated_general_public or self.consolidate_invoice:
            self.consolidate_invoice = True
        else:
            self.consolidate_invoice = False

    def set_e_invois_url(self):
        qrcode_url_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.qrcode_url_einv')

        for rec in self:
            if rec.uuid and rec.longid:
                rec.e_invois_url = f'{qrcode_url_einv}/{rec.uuid}/share/{rec.longid}'


    @api.depends('consolidate_msic_code')
    def _compute_consolidate_msic_code_value(self):
        for record in self:
            record.consolidate_msic_code_value = record.consolidate_msic_code

    @api.depends('consolidate_msic_code')
    def _compute_consolidate_msic_code_name(self):
        selection_dict = dict(
            self.fields_get(allfields=['consolidate_msic_code'])['consolidate_msic_code']['selection'])
        for record in self:
            record.consolidate_msic_code_name = selection_dict.get(record.consolidate_msic_code, False)


    @api.onchange("consolidate_invoice")
    @api.depends("consolidate_invoice")
    def _compute_set_partner(self):
        # if self.e_invoice_type == 'Consolidate':
        if self.consolidate_invoice and not self.partner_id.consolidated_general_public:
            partner = self.env['res.partner'].sudo().search([('name', '=', "General Public"),('company_id','=',self.env.user.company_id.id)])
            if not partner:

                accounts = self.env['account.account'].sudo().search([('default_ar_ap', '=', True)])
                # accounts = False
                if accounts:
                    property_account_receivable_id = False
                    property_account_payable_id = False

                    for account in accounts:
                        if account.user_type_id.name == 'Receivable':
                            property_account_receivable_id = account.id

                        if account.user_type_id.name == 'Payable':
                            property_account_payable_id = account.id
                else:

                    accounts_receivable_type = self.env['account.account.type'].sudo().search(
                        [('type', '=', 'receivable')])
                    if accounts_receivable_type:
                        accounts_receivable = self.env['account.account'].sudo().search(
                            [('user_type_id', '=', accounts_receivable_type.id)])
                        if not accounts_receivable:
                            raise UserError("Please Create Account Receivable In Chart of Account")
                    else:
                        raise UserError("Account Receivable type Not found")

                    accounts_payable_type = self.env['account.account.type'].sudo().search(
                        [('type', '=', 'payable')])
                    if accounts_payable_type:
                        accounts_payable = self.env['account.account'].sudo().search(
                            [('user_type_id', '=', accounts_payable_type.id)])
                        if not accounts_payable:
                            raise UserError("Please Create Account Payablr In Chart of Account")
                    else:
                        raise UserError("Account Payable type Not found")

                    property_account_receivable_id = accounts_receivable[0].id
                    property_account_payable_id = accounts_payable[0].id

                general_public_partner = self.env['res.partner'].sudo().create({
                    'name': 'General Public',
                    'customer': True,
                    'email': 'NA',
                    'phone': 'NA',
                    'street': 'NA',
                    'street2': 'NA',
                    'city': 'NA',
                    'zip': 'NA',
                    'state_id' : self.company_id.partner_id.state_id.id,
                    'buyer_tin_no': 'EI00000000010',
                    'brn_no': 'NA',
                    'company_id': self.company_id.id,
                    'country_id':self.company_id.partner_id.country_id.id,
                    'property_account_receivable_id': property_account_receivable_id if property_account_receivable_id else False,
                    'property_account_payable_id': property_account_receivable_id if property_account_payable_id else False
                })
                self.partner_id = general_public_partner
                self.consolidate_invoice = True
                self.consolidate_msic_code  = self.consolidate_msic_code_name

            else:
                self.partner_id = partner.id

    def send_e_invoice(self):
        if self.e_invoice_status in ['Submitted', 'In_Progress', 'Valid']:
            raise UserError(
                f"The invoice cannot be send because its E-Invoice status is currently in {self.e_invoice_status} state")
        # ///////////////// custom
        self.ensure_one()
        assert self.type in ('out_invoice', 'out_refund', 'in_invoice' , 'in_refund')
        # assert self.state in ('open', 'paid')
        if self.state not in ('open', 'paid'):
            raise UserError("Invoice must be in open or paid state")
        version = self.get_ubl_version()
        xml_string = self.generate_ubl_xml_string(version=version)
        filename = self.get_ubl_filename(version=version)
        ctx = {}

        attachments = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'account.invoice'), ('res_id', '=', self.id),('type' ,'=', 'binary' )])

        if attachments:
            attachments.sudo().unlink()

        # _logger.warning(f"XML ============================= {xml_string}")
        # _logger.warning(f"XML Ecncode ============================= {base64.b64encode(xml_string)}")

        attach = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'res_id': self.id,
            'res_model': str(self._name),
            'datas': base64.b64encode(xml_string),
            'datas_fname': filename,
            'type': 'binary',
            'res_field' : 'ubl_attachment'
        })

        # _logger.warning(f"Attachment Create ============================= {attach.read()[0]}")
        # _logger.warning(f"Attachment Create ============================= {attach[0]}")


        action = self.env['ir.actions.act_window'].for_xml_id(
            'base', 'action_attachment')
        action.update({
            'res_id': attach.id,
            'views': False,
            'view_mode': 'form,tree'
        })

        # ////////////////////////////

        binary_data = base64.b64decode(attach.datas)
        cleaned_bytes_data = binary_data.replace(b'\n', b'')
        binary_data_encdoe = base64.b64encode(cleaned_bytes_data)

        base64_string = binary_data_encdoe.decode('utf-8')

        root = etree.fromstring(cleaned_bytes_data)
        xml_string = etree.tostring(root, encoding='utf-8', method='xml')

        # Compute the SHA-256 hash
        hash_object = hashlib.sha256(cleaned_bytes_data)
        hex_dig = hash_object.hexdigest()

        token_expiry_time = self.env['ir.config_parameter'].sudo().get_param('token_expiry_time')
        apiBaseUrl = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.login_url_taxpayer_einv')
        generatedAccessToken = self.company_id.authorization_token_einv

        if not generatedAccessToken:
            raise UserError("First Generate Access Token Form Settings Page")

        url = f"{apiBaseUrl}/api/v1.0/documentsubmissions"

        payload = json.dumps({
            "documents": [
                {
                    "format": "XML",
                    "documentHash": hex_dig,
                    "codeNumber": self.number,
                    "document": str(base64_string),
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {generatedAccessToken}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # return response
        # //////////////////////////

        # response = send_invoice(self)

        if response.status_code == 202:

            data = json.loads(response.text)
            if data.get('acceptedDocuments') and len(data['acceptedDocuments']) > 0:
                if data['acceptedDocuments'][0]['uuid']:
                    submissionUid = data['submissionUid']
                    uuid =  data['acceptedDocuments'][0]['uuid']
                    self.uuid = uuid
                    self.submissionUid = submissionUid

                    zero_tax_record = self.env['account.tax'].sudo().search([('name', '=', 'Tax 0 %')])
                    if zero_tax_record:
                        zero_tax_record.sudo().unlink()

                    self.write({
                        'e_invoice_status': 'Submitted',
                        'e_invoice_validation_response': 'Invoice Submitted Successfully'
                    })
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view and view.id or False
                    context = dict(self._context or {})
                    context['message'] = "Document is Submitted Successfully please check Status after 10 minutes"

                    self.write({
                        'e_invoice_validation_response': 'Please check Status after 10 minutes'
                    })

                    return {
                        'name': "Success",
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sh.message.wizard',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': context
                    }
                else:
                    self.write({
                        # 'e_invoice_status': 'Invalid',
                        'e_invoice_validation_response': str(response.text)
                    })
                    # self.e_invoice_status = 'Invalid'
                    # self.e_invoice_validation_response = str(response.text)
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view and view.id or False
                    context = dict(self._context or {})
                    context['message'] = str(response.text)

                    return {
                        'name': "Error",
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sh.message.wizard',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': context
                    }
            else:
                self.write({
                    # 'e_invoice_status': 'Invalid',
                    'e_invoice_validation_response': str(response.text)
                })
                # self.e_invoice_status = 'Invalid'
                # self.e_invoice_validation_response = str(response.text)
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = str(response.text)

                return {
                    'name': "Error",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context
                }
        else:
            if response.status_code == 401:
                raise UserError("The E-Invoice token has expired. Please renew the token from setting page to proceed.")
            else:
                self.write({
                    # 'e_invoice_status': 'Invalid',
                    'e_invoice_validation_response': str(response.text)
                })
                # self.e_invoice_status = 'Invalid'
                # self.e_invoice_validation_response = str(response.text)
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = str(response.text)

                return {
                    'name': "Error",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context
                }


    def status_e_invoice(self):
        if self.submissionUid:

            apiBaseUrl = self.env['ir.config_parameter'].sudo().get_param(
                'goexcel_einvoicing_my.login_url_taxpayer_einv')
            generatedAccessToken = self.company_id.authorization_token_einv

                # self.env['ir.config_parameter'].sudo().get_param(
                # 'goexcel_einvoicing_my.authorization_token_einv')


            url = f"{apiBaseUrl}/api/v1.0/documentsubmissions/{str(self.submissionUid)}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {generatedAccessToken}'
            }

            submission_api_response = requests.request("GET", url, headers=headers)

            if submission_api_response.status_code == 200:
                documents_data = json.loads(submission_api_response.text)
                overallStatus = documents_data['overallStatus']
                if documents_data.get('documentSummary') and len(documents_data['documentSummary']) > 0:
                    self.longid = str(documents_data['documentSummary'][0]['longId'])
                    if len(self.longid) > 5:
                        qrcode_url_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.qrcode_url_einv')
                        qrcode_url_einv += f'{self.uuid}/share/{self.longid}'
                        self.e_invois_url = qrcode_url_einv
                        self._generate_qr_code()

                if overallStatus == 'InProgress':

                    url = f"{apiBaseUrl}/api/v1.0/documents/{str(self.uuid)}/details"

                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {generatedAccessToken}'
                    }

                    document_detail_api_response = requests.request("GET", url, headers=headers)
                    if document_detail_api_response.status_code == 200:
                        document_detail_api_data = json.loads(document_detail_api_response.text)
                        document_status = document_detail_api_data['status']

                        if document_status == 'Valid':
                            self.write({
                                'e_invoice_validation_response': 'Invoice Valid',
                                'e_invoice_status': 'Valid'
                            })
                            self.einvoice_sending_time = fields.Datetime.now()
                            self.validation_datetime = fields.Datetime.now()
                            if not self.longid:
                                self.longid = document_detail_api_data['longId']

                            view = self.env.ref('sh_message.sh_message_wizard')
                            view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = "Invoice has been validated"
                            return {
                                'name': "Invoice Valid",
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.message.wizard',
                                'views': [(view.id, 'form')],
                                'view_id': view.id,
                                'target': 'new',
                                'context': context
                            }

                        if document_status == 'Invalid':
                            self.write({
                                'e_invoice_validation_response': 'Invoice In Valid',
                                'e_invoice_status': 'Invalid'
                            })

                            view = self.env.ref('sh_message.sh_message_wizard')
                            view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = "Invoice Not validated"
                            return {
                                'name': "Invoice In Valid",
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.message.wizard',
                                'views': [(view.id, 'form')],
                                'view_id': view.id,
                                'target': 'new',
                                'context': context
                            }

                        if document_status == 'Submitted':
                            self.write({
                                'e_invoice_validation_response': 'Invoice In Progress',
                                'e_invoice_status': 'In_Progress'
                            })

                            view = self.env.ref('sh_message.sh_message_wizard')
                            view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = "Still in Progress"
                            return {
                                'name': "Invoice In Progress",
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.message.wizard',
                                'views': [(view.id, 'form')],
                                'view_id': view.id,
                                'target': 'new',
                                'context': context
                            }
                    else:
                        if document_detail_api_response.status_code == 401:
                            raise UserError(
                                "The E-Invoice token has expired. Please renew the token from setting page to proceed.")
                        else:
                            view = self.env.ref('sh_message.sh_message_wizard')
                            view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = str(document_detail_api_response.text)
                            return {
                                'name': "Error",
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.message.wizard',
                                'views': [(view.id, 'form')],
                                'view_id': view.id,
                                'target': 'new',
                                'context': context
                            }





                if overallStatus == 'Invalid':
                    # ////////////////////////
                    url = f"{apiBaseUrl}/api/v1.0/documents/{str(self.uuid)}/details"

                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {generatedAccessToken}'
                    }

                    document_detail_api_response = requests.request("GET", url, headers=headers)
                    if document_detail_api_response.status_code == 200:
                        document_detail_api_data = json.loads(document_detail_api_response.text)
                        document_status = document_detail_api_data['status']

                        if document_status == 'Invalid':
                            self.write({
                                'e_invoice_validation_response': str(
                                    document_detail_api_data['validationResults']['validationSteps']),
                                'e_invoice_status': 'Invalid'
                            })

                    else:
                        if document_detail_api_response.status_code == 401:
                            raise UserError(
                                "The E-Invoice token has expired. Please renew the token from setting page to proceed.")
                        else:
                            self.write({
                                'e_invoice_validation_response': str(document_detail_api_response.text),
                                'e_invoice_status': 'Invalid'
                            })
                    # ////////////////////////
                    pass

                if overallStatus == 'Valid':
                    documentStatus = documents_data['documentSummary'][0]['status']

                    if documentStatus == 'Invalid':
                        # /// set python status field
                        self.write({
                            'e_invoice_status': 'Invalid',
                            'e_invoice_validation_response':  'Invalid Status'
                        })
                        view = self.env.ref('sh_message.sh_message_wizard')
                        view_id = view and view.id or False
                        context = dict(self._context or {})
                        context['message'] = 'Invalid Status'
                        return {
                            'name': "Error",
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.message.wizard',
                            'views': [(view.id, 'form')],
                            'view_id': view.id,
                            'target': 'new',
                            'context': context
                        }

                    if documentStatus == 'Valid':
                        # ////////////////////////////////////////////////
                        url = f"{apiBaseUrl}/api/v1.0/documents/{str(self.uuid)}/details"

                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {generatedAccessToken}'
                        }

                        document_detail_api_response = requests.request("GET", url, headers=headers)
                        if document_detail_api_response.status_code == 200:
                            document_detail_api_data = json.loads(document_detail_api_response.text)
                            document_status = document_detail_api_data['status']

                            if document_status == 'Valid':
                                self.write({
                                    'e_invoice_validation_response': 'Invoice Valid',
                                    'e_invoice_status': 'Valid'
                                })
                                self.einvoice_sending_time = fields.Datetime.now()
                                self.validation_datetime = fields.Datetime.now()
                                if not self.longid:
                                    self.longid = document_detail_api_data['longId']

                        # ////////////////////////////////////////////////

                                view = self.env.ref('sh_message.sh_message_wizard')
                                view_id = view and view.id or False
                                context = dict(self._context or {})
                                context['message'] = 'Invoice Validate Successfully'

                                return {
                                    'name': 'Success',
                                    'type': 'ir.actions.act_window',
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'sh.message.wizard',
                                    'views': [(view.id, 'form')],
                                    'view_id': view.id,
                                    'target': 'new',
                                    'context': context
                                }
                        else:
                            if document_detail_api_response.status_code == 401:
                                raise UserError(
                                    "The E-Invoice token has expired. Please renew the token from setting page to proceed.")


            else:
                if submission_api_response.status_code == 401:
                    raise UserError("The E-Invoice token has expired. Please renew the token from setting page to proceed.")
                else:
                    self.write({
                        # 'e_invoice_status': 'Invalid',
                        'e_invoice_validation_response': str(submission_api_response.text)
                    })
                    # self.e_invoice_status = 'Invalid'
                    # self.e_invoice_validation_response = str(submission_api_response.text)
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view and view.id or False
                    context = dict(self._context or {})
                    context['message'] = str(submission_api_response.text)

                    return {
                        'name': "Error",
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sh.message.wizard',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': context
                    }
        else:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = "Submission UID is required"

            return {
                'name': "Error",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context
            }

    @api.model
    def status_e_invoice_check(self):

        # company_id = self.env['res.users'].browse(self.env.context.get('uid')).company_id

        invoices = self.env['account.invoice'].sudo().search([('e_invoice_status','=','Submitted')])
        for invoice in invoices:
            invoice = self.env['account.invoice'].browse(invoice.id)
            if invoice:
                company_id = invoice.company_id.id
                # # Apply the company context and update the status_check_limit using update()
                # invoice.with_context(force_company=company_id).sudo().update({
                #     'status_check_limit': 12
                # })

            if invoice.submissionUid:
                apiBaseUrl = self.env['ir.config_parameter'].sudo().get_param(
                    'goexcel_einvoicing_my.login_url_taxpayer_einv')
                generatedAccessToken = invoice.company_id.authorization_token_einv

                    # self.env['ir.config_parameter'].sudo().get_param(
                    # 'goexcel_einvoicing_my.authorization_token_einv')


                url = f"{apiBaseUrl}/api/v1.0/documentsubmissions/{str(invoice.submissionUid)}"

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {generatedAccessToken}'
                }

                submission_api_response = requests.request("GET", url, headers=headers)



                current_value = invoice.status_check_limit or 0
                incremented_value = current_value + 1
                invoice.with_context(force_company=company_id).sudo().update({
                    'status_check_limit': incremented_value
                })

                if submission_api_response.status_code == 200:
                    documents_data = json.loads(submission_api_response.text)
                    overallStatus = documents_data['overallStatus']
                    if len(str(documents_data['documentSummary'][0]['longId'])) > 5:
                        invoice.with_context(force_company=company_id).sudo().update({
                            'longid': str(documents_data['documentSummary'][0]['longId'])
                        })

                        # qrcode_url_einv = request.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.qrcode_url_einv')
                        # qrcode_url_einv += f'{invoice.uuid}/share/{invoice.longid}'
                        # actual_invoice.sudo().e_invois_url = qrcode_url_einv
                        self._generate_qr_code()


                    if overallStatus == 'InProgress':

                        url = f"{apiBaseUrl}/api/v1.0/documents/{str(invoice.uuid)}/details"

                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {generatedAccessToken}'
                        }

                        document_detail_api_response = requests.request("GET", url, headers=headers)
                        if document_detail_api_response.status_code == 200:
                            document_detail_api_data = json.loads(document_detail_api_response.text)
                            document_status = document_detail_api_data['status']

                            if document_status == 'Valid':
                                invoice.write({
                                    'e_invoice_validation_response': 'Invoice Valid',
                                    'e_invoice_status': 'Valid'
                                })
                                invoice.einvoice_sending_time = fields.Datetime.now()
                                invoice.validation_datetime = fields.Datetime.now()
                                if not invoice.longid:
                                    invoice.longid = document_detail_api_data['longId']


                            if document_status == 'Invalid':
                                if invoice.status_check_limit <= 5:
                                    invoice.write({
                                        'e_invoice_status': 'Submitted',
                                        'e_invoice_validation_response': "Still Progress"
                                    })
                                else:
                                    invoice.write({
                                        'e_invoice_validation_response': 'Invoice In Valid',
                                        'e_invoice_status': 'Invalid'
                                    })



                            if document_status == 'Submitted':
                                if invoice.status_check_limit <= 5:
                                    invoice.write({
                                        'e_invoice_status': 'Submitted',
                                        'e_invoice_validation_response': "Still Progress"
                                    })
                                else:
                                    invoice.write({
                                        'e_invoice_validation_response': 'Invoice In Progress',
                                        'e_invoice_status': 'In_Progress'
                                    })
                        else:
                            if document_detail_api_response.status_code == 401:
                                raise UserError(
                                    "The E-Invoice token has expired. Please renew the token from setting page to proceed.")
                            else:
                                invoice.write({
                                    'e_invoice_validation_response': str(document_detail_api_response.text),
                                    # 'e_invoice_status': 'Invalid'
                                })

                    if overallStatus == 'Invalid':
                        if invoice.status_check_limit <= 5:
                            invoice.write({
                                'e_invoice_status': 'Submitted',
                                'e_invoice_validation_response': "Still Progress"
                            })
                        else:
                            # ///////////////////////////////////////////////////////////////////
                            url = f"{apiBaseUrl}/api/v1.0/documents/{str(invoice.uuid)}/details"

                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': f'Bearer {generatedAccessToken}'
                            }

                            document_detail_api_response = requests.request("GET", url, headers=headers)
                            if document_detail_api_response.status_code == 200:
                                document_detail_api_data = json.loads(document_detail_api_response.text)
                                document_status = document_detail_api_data['status']

                                if document_status == 'Invalid':
                                    invoice.write({
                                        'e_invoice_validation_response': str(document_detail_api_data['validationResults']['validationSteps']),
                                        'e_invoice_status': 'Invalid'
                                    })

                            else:
                                invoice.write({
                                    'e_invoice_validation_response': str(document_detail_api_response.text),
                                    'e_invoice_status': 'Invalid'
                                })

                            # /////////////////////////////////////////////////////////////////////

                    if overallStatus == 'Valid':
                        documentStatus = documents_data['documentSummary'][0]['status']

                        if documentStatus == 'Invalid':
                            if invoice.status_check_limit <= 5:
                                invoice.write({
                                    'e_invoice_status': 'Submitted',
                                    'e_invoice_validation_response': "Still Progress"
                                })
                            else:
                                invoice.write({
                                    'e_invoice_status': 'Invalid',
                                    'e_invoice_validation_response':  'Invalid Status'
                                })


                        if documentStatus == 'Valid':
                            # ///////////////////////////////////
                            url = f"{apiBaseUrl}/api/v1.0/documents/{str(invoice.uuid)}/details"

                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': f'Bearer {generatedAccessToken}'
                            }

                            document_detail_api_response = requests.request("GET", url, headers=headers)
                            if document_detail_api_response.status_code == 200:
                                document_detail_api_data = json.loads(document_detail_api_response.text)
                                document_status = document_detail_api_data['status']

                                if document_status == 'Valid':
                                    invoice.write({
                                        'e_invoice_validation_response': 'Invoice Valid',
                                        'e_invoice_status': 'Valid'
                                    })
                                    invoice.einvoice_sending_time = fields.Datetime.now()
                                    invoice.validation_datetime = fields.Datetime.now()
                                    if not invoice.longid:
                                        invoice.longid = document_detail_api_data['longId']

                            # ///////////////////////////////////
                            # invoice.write({
                            #     'e_invoice_status': 'Valid',
                            #     'e_invoice_validation_response': 'Invoice Valid'
                            # })
                            # invoice.einvoice_sending_time = fields.Datetime.now()
                            # invoice.validation_datetime = fields.Datetime.now()
                else:
                    if submission_api_response.status_code == 401:
                        raise UserError(
                            "The E-Invoice token has expired. Please renew the token from setting page to proceed.")
                    else:
                        if invoice.status_check_limit <= 5 :
                            invoice.write({
                                'e_invoice_status': 'Submitted',
                                'e_invoice_validation_response': "Still Progress"
                            })
                        else:
                            invoice.write({
                                'e_invoice_status': 'Invalid',
                                'e_invoice_validation_response': str(submission_api_response.text)
                            })


            # else:
            #     pass
                # invoice.write({
                #
                #
                #     'e_invoice_validation_response': 'Submission UID is required'
                # })
        return


    def generate_token(self):

        # company_ids = self.env['res.users'].browse(self.env.context.get('uid')).company_id
        company_ids = self.env['res.company'].sudo().search([('enable_e_invoice', '=', True)])

        for company_id in company_ids:

            if company_id.enable_e_invoice:

                login_url_taxpayer_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.login_url_taxpayer_einv')
                client_id_einv = company_id.client_id_einv
                    # self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.client_id_einv')
                client_secret_id_einv = company_id.client_secret_id_einv
                    # self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.client_secret_id_einv')

                if login_url_taxpayer_einv and client_id_einv and client_secret_id_einv:



                    url = f"{login_url_taxpayer_einv}/connect/token"

                    payload = {
                        'client_id': client_id_einv,
                        'client_secret': client_secret_id_einv,
                        'grant_type': 'client_credentials',
                        'scope': 'InvoicingAPI'
                    }
                    files = [

                    ]
                    headers = {
                        'client_id': client_id_einv,
                        'client_secret': client_secret_id_einv,
                        'grant_type': 'client_credentials',
                        'scope': 'InvoicingAPI'
                    }

                    response = requests.request("POST", url, data=payload)
                    if response.status_code == 200:

                        response_data = json.loads(response.text)
                        #

                        #

                        #
                        access_token = response_data['access_token']
                        expires_in = response_data['expires_in']
                        token_type = response_data['token_type']
                        scope = response_data['scope']

                        current_datetime = fields.Datetime.now()
                        one_hour_later = current_datetime + timedelta(hours=1)


                        company_id.sudo().write({
                            'authorization_token_einv': str(access_token)
                        })
                    else:
                        _logger.warning(f"Invalid Response {response.text}")



    @api.one
    def _generate_qr_code(self):
        if self.env.user.company_id.enable_e_invoice:
            qrcode_url_einv = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.qrcode_url_einv')
            if qrcode_url_einv:
                if self.uuid and self.longid:
                    qrcode_url_einv += f'/{self.uuid}/share/{self.longid}'
                    self.qr_image = self.generate_qr_code(qrcode_url_einv)
            else:
                raise UserError("Qr Code Url is required , Please Set in setting page")

    def check_einvoice_enable(self):
        for rec in self:
            rec.enable_e_invoice=self.env.user.company_id.enable_e_invoice

    def generate_qr_code(self , url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue())
        return qr_img

    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        # ////////////////////////// custom
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        self._ubl_add_header(xml_root, ns, version=version)

        self._ubl_add_invoice_period(xml_root, ns, version=version)


        self._ubl_add_order_reference(xml_root, ns, version=version)
        self._ubl_add_contract_document_reference(
            xml_root, ns, version=version)
        self._ubl_add_attachments(xml_root, ns, version=version)
        self._ubl_add_supplier_party(
            False, self.company_id, 'AccountingSupplierParty', xml_root, ns,
            version=version)
        self._ubl_add_customer_party(
            self.partner_id, False, 'AccountingCustomerParty', xml_root, ns,
            version=version)
        # the field 'partner_shipping_id' is defined in the 'sale' module
        if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
            self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
        # Put paymentmeans block even when invoice is paid ?
        payment_identifier = self.get_payment_identifier()
        self._ubl_add_payment_means(
            self.partner_bank_id, self.payment_mode_id, self.date_due,
            xml_root, ns, payment_identifier=payment_identifier,
            version=version)
        if self.payment_term_id:
            self._ubl_add_payment_terms(
                self.payment_term_id, xml_root, ns, version=version)
        self._ubl_add_tax_total(xml_root, ns, version=version)
        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        for iline in self.invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(
                xml_root, iline, line_number, ns, version=version)
        return xml_root


    @api.multi
    def _ubl_add_invoice_period(self, parent_node, ns, version='2.1'):
        period_root = etree.SubElement(
            parent_node, ns['cac'] + 'InvoicePeriod')
        issue_date = etree.SubElement(period_root, ns['cbc'] + 'StartDate')
        issue_date.text = self.date_invoice.strftime('%Y-%m-%d')
        end_date = etree.SubElement(period_root, ns['cbc'] + 'EndDate')
        end_date.text = self.date_due.strftime('%Y-%m-%d')


    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        self.ensure_one()
        cur_name = self.currency_id.name
        tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        prec = self.currency_id.decimal_places
        prec = prec if prec <= 2 else 2
        tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
        if not float_is_zero(self.amount_tax, precision_digits=prec):
            for tline in self.tax_line_ids:
                self._ubl_add_tax_subtotal(
                    tline.base, tline.amount, tline.tax_id, cur_name,
                    tax_total_node, ns, version=version)
    @api.multi
    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        ubl_version = etree.SubElement(
            parent_node, ns['cbc'] + 'UBLVersionID')
        ubl_version.text = version
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        doc_id.text = self.number
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        issue_date.text = self.date_invoice.strftime('%Y-%m-%d')

        issue_time = etree.SubElement(parent_node, ns['cbc'] + 'IssueTime')
        issue_time.text = self.date_invoice.strftime('%H:%M:%S %Z')

        type_code = etree.SubElement(
            parent_node, ns['cbc'] + 'InvoiceTypeCode')
        if self.type == 'out_invoice':
            type_code.text = '380'
        elif self.type == 'out_refund':
            type_code.text = '381'
        if self.comment:
            note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note.text = self.comment
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name

        tax_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'TaxCurrencyCode')
        tax_currency.text = self.currency_id.name

    def _ubl_add_suplier_tin(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        if self.name:
            order_ref = etree.SubElement(
                parent_node, ns['cac'] + 'Supplier TIN')
            order_ref_id = etree.SubElement(
                order_ref, ns['cbc'] + 'ID')
            order_ref_id.text = self.company_id.vat

    def cancel_e_invoice_odoo(self):
        if self.state not in ('open', 'paid'):
            raise UserError("Invoice must be in open or paid state")
        return super(AccountInvoice, self).action_invoice_cancel()
    @api.multi
    def action_invoice_cancel(self):
        if self.e_invoice_status in ['Submitted', 'In_Progress']:
            raise UserError(f"The invoice cannot be canceled because its E-Invoice status is currently in {self.e_invoice_status} state")


        current_time = datetime.datetime.now()
        if self.einvoice_sending_time and self.enable_e_invoice:
            invoice_time = self.einvoice_sending_time
            time_difference = current_time - invoice_time
            difference_in_hours = time_difference.total_seconds() / 3600

            if int(difference_in_hours) > 72:
                raise UserError("The invoice cannot be canceled now because the time difference is greater than 72 hours.")
            else:
                if self.uuid:
                    apiBaseUrl = self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.login_url_taxpayer_einv')
                    generatedAccessToken = self.company_id.authorization_token_einv
                        # self.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.authorization_token_einv')


                    url = f"{apiBaseUrl}/api/v1.0/documents/state/{self.uuid}/state"

                    if self.e_invoice_cancel_reason:

                        payload = json.dumps({
                            "status": "cancelled",
                            "reason": str(self.e_invoice_cancel_reason)
                        })
                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {generatedAccessToken}'
                        }

                        response = requests.request("PUT", url, headers=headers, data=payload)
                        if response.status_code == 200:
                            self.write({
                                'e_invoice_status': 'Cancelled',
                                'e_invoice_validation_response': 'Invoice Cancelled'
                            })

                            attachments = self.env['ir.attachment'].sudo().search(
                                [('res_model', '=', 'account.invoice'), ('res_id', '=', self.id),('type','=','binary')])

                            if attachments:
                                attachments.sudo().unlink()

                            return super(AccountInvoice, self).action_invoice_cancel()
                        else:
                            raise UserError(f"{ response.text}")


                            # view = self.env.ref('sh_message.sh_message_wizard')
                            # view_id = view and view.id or False
                            # context = dict(self._context or {})
                            # context['message'] = str(response.text)
                            #
                            # return {
                            #     'name': "Error",
                            #     'type': 'ir.actions.act_window',
                            #     'view_type': 'form',
                            #     'view_mode': 'form',
                            #     'res_model': 'sh.message.wizard',
                            #     'views': [(view.id, 'form')],
                            #     'view_id': view.id,
                            #     'target': 'new',
                            #     'context': context
                            # }


                    else:
                        raise UserError("Cancel Reason Required")
                        #
                        # view = self.env.ref('sh_message.sh_message_wizard')
                        # view_id = view and view.id or False
                        # context = dict(self._context or {})
                        # context['message'] = "Cancel Reason Required"
                        #
                        # return {
                        #     'name': "Error",
                        #     'type': 'ir.actions.act_window',
                        #     'view_type': 'form',
                        #     'view_mode': 'form',
                        #     'res_model': 'sh.message.wizard',
                        #     'views': [(view.id, 'form')],
                        #     'view_id': view.id,
                        #     'target': 'new',
                        #     'context': context
                        # }
        else:
            self.e_invoice_status = False
            self.submissionUid = ''
            self.uuid = ''
            self.e_invoice_validation_response = ''
            self.status_check_limit = 0

        return super(AccountInvoice,self).action_invoice_cancel()



    @api.multi
    def generate_ubl_xml_string(self, version='2.1'):
        # ///////////////////////custom
        self.ensure_one()
        # assert self.state in ('open', 'paid')
        if self.state not in ('open', 'paid'):
            raise UserError("Invoice must be in open or paid state")
        assert self.type in ('out_invoice', 'out_refund')
        _logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        xml_root = self.with_context(lang=lang). \
            generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8')
        self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
        _logger.debug(
            'Invoice UBL XML file generated for account invoice ID %d '
            '(state %s)', self.id, self.state)
        _logger.debug(xml_string.decode('utf-8'))
        return xml_string


class AccountinvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    measurement = fields.Char(string="Measurement",help="Percentage of deduction from the original price of a product or service")

