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
import json
import os

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.generic import NameObject
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BaseUbl(models.AbstractModel):

    _name = 'base.ubl'
    _description = 'Common methods to generate and parse UBL XML files'

    # ==================== METHODS TO GENERATE UBL files

    @api.model
    def _ubl_add_country(self, country, parent_node, ns, version='2.1'):

        json_file_path = 'static/countries.json'
        full_path = os.path.join(os.path.dirname(__file__), '../', json_file_path)

        with open(full_path, 'r') as json_file:
            country_data = json.load(json_file)


        country_dict = {state['Country'].lower(): state['Code'] for state in country_data}

        country_root = etree.SubElement(parent_node, ns['cac'] + 'Country')
        country_code = etree.SubElement(
            country_root, ns['cbc'] + 'IdentificationCode')
        # country_code.text = country.code
        country_name = etree.SubElement(
            country_root, ns['cbc'] + 'Name')
        if country:
            # for contry in country_dict:
            #     if contry['Country'].lower() == country.name.lower():
            #         country_name.text = contry['Code']
            #         break
                country_name.text = country.name
                country_code.text = country_dict.get(country.name.lower(), '')
                # country_name.text = country.name
        # country_root = etree.SubElement(parent_node, ns['cac'] + 'Country')
        # einvoice_country = self.env['einvoice.res.country'].search([('country_name' ,'=', country.name.upper())])
        # if einvoice_country:
        #     country_code = etree.SubElement(
        #         country_root, ns['cbc'] + 'IdentificationCode')
        #     country_code.text = einvoice_country.country_code
        #     country_name = etree.SubElement(
        #         country_root, ns['cbc'] + 'Name')
        #     country_name.text = einvoice_country.country_name
        # else:
        #     raise UserError(f'UBL: country name on partner is not correct or missing')

    @api.model
    def _ubl_add_address(
            self, partner, node_name, parent_node, ns, tag_type ,version='2.1'):



        states_dict = {
                    'johor': '01',
                    'kedah': '02',
                    'kelantan': '03',
                    'melaka': '04',
                    'negeri sembilan': '05',
                    'pahang': '06',
                    'pulau pinang': '07',
                    'perak': '08',
                    'perlis': '09',
                    'selangor': '10',
                    'terengganu': '11',
                    'sabah': '12',
                    'sarawak': '13',
                    'kuala lumpur': '14',
                    'labuan': '15',
                    'putrajaya': '16',
                    'not applicable': '17'
                }

        if tag_type == 'CustomerAssignedAccountID':
            # ////// company value partner id =1
            address = etree.SubElement(parent_node, ns['cac'] + node_name)
            if partner.street2:
                streetname = etree.SubElement(
                    address, ns['cbc'] + 'StreetName')
                streetname.text = partner.street2
            # if partner.street2:
            #     addstreetname = etree.SubElement(
            #         address, ns['cbc'] + 'AdditionalStreetName')
            #     addstreetname.text = partner.street2
            if hasattr(partner, 'street3') and partner.street3:
                blockname = etree.SubElement(
                    address, ns['cbc'] + 'BlockName')
                blockname.text = partner.street3
            if partner.city:
                city = etree.SubElement(address, ns['cbc'] + 'CityName')
                city.text = partner.city
            else:
                raise UserError(f'UBL: Please fill in the "City" field in the address for the customer or vendor. {partner.name}')
            if partner.zip:
                zip = etree.SubElement(address, ns['cbc'] + 'PostalZone')
                zip.text = partner.zip
            if partner.country_id.name.lower() == 'Malaysia'.lower():
                if partner.state_id:
                    state = etree.SubElement(
                        address, ns['cbc'] + 'CountrySubentity')
                    state.text = partner.state_id.name
                    state_code = etree.SubElement(
                        address, ns['cbc'] + 'CountrySubentityCode')
                    # state_code.text = partner.state_id.code
                    # for state in states_data:
                    #     if state['State'].lower() == partner.state_id.name.lower():
                    #         state_code.text = state['Code']
                    #         break
                    state_code.text = states_dict.get(partner.state_id.name.lower(), '17')

                    # if len(partner.state_id.code) < 2 :
                    #     state_code.text = '0'+partner.state_id.code
                    # else:
                    #     state_code.text = partner.state_id.code

                else:
                    raise UserError(f'UBL: Please fill in the "State" field in the address for the customer or vendor {partner.name}')
            else:
                state = etree.SubElement(
                    address, ns['cbc'] + 'CountrySubentity')
                state.text = 'Not Applicable'
                state_code = etree.SubElement(
                    address, ns['cbc'] + 'CountrySubentityCode')
                state_code.text = '17'


            if partner.street:
                address_line = etree.SubElement(
                    address, ns['cac'] + 'AddressLine')

                address_line_lot = etree.SubElement(
                    address_line, ns['cbc'] + 'Line')

                address_line_lot.text = partner.street
            else:
                raise UserError(f'UBL: Please fill in the "Street" field in the address for the customer or vendor {partner.name}')

            if partner.country_id:
                self._ubl_add_country(
                    partner.country_id, address, ns, version=version)
            else:
                raise UserError(f'UBL: Please fill in the "Country" field in the address for the customer or vendor  {partner.name}')
                logger.warning('UBL: Please fill in the "Country" field in the address for the customer or vendor %s', partner.name)

        if tag_type == 'SupplierAssignedAccountID':
            # ////// self,parther
            address = etree.SubElement(parent_node, ns['cac'] + node_name)
            if partner.street2:
                streetname = etree.SubElement(
                    address, ns['cbc'] + 'StreetName')
                streetname.text = partner.street2
            # if partner.street2:
            #     addstreetname = etree.SubElement(
            #         address, ns['cbc'] + 'AdditionalStreetName')
            #     addstreetname.text = partner.street2
            if hasattr(partner, 'street3') and partner.street3:
                blockname = etree.SubElement(
                    address, ns['cbc'] + 'BlockName')
                blockname.text = partner.street3
            if partner.city:
                city = etree.SubElement(address, ns['cbc'] + 'CityName')
                city.text = partner.city
            else:
                raise UserError(
                    f'UBL: Please fill in the "City" field in the address for the customer or vendor. {partner.name}')
            if partner.zip:
                zip = etree.SubElement(address, ns['cbc'] + 'PostalZone')
                zip.text = partner.zip
            # if partner.country_id.name == 'Malaysia':
            if partner.country_id.name.lower() == 'Malaysia'.lower():
                if partner.state_id:
                    state = etree.SubElement(
                        address, ns['cbc'] + 'CountrySubentity')
                    state.text = partner.state_id.name
                    state_code = etree.SubElement(
                        address, ns['cbc'] + 'CountrySubentityCode')
                    # for state in states_data:
                    #     if state['State'].lower() == partner.state_id.name.lower():
                    #         state_code.text = state['Code']
                    #         break
                    state_code.text = states_dict.get(partner.state_id.name.lower(), '17')

                    # if len(partner.state_id.code) < 2 :
                    #     state_code.text = '0'+partner.state_id.code
                    # else:
                    #     state_code.text = partner.state_id.code


                else:
                    raise UserError(f'UBL: Please fill in the "State" field in the address for the customer or vendor  {partner.name}')
            else:
                state = etree.SubElement(
                    address, ns['cbc'] + 'CountrySubentity')
                state.text = 'Not Applicable'
                state_code = etree.SubElement(
                    address, ns['cbc'] + 'CountrySubentityCode')
                state_code.text = '17'

            if partner.street:
                address_line = etree.SubElement(
                    address, ns['cac'] + 'AddressLine')

                address_line_lot = etree.SubElement(
                    address_line, ns['cbc'] + 'Line')

                address_line_lot.text = partner.street
            else:
                raise UserError(f'UBL: Please fill in the "Street" field in the address for the customer or vendor {partner.name}')

            if partner.country_id:
                self._ubl_add_country(
                    partner.country_id, address, ns, version=version)
            else:
                raise UserError(f'UBL: Please fill in the "Country" field in the address for the customer or vendor {partner.name}')
                logger.warning('UBL: Please fill in the "Country" field in the address for the customer or vendor %s', partner.name)

    @api.model
    def _ubl_get_contact_id(self, partner):
        return False

    @api.model
    def _ubl_add_contact(
            self, partner, parent_node, ns, node_name='Contact',
            version='2.1'):
        contact = etree.SubElement(parent_node, ns['cac'] + node_name)
        contact_id_text = self._ubl_get_contact_id(partner)
        if contact_id_text:
            contact_id = etree.SubElement(contact, ns['cbc'] + 'ID')
            contact_id.text = contact_id_text
        # if partner.parent_id:
        #     contact_name = etree.SubElement(contact, ns['cbc'] + 'Name')
        #     contact_name.text = partner.name
        phone = partner.phone or partner.commercial_partner_id.phone
        if phone:
            telephone = etree.SubElement(contact, ns['cbc'] + 'Telephone')
            telephone.text = phone
        else:
            raise UserError(f'UBL: missing Phone number on partner {partner.name}')
        email = partner.email or partner.commercial_partner_id.email
        if email:
            electronicmail = etree.SubElement(
                contact, ns['cbc'] + 'ElectronicMail')
            electronicmail.text = email

    @api.model
    def _ubl_add_language(self, lang_code, parent_node, ns, version='2.1'):
        langs = self.env['res.lang'].sudo().search([('code', '=', lang_code)])
        if not langs:
            return
        lang = langs[0]
        lang_root = etree.SubElement(parent_node, ns['cac'] + 'Language')
        lang_name = etree.SubElement(lang_root, ns['cbc'] + 'Name')
        lang_name.text = lang.name
        lang_code = etree.SubElement(lang_root, ns['cbc'] + 'LocaleCode')
        lang_code.text = lang.code

    @api.model
    def _ubl_get_party_identification(self, commercial_partner):
        '''This method is designed to be inherited in localisation modules
        Should return a dict with key=SchemeName, value=Identifier'''
        return {}

    @api.model
    def _ubl_add_party_identification(
            self, commercial_partner, parent_node, ns, version='2.1'):
        id_dict = self._ubl_get_party_identification(commercial_partner)
        if id_dict:
            party_identification = etree.SubElement(
                parent_node, ns['cac'] + 'PartyIdentification')
            for scheme_name, party_id_text in id_dict.items():
                party_identification_id = etree.SubElement(
                    party_identification, ns['cbc'] + 'ID',
                    schemeID=scheme_name)
                party_identification_id.text = party_id_text
        return

    @api.model
    def _ubl_get_tax_scheme_dict_from_partner(self, commercial_partner):
        tax_scheme_dict = {
            'id': 'VAT',
            'name': False,
            'type_code': False,
            }
        return tax_scheme_dict

    @api.model
    def _ubl_add_party_tax_scheme(
            self, commercial_partner, parent_node, ns, version='2.1'):
        if commercial_partner.vat:
            party_tax_scheme = etree.SubElement(
                parent_node, ns['cac'] + 'PartyTaxScheme')
            registration_name = etree.SubElement(
                party_tax_scheme, ns['cbc'] + 'RegistrationName')
            registration_name.text = commercial_partner.name
            company_id = etree.SubElement(
                party_tax_scheme, ns['cbc'] + 'CompanyID')
            company_id.text = commercial_partner.sanitized_vat
            tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_partner(
                commercial_partner)
            self._ubl_add_tax_scheme(
                tax_scheme_dict, party_tax_scheme, ns, version=version)

    @api.model
    def _ubl_add_party_legal_entity(
            self, commercial_partner, parent_node, ns, version='2.1'):
        party_legal_entity = etree.SubElement(
            parent_node, ns['cac'] + 'PartyLegalEntity')
        registration_name = etree.SubElement(
            party_legal_entity, ns['cbc'] + 'RegistrationName')
        if commercial_partner.consolidated_general_public:
            registration_name.text = "General Public"
        else:
            try:
                if commercial_partner.short_name:
                    registration_name.text = commercial_partner.short_name
                else:
                    registration_name.text = commercial_partner.name
            except:
                registration_name.text = commercial_partner.name
        self._ubl_add_address(
            commercial_partner, 'RegistrationAddress', party_legal_entity,
            ns, tag_type='CustomerAssignedAccountID' ,  version=version)

    @api.model
    def _ubl_add_party(
            self, partner, company, node_name, parent_node, ns,tag_type, version='2.1'):
        commercial_partner = partner.commercial_partner_id
        party = etree.SubElement(parent_node, ns['cac'] + node_name)

        if self.type == 'in_invoice' or self.type == 'in_refund':
            if tag_type == 'CustomerAssignedAccountID':
                if commercial_partner.msic_code:
                    industry_classification_code = etree.SubElement(party, ns['cbc'] + 'IndustryClassificationCode',name=f"{commercial_partner.msic_code.msic_name}")
                    industry_classification_code.text = f"{commercial_partner.msic_code.msic_code}"
                else:
                    if (self.type == 'in_invoice' or self.type == 'in_refund') and commercial_partner.country_id.name != 'Malaysia':
                        industry_classification_code = etree.SubElement(party, ns['cbc'] + 'IndustryClassificationCode',name=f"{commercial_partner.msic_code.msic_name}")
                        msic_code = self.env['msic.code'].sudo().search([('msic_code', '=', '00000')])
                        industry_classification_code.text = msic_code.msic_code
                    else:
                        raise UserError(f'UBL: missing MSIC Code on partner {commercial_partner.name}')
        else:
            if tag_type == 'CustomerAssignedAccountID':
                # if self.e_invoice_type == 'Consolidate':
                if self.consolidate_invoice:
                    if self.consolidate_msic_code:
                        industry_classification_code = etree.SubElement(party, ns['cbc'] + 'IndustryClassificationCode',name=f"{self.consolidate_msic_code_name}")
                        industry_classification_code.text = f"{self.consolidate_msic_code_value}"
                    else:
                        raise UserError(f'UBL: missing MSIC Code on Invoice {self.name}')

                else:
                    if commercial_partner.msic_code:
                        industry_classification_code = etree.SubElement(party, ns['cbc'] + 'IndustryClassificationCode',name=f"{commercial_partner.msic_code.msic_name}")
                        industry_classification_code.text = f"{commercial_partner.msic_code.msic_code}"
                    else:
                        raise UserError(f'UBL: missing MSIC Code on partner {commercial_partner.name}')

        # CustomerAssignedAccountID  =supplier
        # SupplierAssignedAccountID = customer

        if self.type == 'in_invoice' or self.type == 'in_refund':
            if tag_type == 'CustomerAssignedAccountID':
                self._ubl_add_party_identification(
                    commercial_partner, party, ns, tag_type = 'CustomerAssignedAccountID' , version=version)
            if tag_type == 'SupplierAssignedAccountID':
                self._ubl_add_party_identification(
                    self.company_id.partner_id, party, ns, tag_type='SupplierAssignedAccountID', version=version)
        else:
            if tag_type == 'CustomerAssignedAccountID':
                self._ubl_add_party_identification(
                    commercial_partner, party, ns, tag_type = 'CustomerAssignedAccountID' , version=version)
            if tag_type == 'SupplierAssignedAccountID':
                self._ubl_add_party_identification(
                    self.partner_id, party, ns, tag_type='SupplierAssignedAccountID', version=version)



        party_name = etree.SubElement(party, ns['cac'] + 'PartyName')
        name = etree.SubElement(party_name, ns['cbc'] + 'Name')
        if commercial_partner.consolidated_general_public:
            name.text = "General Public"
        else:
            name.text = commercial_partner.name
        if partner.lang:
            self._ubl_add_language(partner.lang, party, ns, version=version)

        if self.type == 'in_invoice' or self.type == 'in_refund':
            if tag_type == 'CustomerAssignedAccountID':
                self._ubl_add_address(
                    commercial_partner, 'PostalAddress', party, ns, tag_type="CustomerAssignedAccountID", version=version ,)
            if tag_type == 'SupplierAssignedAccountID':
                self._ubl_add_address(
                    self.company_id.partner_id, 'PostalAddress', party, ns, tag_type="SupplierAssignedAccountID" , version=version ,)

            if tag_type == 'SupplierAssignedAccountID':
                party_legal_entity = etree.SubElement(party, ns['cac'] + 'PartyLegalEntity')
                registration_name = etree.SubElement(party_legal_entity, ns['cbc'] + 'RegistrationName')
                if self.company_id.partner_id.consolidated_general_public:
                    registration_name.text = "General Public"
                else:
                    try:
                        if self.company_id.partner_id.short_name:
                            registration_name.text = self.company_id.partner_id.short_name
                        else:
                            registration_name.text = self.company_id.partner_id.name
                    except:
                        registration_name.text = self.company_id.partner_id.name

        else:
            if tag_type == 'CustomerAssignedAccountID':
                self._ubl_add_address(
                    commercial_partner, 'PostalAddress', party, ns, tag_type="CustomerAssignedAccountID", version=version ,)
            if tag_type == 'SupplierAssignedAccountID':
                self._ubl_add_address(
                    self.partner_id, 'PostalAddress', party, ns, tag_type="SupplierAssignedAccountID" , version=version ,)

            if tag_type == 'SupplierAssignedAccountID':
                party_legal_entity = etree.SubElement(party, ns['cac'] + 'PartyLegalEntity')
                registration_name = etree.SubElement(party_legal_entity, ns['cbc'] + 'RegistrationName')
                if self.partner_id.consolidated_general_public:
                    registration_name.text = "General Public"
                else:
                    try:
                        if self.partner_id.short_name:
                            registration_name.text = self.partner_id.short_name
                        else:
                            registration_name.text = self.partner_id.name
                    except:
                        registration_name.text = self.partner_id.name

        # else:
        #     party_legal_entity = etree.SubElement(party, ns['cac'] + 'PartyLegalEntity')
        #     registration_name = etree.SubElement(party_legal_entity, ns['cbc'] + 'RegistrationName')
        #     registration_name.text = "XYZ Group"

        # self._ubl_add_party_tax_scheme(
        #     commercial_partner, party, ns, version=version)
        if company:
            self._ubl_add_party_legal_entity(
                commercial_partner, party, ns, version='2.1')
        self._ubl_add_contact(partner, party, ns, version=version)

    @api.model
    def _ubl_add_customer_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        """Please read the docstring of the method _ubl_add_supplier_party"""
        # //customer
        if company:
            if partner:
                assert partner.commercial_partner_id == company.partner_id,\
                    'partner is wrong'
            else:
                partner = company.partner_id
        customer_party_root = etree.SubElement(
            parent_node, ns['cac'] + node_name)
        if not company and partner.commercial_partner_id.ref:
            customer_ref = etree.SubElement(
                customer_party_root, ns['cbc'] + 'SupplierAssignedAccountID')
            customer_ref.text = partner.commercial_partner_id.ref
        if self.type == 'in_invoice' or self.type == 'in_refund':
            self._ubl_add_party(
                self.company_id.partner_id, company, 'Party', customer_party_root, ns, tag_type="SupplierAssignedAccountID",
                version=version)

        else:
            self._ubl_add_party(
                partner, company, 'Party', customer_party_root, ns,tag_type="SupplierAssignedAccountID",
                version=version)
            # TODO: rewrite support for AccountingContact + add DeliveryContact
        # Additional optional args
        if partner and not company and partner.parent_id:
            self._ubl_add_contact(
                partner, customer_party_root, ns,
                node_name='AccountingContact', version=version)

    @api.model
    def _ubl_add_supplier_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        """The company argument has been added to properly handle the
        'ref' field.
        In Odoo, we only have one ref field, in which we are supposed
        to enter the reference that our company gives to its
        customers/suppliers. We unfortunately don't have a native field to
        enter the reference that our suppliers/customers give to us.
        So, to set the fields CustomerAssignedAccountID and
        SupplierAssignedAccountID, I need to know if the partner for
        which we want to build the party block is our company or a
        regular partner:
        1) if it is a regular partner, call the method that way:
            self._ubl_add_supplier_party(partner, False, ...)
        2) if it is our company, call the method that way:
            self._ubl_add_supplier_party(False, company, ...)
        """
        # ////suplier
        if company:
            if partner:
                assert partner.commercial_partner_id == company.partner_id,\
                    'partner is wrong'
            else:
                partner = company.partner_id
        supplier_party_root = etree.SubElement(
            parent_node, ns['cac'] + node_name)
        if not company and partner.commercial_partner_id.ref:
            supplier_ref = etree.SubElement(
                supplier_party_root, ns['cbc'] + 'CustomerAssignedAccountID')
            supplier_ref.text = partner.commercial_partner_id.ref
        if self.type == 'in_invoice' or self.type == 'in_refund':
            self._ubl_add_party(
                self.partner_id, company, 'Party', supplier_party_root, ns, tag_type="CustomerAssignedAccountID",
                version=version)
        else:
            self._ubl_add_party(
                partner, company, 'Party', supplier_party_root, ns,tag_type="CustomerAssignedAccountID",
                version=version )

    @api.model
    def _ubl_add_delivery(
            self, delivery_partner, parent_node, ns, version='2.1'):
        delivery = etree.SubElement(parent_node, ns['cac'] + 'Delivery')
        delivery_location = etree.SubElement(
            delivery, ns['cac'] + 'DeliveryLocation')
        self._ubl_add_address(
            delivery_partner, 'Address', delivery_location, ns, tag_type="SupplierAssignedAccountID" ,
            version=version)
        self._ubl_add_party(
            delivery_partner, False, 'DeliveryParty', delivery, ns ,tag_type="SupplierAssignedAccountID",
            version=version)

    @api.model
    def _ubl_add_delivery_terms(
            self, incoterm, parent_node, ns, version='2.1'):
        delivery_term = etree.SubElement(
            parent_node, ns['cac'] + 'DeliveryTerms')
        delivery_term_id = etree.SubElement(
            delivery_term, ns['cbc'] + 'ID',
            schemeAgencyID='6', schemeID='INCOTERM')
        delivery_term_id.text = incoterm.code

    @api.model
    def _ubl_add_payment_terms(
            self, payment_term, parent_node, ns, version='2.1'):
        pay_term_root = etree.SubElement(
            parent_node, ns['cac'] + 'PaymentTerms')
        pay_term_note = etree.SubElement(
            pay_term_root, ns['cbc'] + 'Note')
        pay_term_note.text = payment_term.name

    @api.model
    def _ubl_add_line_item(
            self, line_number, name, product, type, quantity, uom, parent_node,
            ns, seller=False, currency=False, price_subtotal=False,
            qty_precision=3, price_precision=2, version='2.1'):
        line_item = etree.SubElement(
            parent_node, ns['cac'] + 'LineItem')
        line_item_id = etree.SubElement(line_item, ns['cbc'] + 'ID')
        line_item_id.text = str(line_number)
        if not uom.unece_code:
            raise UserError(_("Missing UNECE code on unit of measure '%s'")% uom.name)
        quantity_node = etree.SubElement(
            line_item, ns['cbc'] + 'Quantity',
            unitCode=uom.unece_code)
        quantity_node.text = str(quantity)
        if currency and price_subtotal:
            line_amount = etree.SubElement(
                line_item, ns['cbc'] + 'LineExtensionAmount',
                currencyID=currency.name)
            line_amount.text = str(price_subtotal)
            price_unit = 0.0
            # Use price_subtotal/qty to compute price_unit to be sure
            # to get a *tax_excluded* price unit
            if not float_is_zero(quantity, precision_digits=qty_precision):
                price_unit = float_round(
                    price_subtotal / float(quantity),
                    precision_digits=price_precision)
            price = etree.SubElement(
                line_item, ns['cac'] + 'Price')
            price_amount = etree.SubElement(
                price, ns['cbc'] + 'PriceAmount',
                currencyID=currency.name)
            price_amount.text = str(price_unit)
            base_qty = etree.SubElement(
                price, ns['cbc'] + 'BaseQuantity',
                unitCode=uom.unece_code)
            base_qty.text = '1'  # What else could it be ?
        self._ubl_add_item(
            name, product, line_item, ns, type=type, seller=seller,
            version=version)

    @api.model
    def _ubl_add_item(
            self, name, product, parent_node, ns, type='purchase',
            seller=False, version='2.1'):
        """Beware that product may be False (in particular on invoices)"""
        assert type in ('sale', 'purchase'), 'Wrong type param'
        assert name, 'name is a required arg'
        item = etree.SubElement(parent_node, ns['cac'] + 'Item')
        product_name = False
        seller_code = False
        if product:
            if type == 'purchase':
                if seller:
                    sellers = product._select_seller(
                        partner_id=seller, quantity=0.0, date=None,
                        uom_id=False)
                    if sellers:
                        product_name = sellers[0].product_name
                        seller_code = sellers[0].product_code
            if not seller_code:
                seller_code = product.default_code
            if not product_name:
                variant = ", ".join(
                    [v.name for v in product.attribute_value_ids])
                product_name = variant and "%s (%s)" % (product.name, variant)\
                    or product.name
        description = etree.SubElement(item, ns['cbc'] + 'Description')
        description.text = name

        # if self.e_invoice_type == 'Consolidate':
        if self.consolidate_invoice:
            commodity_classification = etree.SubElement(item, ns['cac'] + 'CommodityClassification')
            item_classificationCode = etree.SubElement(commodity_classification, ns['cbc'] + 'ItemClassificationCode' , listID="CLASS")
            product_classification_item = self.env['classification.type'].sudo().search([('classification_name' ,'=', 'Consolidated e-Invoice')])
            if product_classification_item:
                item_classificationCode.text = product_classification_item.classification_code
            else:
                raise UserError(f"For Consolidated e-Invoice classification code of product is missing")

        else:
            commodity_classification = etree.SubElement(item, ns['cac'] + 'CommodityClassification')
            item_classificationCode = etree.SubElement(commodity_classification, ns['cbc'] + 'ItemClassificationCode',
                                                       listID="CLASS")

            if self.type == 'in_invoice':
                if product.self_bill_classification_item.classification_code:
                    item_classificationCode.text = product.self_bill_classification_item.classification_code
                else:
                    if product.classification_item.classification_code:
                        item_classificationCode.text = product.classification_item.classification_code
                    else:
                        raise UserError(
                            f"Classification code of product is missing , Please Set in Product {product.name}")
            else:
                if product.classification_item.classification_code:
                    item_classificationCode.text = product.classification_item.classification_code
                else:
                    raise UserError(f"Classification code of product is missing , Please Set in Product {product.name}")


        # name_node = etree.SubElement(item, ns['cbc'] + 'Name')
        # name_node.text = product_name or name.split('\n')[0]
        # if seller_code:
        #     seller_identification = etree.SubElement(
        #         item, ns['cac'] + 'SellersItemIdentification')
        #     seller_identification_id = etree.SubElement(
        #         seller_identification, ns['cbc'] + 'ID')
        #     seller_identification_id.text = seller_code
        if product:
            # if product.barcode:
            #     std_identification = etree.SubElement(
            #         item, ns['cac'] + 'StandardItemIdentification')
            #     std_identification_id = etree.SubElement(
            #         std_identification, ns['cbc'] + 'ID',
            #         schemeAgencyID='6', schemeID='GTIN')
            #     std_identification_id.text = product.barcode
            # I'm not 100% sure, but it seems that ClassifiedTaxCategory
            # contains the taxes of the product without taking into
            # account the fiscal position
            if type == 'sale':
                taxes = product.taxes_id
            else:
                taxes = product.supplier_taxes_id
            # if taxes:
            #     for tax in taxes.filtered(
            #             lambda t: t.company_id == self.env.user.company_id):
            #         self._ubl_add_tax_category(
            #             tax, item, ns, node_name='ClassifiedTaxCategory',
            #             version=version)
            for attribute_value in product.attribute_value_ids:
                item_property = etree.SubElement(
                    item, ns['cac'] + 'AdditionalItemProperty')
                property_name = etree.SubElement(
                    item_property, ns['cbc'] + 'Name')
                property_name.text = attribute_value.attribute_id.name
                property_value = etree.SubElement(
                    item_property, ns['cbc'] + 'Value')
                property_value.text = attribute_value.name

    @api.model
    def _ubl_add_tax_subtotal(
            self, taxable_amount, tax_amount, tax, currency_code,
            parent_node, ns, version='2.1'):
        prec = self.env['decimal.precision'].precision_get('Account')
        prec = prec if prec <= 2 else 2
        tax_subtotal = etree.SubElement(parent_node, ns['cac'] + 'TaxSubtotal')
        if not float_is_zero(taxable_amount, precision_digits=prec):
            taxable_amount_node = etree.SubElement(
                tax_subtotal, ns['cbc'] + 'TaxableAmount',
                currencyID=currency_code)
            taxable_amount_node.text = '%0.*f' % (prec, taxable_amount)
        else:
            taxable_amount_node = etree.SubElement(
                tax_subtotal, ns['cbc'] + 'TaxableAmount',
                currencyID=currency_code)
            taxable_amount_node.text = '%0.*f' % (prec, taxable_amount)
        tax_amount_node = etree.SubElement(
            tax_subtotal, ns['cbc'] + 'TaxAmount', currencyID=currency_code)
        tax_amount_node.text = '%0.*f' % (prec, tax_amount)
        if tax:
            if (
                    tax.amount_type == 'percent' and
                    not float_is_zero(tax.amount, precision_digits=prec+3)):
                percent = etree.SubElement(
                    tax_subtotal, ns['cbc'] + 'Percent')
                percent.text = str(
                    float_round(tax.amount, precision_digits=2))
        self._ubl_add_tax_category(tax, tax_subtotal, ns, version=version)

    @api.model
    def _ubl_add_tax_category(
            self, tax, parent_node, ns, node_name='TaxCategory',
            version='2.1'):
        if tax:
            tax_category = etree.SubElement(parent_node, ns['cac'] + node_name)
            if not tax.unece_categ_id:
                raise UserError(_(
                    "Missing UNECE Tax Category on tax '%s'" % tax.name))
            tax_category_id = etree.SubElement(
                tax_category, ns['cbc'] + 'ID', schemeID='UN/ECE 5305',
                schemeAgencyID='6')
            tax_category_id.text = tax.unece_categ_code
            tax_name = etree.SubElement(
                tax_category, ns['cbc'] + 'Name')
            tax_name.text = tax.name
            if tax.amount_type == 'percent':
                tax_percent = etree.SubElement(
                    tax_category, ns['cbc'] + 'Percent')
                tax_percent.text = str(tax.amount)
            if tax.amount == 0.0:
                taxexemptionreason = etree.SubElement(
                    tax_category, ns['cbc'] + 'TaxExemptionReason')
                taxexemptionreason.text = "NA"

            tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
            self._ubl_add_tax_scheme(
                tax_scheme_dict, tax_category, ns, version=version)
        else:
            tax_category = etree.SubElement(parent_node, ns['cac'] + node_name)
            tax_category_id = etree.SubElement(
                tax_category, ns['cbc'] + 'ID', schemeID='UN/ECE 5305',
                schemeAgencyID='6')
            tax_category_id.text = '01'
            tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
            self._ubl_add_tax_scheme(
                tax_scheme_dict, tax_category, ns, version=version)

    @api.model
    def _ubl_get_tax_scheme_dict_from_tax(self, tax):
        if tax:
            if not tax.unece_type_id:
                raise UserError(_(
                    "Missing UNECE Tax Type on tax '%s'" % tax.name))
            tax_scheme_dict = {
                'id': tax.unece_type_code,
                'name': False,
                'type_code': False,
                }
            return tax_scheme_dict
        else:
            unece = self.env.ref('account_tax_unece.tax_categ_sale')
            if unece:
                tax_scheme_dict = {
                    'id': unece.id,
                    'name': False,
                    'type_code': False,
                }
                return tax_scheme_dict

    @api.model
    def _ubl_add_tax_scheme(
            self, tax_scheme_dict, parent_node, ns, version='2.1'):
        tax_scheme = etree.SubElement(parent_node, ns['cac'] + 'TaxScheme')
        if tax_scheme_dict.get('id'):
            tax_scheme_id = etree.SubElement(
                tax_scheme, ns['cbc'] + 'ID', schemeID='UN/ECE 5153',
                schemeAgencyID='6')
            tax_scheme_id.text = 'OTH'
            # if not self.tax_line_ids:
            #     tax_scheme_id.text = 'OTH'
            # else:
            #     tax_scheme_id.text = tax_scheme_dict['id']
        if tax_scheme_dict.get('name'):
            tax_scheme_name = etree.SubElement(tax_scheme, ns['cbc'] + 'Name')
            tax_scheme_name.text = tax_scheme_dict['name']
        if tax_scheme_dict.get('type_code'):
            tax_scheme_type_code = etree.SubElement(
                tax_scheme, ns['cbc'] + 'TaxTypeCode')
            tax_scheme_type_code.text = tax_scheme_dict['type_code']

    @api.model
    def _ubl_get_nsmap_namespace(self, doc_name, version='2.1'):
        nsmap = {
            None: 'urn:oasis:names:specification:ubl:schema:xsd:' + doc_name,
            'cac': 'urn:oasis:names:specification:ubl:'
                   'schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonBasicComponents-2',
            }
        ns = {
            'cac': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonAggregateComponents-2}',
            'cbc': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonBasicComponents-2}',
            }
        return nsmap, ns

    @api.model
    def _ubl_check_xml_schema(self, xml_string, document, version='2.1'):
        """Validate the XML file against the XSD"""
        xsd_file = 'base_ubl/data/xsd-%s/maindoc/UBL-%s-%s.xsd' % (
            version, document, version)
        xsd_etree_obj = etree.parse(file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            t = etree.parse(BytesIO(xml_string))
            official_schema.assertValid(t)
        except Exception as e:
            # if the validation of the XSD fails, we arrive here
            logger = logging.getLogger(__name__)
            logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(_(
                "The UBL XML file is not valid against the official "
                "XML Schema Definition. The XML file and the "
                "full error have been written in the server logs. "
                "Here is the error, which may give you an idea on the "
                "cause of the problem : %s.")
                % str(e))
        return True

    @api.model
    def embed_xml_in_pdf(
            self, xml_string, xml_filename, pdf_content=None, pdf_file=None):
        """
        2 possible uses:
        a) use the pdf_content argument, which has the binary of the PDF
        -> it will return the new PDF binary with the embedded XML
        (used for qweb-pdf reports)
        b) OR use the pdf_file argument, which has the path to the
        original PDF file
        -> it will re-write this file with the new PDF
        (used for py3o reports, *_ubl_py3o modules in this repo)
        """
        assert pdf_content or pdf_file, 'Missing pdf_file or pdf_content'
        logger.debug('Starting to embed %s in PDF file', xml_filename)
        if pdf_file:
            original_pdf_file = pdf_file
        elif pdf_content:
            original_pdf_file = BytesIO(pdf_content)
        original_pdf = PdfFileReader(original_pdf_file)
        new_pdf_filestream = PdfFileWriter()
        new_pdf_filestream.appendPagesFromReader(original_pdf)
        new_pdf_filestream.addAttachment(xml_filename, xml_string)
        # show attachments when opening PDF
        new_pdf_filestream._root_object.update({
            NameObject("/PageMode"): NameObject("/UseAttachments"),
        })
        new_pdf_content = None
        if pdf_file:
            f = open(pdf_file, 'wb')
            new_pdf_filestream.write(f)
            f.close()
            new_pdf_content = pdf_content
        elif pdf_content:
            with NamedTemporaryFile(prefix='odoo-ubl-', suffix='.pdf') as f:
                new_pdf_filestream.write(f)
                f.seek(0)
                new_pdf_content = f.read()
                f.close()
        logger.info('%s file added to PDF', xml_filename)
        return new_pdf_content

    # ==================== METHODS TO PARSE UBL files

    @api.model
    def ubl_parse_customer_party(self, customer_party_node, ns):
        ref_xpath = customer_party_node.xpath(
            'cac:SupplierAssignedAccountID', namespaces=ns)
        party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_supplier_party(self, customer_party_node, ns):
        ref_xpath = customer_party_node.xpath(
            'cac:CustomerAssignedAccountID', namespaces=ns)
        party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_party(self, party_node, ns):
        partner_name_xpath = party_node.xpath(
            'cac:PartyName/cbc:Name', namespaces=ns)
        vat_xpath = party_node.xpath(
            'cac:PartyTaxScheme/cbc:CompanyID', namespaces=ns)
        email_xpath = party_node.xpath(
            'cac:Contact/cbc:ElectronicMail', namespaces=ns)
        phone_xpath = party_node.xpath(
            'cac:Contact/cbc:Telephone', namespaces=ns)
        website_xpath = party_node.xpath(
            'cbc:WebsiteURI', namespaces=ns)
        partner_dict = {
            'vat': vat_xpath and vat_xpath[0].text or False,
            'name': partner_name_xpath[0].text,
            'email': email_xpath and email_xpath[0].text or False,
            'website': website_xpath and website_xpath[0].text or False,
            'phone': phone_xpath and phone_xpath[0].text or False,
            }
        address_xpath = party_node.xpath('cac:PostalAddress', namespaces=ns)
        if address_xpath:
            address_dict = self.ubl_parse_address(address_xpath[0], ns)
            partner_dict.update(address_dict)
        return partner_dict

    @api.model
    def ubl_parse_address(self, address_node, ns):
        country_code_xpath = address_node.xpath(
            'cac:Country/cbc:IdentificationCode',
            namespaces=ns)
        country_code = country_code_xpath and country_code_xpath[0].text\
            or False
        state_code_xpath = address_node.xpath(
            'cbc:CountrySubentityCode', namespaces=ns)
        state_code = state_code_xpath and state_code_xpath[0].text or False
        zip_xpath = address_node.xpath('cbc:PostalZone', namespaces=ns)
        zip = zip_xpath and zip_xpath[0].text and\
            zip_xpath[0].text.replace(' ', '') or False
        address_dict = {
            'zip': zip,
            'state_code': state_code,
            'country_code': country_code,
            }
        return address_dict

    @api.model
    def ubl_parse_delivery(self, delivery_node, ns):
        party_xpath = delivery_node.xpath('cac:DeliveryParty', namespaces=ns)
        if party_xpath:
            partner_dict = self.ubl_parse_party(party_xpath[0], ns)
        else:
            partner_dict = {}
        delivery_address_xpath = delivery_node.xpath(
            'cac:DeliveryLocation/cac:Address', namespaces=ns)
        if not delivery_address_xpath:
            delivery_address_xpath = delivery_node.xpath(
                'cac:DeliveryAddress', namespaces=ns)
        if delivery_address_xpath:
            address_dict = self.ubl_parse_address(
                delivery_address_xpath[0], ns)
        else:
            address_dict = {}
        delivery_dict = {
            'partner': partner_dict,
            'address': address_dict,
            }
        return delivery_dict

    def ubl_parse_incoterm(self, delivery_term_node, ns):
        incoterm_xpath = delivery_term_node.xpath("cbc:ID", namespaces=ns)
        if incoterm_xpath:
            incoterm_dict = {'code': incoterm_xpath[0].text}
            return incoterm_dict
        return {}

    def ubl_parse_product(self, line_node, ns):
        barcode_xpath = line_node.xpath(
            "cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID='GTIN']",
            namespaces=ns)
        code_xpath = line_node.xpath(
            "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns)
        product_dict = {
            'barcode': barcode_xpath and barcode_xpath[0].text or False,
            'code': code_xpath and code_xpath[0].text or False,
            }
        return product_dict

    # ======================= METHODS only needed for testing

    # Method copy-pasted from edi/base_business_document_import/
    # models/business_document_import.py
    # Because we don't depend on this module
    def get_xml_files_from_pdf(self, pdf_file):
        """Returns a dict with key = filename, value = XML file obj"""
        logger.info('Trying to find an embedded XML file inside PDF')
        res = {}
        try:
            fd = BytesIO(pdf_file)
            pdf = PdfFileReader(fd)
            logger.debug('pdf.trailer=%s', pdf.trailer)
            pdf_root = pdf.trailer['/Root']
            logger.debug('pdf_root=%s', pdf_root)
            embeddedfiles = pdf_root['/Names']['/EmbeddedFiles']['/Names']
            i = 0
            xmlfiles = {}  # key = filename, value = PDF obj
            for embeddedfile in embeddedfiles[:-1]:
                mime_res = mimetypes.guess_type(embeddedfile)
                if mime_res and mime_res[0] in ['application/xml', 'text/xml']:
                    xmlfiles[embeddedfile] = embeddedfiles[i+1]
                i += 1
            logger.debug('xmlfiles=%s', xmlfiles)
            for filename, xml_file_dict_obj in xmlfiles.items():
                try:
                    xml_file_dict = xml_file_dict_obj.getObject()
                    logger.debug('xml_file_dict=%s', xml_file_dict)
                    xml_string = xml_file_dict['/EF']['/F'].getData()
                    xml_root = etree.fromstring(xml_string)
                    logger.debug(
                        'A valid XML file %s has been found in the PDF file',
                        filename)
                    res[filename] = xml_root
                except Exception as e:
                    continue
        except Exception as e:
            pass
        logger.info('Valid XML files found in PDF: %s', list(res.keys()))
        return res
