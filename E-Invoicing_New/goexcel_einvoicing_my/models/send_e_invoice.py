import requests
import json
import base64
from lxml import etree
import hashlib
import re
import hashlib
from xml.etree import ElementTree as ET
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


def send_invoice(object):


    attachments = object.env['ir.attachment'].sudo().search([('res_model', '=', 'account.invoice'), ('res_id', '=', object.id)])
    if len(attachments) > 1:
        attachments = object.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'account.invoice'), ('res_id', '=', object.id)])[0]
    else:
        attachments = object.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'account.invoice'), ('res_id', '=', object.id)])

    # _logger.warning(f"Attachment data ============================= {attachments}")
    # _logger.warning(f"Attachment data ============================= {attachments.datas}")
    # _logger.warning(f"Attachment Create ============================= {attachments.read()[0]}")



    binary_data = base64.b64decode(attachments.datas)
    cleaned_bytes_data = binary_data.replace(b'\n', b'')
    binary_data_encdoe = base64.b64encode(cleaned_bytes_data)

    base64_string = binary_data_encdoe.decode('utf-8')


    root = etree.fromstring(cleaned_bytes_data)
    xml_string = etree.tostring(root, encoding='utf-8', method='xml')

    # Compute the SHA-256 hash
    hash_object = hashlib.sha256(xml_string)
    hex_dig = hash_object.hexdigest()

    token_expiry_time = object.env['ir.config_parameter'].sudo().get_param('token_expiry_time')
    apiBaseUrl = object.env['ir.config_parameter'].sudo().get_param('goexcel_einvoicing_my.login_url_taxpayer_einv')
    generatedAccessToken = object.company_id.authorization_token_einv

    if not generatedAccessToken:
        raise UserError("First Generate Access Token Form Settings Page")


    url = f"{apiBaseUrl}/api/v1.0/documentsubmissions"

    payload = json.dumps({
        "documents": [
            {
                "format": "XML",
                "documentHash": hex_dig,
                "codeNumber": object.number,
                "document":str(base64_string),
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {generatedAccessToken}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response
    # return 202

