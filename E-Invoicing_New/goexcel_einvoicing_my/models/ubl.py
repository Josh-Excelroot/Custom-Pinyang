# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, file_open
from lxml import etree
from io import BytesIO
from tempfile import NamedTemporaryFile
import mimetypes
import logging
logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.generic import NameObject
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BaseUblInherit(models.AbstractModel):
    _inherit = 'base.ubl'
    _description = 'Common methods to generate and parse UBL XML files'


    # @api.model
    # def _ubl_get_party_identification(self, commercial_partner):
    #     '''This method is designed to be inherited in localisation modules
    #     Should return a dict with key=SchemeName, value=Identifier'''
    #     return {
    #         'TIN':commercial_partner.buyer_tin_no or 'C26001776000',
    #         'BRN':commercial_partner.buyer_sst_no or '1234166-T'
    #     }

    @api.model
    def _ubl_add_party_identification(self, commercial_partner, parent_node, ns, tag_type, version='2.1'):
        # id_dict = self._ubl_get_party_identification(commercial_partner)
        if tag_type == 'CustomerAssignedAccountID':
            if commercial_partner:
                party_identification_tin = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')
                party_identification_brn = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')




                party_identification_tin_id = etree.SubElement(
                    party_identification_tin, ns['cbc'] + 'ID',
                    schemeID="TIN")
                if commercial_partner.buyer_tin_no:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            if self.type == 'in_invoice' or self.type == 'in_refund':
                                party_identification_tin_id.text = 'EI00000000030'
                            else:
                                party_identification_tin_id.text = 'EI00000000020'
                        else:
                            party_identification_tin_id.text = commercial_partner.buyer_tin_no
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                else:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            if self.type == 'in_invoice' or self.type == 'in_refund':
                                party_identification_tin_id.text = 'EI00000000030'
                            else:
                                party_identification_tin_id.text = 'EI00000000020'
                        else:
                            raise UserError(_('UBL: missing TIN on partner {}').format(commercial_partner.name))
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                party_identification_brn_id = etree.SubElement(
                    party_identification_brn, ns['cbc'] + 'ID',
                    schemeID="BRN")
                if commercial_partner.brn_no:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            party_identification_brn_id.text = 'NA'
                        else:
                            party_identification_brn_id.text = commercial_partner.brn_no
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                else:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            party_identification_brn_id.text = 'NA'
                        else:
                            raise UserError(_('UBL: missing BRN on partner {}').format(commercial_partner.name))
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
# /////////////////////////////////////SST
                party_identification_sst = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')

                party_identification_sst_id = etree.SubElement(
                    party_identification_sst, ns['cbc'] + 'ID',
                    schemeID="SST")
                if commercial_partner.buyer_sst_no:
                    party_identification_sst_id.text = commercial_partner.buyer_sst_no
                else:
                    party_identification_sst_id.text = 'NA'

                # /////////////////////////////////////TTX
                party_identification_ttx = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')

                party_identification_ttx_id = etree.SubElement(
                    party_identification_ttx, ns['cbc'] + 'ID',
                    schemeID="TTX")
                if commercial_partner.ttx_no:
                    party_identification_ttx_id.text = commercial_partner.ttx_no
                else:
                    party_identification_ttx_id.text = 'NA'


            return

        if tag_type == 'SupplierAssignedAccountID':
            if commercial_partner:
                party_identification_tin = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')
                party_identification_brn = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')


                party_identification_tin_id = etree.SubElement(
                    party_identification_tin, ns['cbc'] + 'ID',
                    schemeID="TIN")
                if commercial_partner.buyer_tin_no:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            if self.type == 'in_invoice' or self.type == 'in_refund':
                                party_identification_tin_id.text = 'EI00000000030'
                            else:
                                party_identification_tin_id.text = 'EI00000000020'
                        else:
                            party_identification_tin_id.text = commercial_partner.buyer_tin_no
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                else:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            if self.type == 'in_invoice'or self.type == 'in_refund':
                                party_identification_tin_id.text = 'EI00000000030'
                            else:
                                party_identification_tin_id.text = 'EI00000000020'
                        else:
                            raise UserError(_('UBL: missing TIN on partner {}').format(commercial_partner.name))
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                party_identification_brn_id = etree.SubElement(
                    party_identification_brn, ns['cbc'] + 'ID',
                    schemeID="BRN")
                if commercial_partner.brn_no:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            party_identification_brn_id.text = 'NA'
                        else:
                            party_identification_brn_id.text = commercial_partner.brn_no
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')
                else:
                    if commercial_partner.country_id:
                        if commercial_partner.country_id.name.lower() != 'Malaysia'.lower():
                            party_identification_brn_id.text = 'NA'
                        else:
                            raise UserError(_('UBL: missing BRN on partner {}').format(commercial_partner.name))
                    else:
                        raise UserError(f'UBL: missing Country on partner {commercial_partner.name}')


# ////////////////////////SST

                party_identification_sst = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')

                party_identification_sst_id = etree.SubElement(
                    party_identification_sst, ns['cbc'] + 'ID',
                    schemeID="SST")
                if commercial_partner.buyer_sst_no:
                    party_identification_sst_id.text = commercial_partner.buyer_sst_no
                else:
                    party_identification_sst_id.text = 'NA'

    # ////////////////////////////TTX
                party_identification_ttx = etree.SubElement(
                    parent_node, ns['cac'] + 'PartyIdentification')

                party_identification_ttx_id = etree.SubElement(
                    party_identification_ttx, ns['cbc'] + 'ID',
                    schemeID="TTX")
                if commercial_partner.ttx_no:
                    party_identification_ttx_id.text = commercial_partner.ttx_no
                else:
                    party_identification_ttx_id.text = 'NA'
            return



    # @api.model
    # def _ubl_add_party_legal_entity(
    #         self, commercial_partner, parent_node, ns, version='2.1'):
    #     party_legal_entity = etree.SubElement(
    #         parent_node, ns['cac'] + 'PartyLegalEntity')
    #     registration_name = etree.SubElement(
    #         party_legal_entity, ns['cbc'] + 'RegistrationName')
    #     registration_name.text = commercial_partner.name
    #     self._ubl_add_address(
    #         commercial_partner, 'RegistrationAddress', party_legal_entity,
    #         ns, version=version)
    #     self._ubl_add_party_identification(commercial_partner,parent_node,ns,version)
    #
    # def _ubl_add_party_identification(self,partner,parent_node,ns,version):
    #     party_identification = etree.SubElement(
    #         parent_node, ns['cac'] + 'PartyIdentification')
    #     identity_tin_id = etree.SubElement(
    #         party_identification, ns['cbc'] + 'ID', schemeID='TIN',
    #         schemeAgencyID='6')
    #     identity_tin_id.text = partner.vat
    #
    #     identity_sst_id = etree.SubElement(
    #         party_identification, ns['cbc'] + 'ID', schemeID='SST',
    #         schemeAgencyID='6')
    #     identity_sst_id.text = partner.supplier_sst_no
    #
    #     identity_ttx_id = etree.SubElement(
    #         party_identification, ns['cbc'] + 'ID', schemeID='TTX',
    #         schemeAgencyID='6')
    #     identity_ttx_id.text = partner.supplier_tourism_tax_reg_no
    #
    #     identity_nric_id = etree.SubElement(
    #         party_identification, ns['cbc'] + 'ID', schemeID='NRIC',
    #         schemeAgencyID='6')
    #     identity_nric_id.text = partner.supplier_registration_no
