from odoo import models, fields, api
from odoo.exceptions import Warning


class OCRTableMapping(models.Model):
    _name = 'ocr.table.mapping'
    _description = 'OCR Table Mapping'

    sequence = fields.Integer(string="sequence")
    name = fields.Char(string='Name')
    type = fields.Selection([('default', 'Default'),
                             ('payment_term', 'Payment Term'),
                             ('currency', 'Currency'),
                             ('product', 'Product'),
                             ('partner', 'Partner'),
                             ('pol', 'Port of Loading'),
                             ], default='default', string="Type")
    mapping_line_ids = fields.One2many('ocr.table.mapping.line', 'line_id', string="Mapping Line", copy=True,
                                       auto_join=True)

    # def write(self, vals):
    #     if self.id == 10:
    #         prods = [['SEAFREIGHT', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['CHASSIS USAGE CHARGES', 'DESTINATION CHASSIS FEE', 4, 17237], ['ISPS - INTERN. SHIP AND PORT SECURITY CHARGES (POD)', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['SEAL FEE', 'SEAL FEE (MSC)', 4, 17237], ['GLOBAL FUEL SURCHAGES', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['CONTAINER COMPLIANCE CHARGES', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['TERMINAL HANDLING CHARGES', "THC PTP - 40' (MSC)", 4, 17237], ['BL FEE', 'BL FEE (MSC)', 4, 17237], ['EDI FEE - EXPORT', 'EDI FEE (MSC)', 4, 17237], ['LOW SULPHUR FUEL CONTRIBUTION', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['QUARTELY BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['WHARFAGE', 'DESTINATION WHARFAGE CHARGES', 4, 17237], ['BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 4, 17237], ['TELEX RELEASE', 'TELEX RELEASE FEE (MSC)', 4, 17237], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 4, 14632], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 4, 14632], ['Export Service', 'SEAL FEE (SEALAND)', 4, 14632], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 4, 14632], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 4, 14632], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 4, 14632], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 4, 14632], ['Export Service', 'SEAL FEE (SEALAND)', 4, 14632], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 4, 14632], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 4, 14632], ['Environmental Fuel Fee', "OCEAN FREIGHT - 20'", 4, 14632], ['Low Sulphur Surcharge', "OCEAN FREIGHT - 20'", 4, 14632], ['Panamal Canal Fee', "OCEAN FREIGHT - 20'", 4, 14632], ['SEAL FEE (SJ)', 'SEAL FEE (YML)', 4, 14638], ['SECURITY MANIFEST DOC CHARGES (SQ)', 'AMS/ACI CHARGES (YML)', 4, 14638], ['ELECTRONIC DATA INTERCHANGE (EDI) FEE (ED)', 'EDI FEE (YML)', 4, 14638], ['DOCUMENTATION FEE (DF)', 'BL FEE (YML)', 4, 14638], ['CARRIER SECURITY CHARGES (VS)', "OCEAN FREIGHT - 20'", 4, 14638], ['CY RECEIVING CHARGES (CY)', "THC PKL  - 20' (YML)", 4, 14638], ['OCEAN FREIGHT (OF)', "OCEAN FREIGHT - 20'", 4, 14638], ['LC-LOCAL EDI CHARGES', 'EDI FEE (YML)', 4, 14638], ['TERMINAL HANDLING CHARGES', "THC PGU - 20' (YML)", 4, 14638], ['ENTRY & EXPORT SUMMARY DECLARATION SURCHARGES', 'ENS CHARGES (YMG)', 4, 14638], ['TELEX RELEASE', 'TELEX RELEASE FEE (YML)', 4, 14638], ['OCEAN FREIGHT', "OCEAN FREIGHT - 20'", 4, 14629], ['Terminal Handl. ch destination', 'DESTINATION THC', 4, 14629], ['Terminal Handl. Ch origin', "THC PTP - 20' (CMA)", 4, 14629], ['Export Declaration Surcharge', 'AMS/ACI CHARGES (CMA)', 4, 14629], ['Container inspection fees and survey fees', 'DESTINATION DOCUMENTATION FEE', 4, 14629], ['Overweight, freight additional', 'OVERWEIGHT', 4, 14629], ['Destinat. Terminal-Intl Ship&Port facility Security', 'DESTINATION DOCUMENTATION FEE', 4, 14629], ['Sealing service export', 'SEAL FEE (CMA)', 4, 14629], ['On Carriage Additional - Congestion', 'DESTINATION DOCUMENTATION FEE', 4, 14629], ['Communication Fee', 'EDI FEE (CMA)', 4, 14629], ['Export Documentation Fee', 'BL FEE (CMA)', 4, 14629], ['Express Release Fee', 'TELEX RELEASE FEE (CMA)', 4, 14629], ['Ocean Carrier-Intl Ship & port Facility Security', "OCEAN FREIGHT - 20'", 4, 14629], ['SEAFREIGHT', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['CHASSIS USAGE CHARGES', 'DESTINATION CHASSIS FEE', 2, 14403], ['ISPS - INTERN. SHIP AND PORT SECURITY CHARGES (POD)', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['SEAL FEE', 'SEAL FEE (MSC)', 2, 14403], ['GLOBAL FUEL SURCHAGES', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['CONTAINER COMPLIANCE CHARGES', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['TERMINAL HANDLING CHARGES', "THC PTP - 40' (MSC)", 2, 14403], ['BL FEE', 'BL FEE (MSC)', 2, 14403], ['EDI FEE - EXPORT', 'EDI FEE (MSC)', 2, 14403], ['LOW SULPHUR FUEL CONTRIBUTION', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['QUARTELY BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['WHARFAGE', 'DESTINATION WHARFAGE CHARGES', 2, 14403], ['BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 2, 14403], ['TELEX RELEASE', 'TELEX RELEASE FEE (MSC)', 2, 14403], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 2, 14411], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 2, 14411], ['Export Service', 'SEAL FEE (SEALAND)', 2, 14411], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 2, 14411], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 2, 14411], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 2, 14405], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 2, 14405], ['Export Service', 'SEAL FEE (SEALAND)', 2, 14405], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 2, 14405], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 2, 14405], ['Environmental Fuel Fee', "OCEAN FREIGHT - 20'", 2, 14405], ['Low Sulphur Surcharge', "OCEAN FREIGHT - 20'", 2, 14405], ['Panamal Canal Fee', "OCEAN FREIGHT - 20'", 2, 14405], ['SEAL FEE (SJ)', 'SEAL FEE (YML)', 2, 14425], ['SECURITY MANIFEST DOC CHARGES (SQ)', 'AMS/ACI CHARGES (YML)', 2, 14425], ['ELECTRONIC DATA INTERCHANGE (EDI) FEE (ED)', 'EDI FEE (YML)', 2, 14425], ['DOCUMENTATION FEE (DF)', 'BL FEE (YML)', 2, 14425], ['CARRIER SECURITY CHARGES (VS)', "OCEAN FREIGHT - 20'", 2, 14425], ['CY RECEIVING CHARGES (CY)', "THC PKL  - 20' (YML)", 2, 14425], ['OCEAN FREIGHT (OF)', "OCEAN FREIGHT - 20'", 2, 14425], ['LC-LOCAL EDI CHARGES', 'EDI FEE (YML)', 2, 14425], ['TERMINAL HANDLING CHARGES', "THC PGU - 20' (YML)", 2, 14425], ['ENTRY & EXPORT SUMMARY DECLARATION SURCHARGES', 'ENS CHARGES (YMG)', 2, 14425], ['TELEX RELEASE', 'TELEX RELEASE FEE (YML)', 2, 14425], ['Telex Release', 'TELEX RELEASE FEE (WAN HAI)', 2, 14423], ['TERMINAL HANDLING CHARGES', "THC PGU - 20' (WAN HAI)", 2, 14423], ['OCEAN FREIGHT CHARGES', "OCEAN FREIGHT - 20'", 2, 14423], ['MANIFEST TRANSMISSION FEE', 'AMS/ACI CHARGES (WHL)', 2, 14423], ['HIGH SECURITY SEAL', 'SEAL FEE (WAN HAI)', 2, 14423], ['ELECTRONIC DATA INTERCHANGE CHARGES', 'EDI FEE (WAN HAI)', 2, 14423], ['DOCUMENTATION FEE', 'BL FEE (WAN HAI)', 2, 14423], ['DESTINATION DELIVERY CHARGES', "OCEAN FREIGHT - 20'", 2, 14423], ['BUNKER ADJUSTMENT FACTOR', "OCEAN FREIGHT - 20'", 2, 14423], ['Telex Release', 'TELEX RELEASE FEE (COSCO)', 2, 14383], ['Arbitrary at Load', "OCEAN FREIGHT - 40'", 2, 14383], ['Carrier Security Charges', "OCEAN FREIGHT - 40'", 2, 14383], ['ORIGIN DOC FEE', 'BL FEE (COSCO)', 2, 14383], ['EDE FEE', 'EDI FEE (COSCO)', 2, 14383], ['Advance Manifest Security Charges for Auto NVOCC', 'AMS/ACI CHARGES (COSCO)', 2, 14383], ['Ocean Freight', "OCEAN FREIGHT - 40'", 2, 14383], ['Seal Fee', 'SEAL FEE (COSCO)', 2, 14383], ['ORIG TRML HANDLG', "THC PGU - 40' (COSCO)", 2, 14383], ['OVERWEIGHT PENANLTY', 'OVERWEIGHT', 2, 14383], ['OCEAN FREIGHT', "OCEAN FREIGHT - 20'", 2, 14384], ['Terminal Handl. ch destination', 'DESTINATION THC', 2, 14384], ['Terminal Handl. Ch origin', "THC PTP - 20' (CMA)", 2, 14384], ['Export Declaration Surcharge', 'AMS/ACI CHARGES (CMA)', 2, 14384], ['Container inspection fees and survey fees', 'DESTINATION DOCUMENTATION FEE', 2, 14384], ['Overweight, freight additional', 'OVERWEIGHT', 2, 14384], ['Destinat. Terminal-Intl Ship&Port facility Security', 'DESTINATION DOCUMENTATION FEE', 2, 14384], ['Sealing service export', 'SEAL FEE (CMA)', 2, 14384], ['On Carriage Additional - Congestion', 'DESTINATION DOCUMENTATION FEE', 2, 14384], ['Communication Fee', 'EDI FEE (CMA)', 2, 14384], ['Export Documentation Fee', 'BL FEE (CMA)', 2, 14384], ['Express Release Fee', 'TELEX RELEASE FEE (CMA)', 2, 14384], ['Ocean Carrier-Intl Ship & port Facility Security', "OCEAN FREIGHT - 20'", 2, 14384], ['SEAFREIGHT', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['CHASSIS USAGE CHARGES', 'DESTINATION CHASSIS FEE', 3, 14843], ['ISPS - INTERN. SHIP AND PORT SECURITY CHARGES (POD)', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['SEAL FEE', 'SEAL FEE (MSC)', 3, 14843], ['GLOBAL FUEL SURCHAGES', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['CONTAINER COMPLIANCE CHARGES', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['TERMINAL HANDLING CHARGES', "THC PTP - 40' (MSC)", 3, 14843], ['BL FEE', 'BL FEE (MSC)', 3, 14843], ['EDI FEE - EXPORT', 'EDI FEE (MSC)', 3, 14843], ['LOW SULPHUR FUEL CONTRIBUTION', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['QUARTELY BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['WHARFAGE', 'DESTINATION WHARFAGE CHARGES', 3, 14843], ['BUNKER RECOVERY CHARGE', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14843], ['TELEX RELEASE', 'TELEX RELEASE FEE (MSC)', 3, 14843], ['CONTAINER FACILITY CHARGES-Origin', "CONTAINER FACILITY CHARGE - 40'HC (MSC JKT)", 3, 14926], ['SEAL FEE-Origin', 'SEAL FEE (MSC JKT)', 3, 14926], ['TERMINAL HANDLING CHARGES-Origin', "THC JKT/SMR - 40' (MSC JKT)", 3, 14926], ['OUTBOUND - ADMINISTRATION FEE-Local', 'ADMIN FEE (MSC JKT)', 3, 14926], ['SEA WAY BILL FEE-Local', 'SEAWAY BILL (MSC JKT)', 3, 14926], ['SEA FREIGHT', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14926], ['CHASSIS USAGE CHARGES-Origin', 'DESTINATION CHASSIS FEE', 3, 14926], ['CONTAINER COMPLIANCE CHARGES-Freight', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14926], ['GLOBAL FUEL SURCHARGES-Freight', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14926], ['ISPS - INTERN. SHIP AND PORT SECURITY CHARGES (POD)-Destination', "OCEAN FREIGHT - 40' HIGH CUBE", 3, 14926], ['OUTBOUND -DOC FEE-Local', 'BL FEE (MSC JKT)', 3, 14926], ['OUTBOUND - TELEX RELEASE-Local', 'TELEX RELEASE FEE (MSC)', 3, 14926], ['VAT', 'VAT', 3, 14926], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 3, 14842], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 3, 14842], ['Export Service', 'SEAL FEE (SEALAND)', 3, 14842], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 3, 14842], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 3, 14842], ['Basic Ocean Freight', "OCEAN FREIGHT - 20'", 3, 14845], ['Documentation Fee- Origin', 'BL FEE (SEALAND)', 3, 14845], ['Export Service', 'SEAL FEE (SEALAND)', 3, 14845], ['Terminal Handling Service - Origin', "THC PTP - 20' (SEALAND)", 3, 14845], ['Electronic Cargo Release Service - Export', 'TELEX RELEASE FEE (SEALAND)', 3, 14845], ['Environmental Fuel Fee', "OCEAN FREIGHT - 20'", 3, 14845], ['Low Sulphur Surcharge', "OCEAN FREIGHT - 20'", 3, 14845], ['Panamal Canal Fee', "OCEAN FREIGHT - 20'", 3, 14845], ['SEAL FEE (SJ)', 'SEAL FEE (YML)', 3, 14867], ['SECURITY MANIFEST DOC CHARGES (SQ)', 'AMS/ACI CHARGES (YML)', 3, 14867], ['ELECTRONIC DATA INTERCHANGE (EDI) FEE (ED)', 'EDI FEE (YML)', 3, 14867], ['DOCUMENTATION FEE (DF)', 'BL FEE (YML)', 3, 14867], ['CARRIER SECURITY CHARGES (VS)', "OCEAN FREIGHT - 20'", 3, 14867], ['CY RECEIVING CHARGES (CY)', "THC PKL  - 20' (YML)", 3, 14867], ['OCEAN FREIGHT (OF)', "OCEAN FREIGHT - 20'", 3, 14867], ['LC-LOCAL EDI CHARGES', 'EDI FEE (YML)', 3, 14867], ['TERMINAL HANDLING CHARGES', "THC PGU - 20' (YML)", 3, 14867], ['ENTRY & EXPORT SUMMARY DECLARATION SURCHARGES', 'ENS CHARGES (YMG)', 3, 14867], ['TELEX RELEASE', 'TELEX RELEASE FEE (YML)', 3, 14867], ['Telex Release', 'TELEX RELEASE FEE (WAN HAI)', 3, 14866], ['TERMINAL HANDLING CHARGES', "THC PGU - 20' (WAN HAI)", 3, 14866], ['OCEAN FREIGHT CHARGES', "OCEAN FREIGHT - 20'", 3, 14866], ['MANIFEST TRANSMISSION FEE', 'AMS/ACI CHARGES (WHL)', 3, 14866], ['HIGH SECURITY SEAL', 'SEAL FEE (WAN HAI)', 3, 14866], ['ELECTRONIC DATA INTERCHANGE CHARGES', 'EDI FEE (WAN HAI)', 3, 14866], ['DOCUMENTATION FEE', 'BL FEE (WAN HAI)', 3, 14866], ['DESTINATION DELIVERY CHARGES', "OCEAN FREIGHT - 20'", 3, 14866], ['BUNKER ADJUSTMENT FACTOR', "OCEAN FREIGHT - 20'", 3, 14866], ['Telex Release', 'TELEX RELEASE FEE (COSCO)', 3, 14828], ['Arbitrary at Load', "OCEAN FREIGHT - 40'", 3, 14828], ['Carrier Security Charges', "OCEAN FREIGHT - 40'", 3, 14828], ['ORIGIN DOC FEE', 'BL FEE (COSCO)', 3, 14828], ['EDE FEE', 'EDI FEE (COSCO)', 3, 14828], ['Advance Manifest Security Charges for Auto NVOCC', 'AMS/ACI CHARGES (COSCO)', 3, 14828], ['Ocean Freight', "OCEAN FREIGHT - 40'", 3, 14828], ['Seal Fee', 'SEAL FEE (COSCO)', 3, 14828], ['ORIG TRML HANDLG', "THC PGU - 40' (COSCO)", 3, 14828], ['OVERWEIGHT PENANLTY', 'OVERWEIGHT', 3, 14828]]
    #         for idx, prod in enumerate(prods, 1):
    #             p = self.env['product.template'].sudo().search([
    #                 ('name', 'ilike', prod[1]), ('company_id', '=', prod[2])], limit=1).product_variant_id
    #             self.mapping_line_ids.create({
    #                 'keyword': prod[0],
    #                 'type': 'value',
    #                 'line_id': 10,
    #                 'product_id': p.id,
    #                 'partner_id': prod[3],
    #                 'company_id': prod[2]
    #             })
    #         res = super(OCRTableMapping, self).write(vals)
    #     return res

class OCRTableMappingLine(models.Model):
    _name = 'ocr.table.mapping.line'
    _description = 'OCR Table Mapping Line'

    sequence = fields.Integer(string="sequence")
    line_id = fields.Many2one('ocr.table.mapping', string='Mapping', required=True, ondelete='cascade',
                              index=True, copy=False)
    name = fields.Char(string='Name')
    category = fields.Char(string='Category')
    type = fields.Selection([('label', 'Label'),
                             ('value', 'Value')], default='label', string="Type")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    currency = fields.Many2one('res.currency', string='Currency')
    product_id = fields.Many2one('product.product', string='Product')
    direction = fields.Selection([("import", "Import"), ("export", "Export")], default="export", string="Direction")
    container_size = fields.Selection([("20", "20"), ("40", "40")], default="40", string="Container Size")
    partner_id = fields.Many2one('res.partner', string='Partner')
    port_of_loading_id = fields.Many2one('freight.ports', string='Port of Loading')
    user_id = fields.Many2one('res.users', string='User')
    keyword = fields.Char(string='Keyword')
    company_id = fields.Many2one('res.company')

    @api.model
    def create(self, value):
        header = self.env['ocr.table.mapping'].browse(value.get("line_id"))
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


class OCRPartnerTemplate(models.Model):
    _name = 'ocr.partner.template'
    _description = 'OCR Partner Template'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company')

    merge_line_item = fields.Boolean('Merge Line Item')

    page_segmentation_modes_value = fields.Char(string='Page Segmentation Modes')
    density_value = fields.Char(string='Density')

    date_format = fields.Char(string='Date Format')
    reference_pattern = fields.Char(string='Reference Pattern', help="")
    bl_no_pattern = fields.Char(string='BL No. Pattern', help="")
    exchange_rate_pattern = fields.Char(string='Exchange Rate Pattern', help="NEXT LINE; LAST")

    date_template_label = fields.Many2one('ocr.table.mapping.line', string='Date')
    due_date_template_label = fields.Many2one('ocr.table.mapping.line', string='Due Date')
    reference_template_label = fields.Many2one('ocr.table.mapping.line', string='Reference')
    debit_note_template_label = fields.Many2one('ocr.table.mapping.line', string='Debit Note')

    bl_no_template_label = fields.Many2one('ocr.table.mapping.line', string='BL No')
    exchange_rate_template_label = fields.Many2one('ocr.table.mapping.line', string='Exchange Rate')

    payment_term_template_label = fields.Many2one('ocr.table.mapping.line', string='Payment Term')
    currency_template_label = fields.Many2one('ocr.table.mapping.line', string='Currency')
    pol_template_label = fields.Many2one('ocr.table.mapping.line', string='POL')

    product_section_start = fields.Char(string='Product Section Start')
    product_section_end = fields.Char(string='Product Section End')
    line_item_pattern = fields.Char(string='Line Item Pattern',
                                    help="NIL - None; QTY - Quantity; RTE – Conversion Rate; "
                                         "PFC – Unit Price (Foreign Currency); UPI – Unit Price; "
                                         "TOTAL - Total")
    x2nd_line_item_pattern = fields.Char(string='2nd Line Item Pattern')
    line_item_pattern_with_exchange_rate = fields.Char(string='Line Item Pattern With Exchange Rate')
    with_exchange_rate = fields.Boolean(string="With Exchange Rate")
    complex_line = fields.Boolean(string="Complex Line")
    complex_line_pattern = fields.Char(string='Complex Line Pattern')

    pol_pattern = fields.Char(string='POL Pattern')

    #container_template_label = fields.Many2one('ocr.table.mapping.line', string='Container')
    #container_pattern = fields.Char(string='Container Pattern')

    multi_page_check = fields.Boolean("With Multi Page")
    multi_page_count = fields.Integer("Multi Page Count")

    container_section_start = fields.Char(string='Container Section Start')
    container_section_end = fields.Char(string='Container Section End')

    container_inline_product = fields.Boolean("Container Inline Product")
    container_inline_product_pattern = fields.Char(string='Container Inline Product Pattern')


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.name = self.partner_id.name
        if self.partner_id:
            partner = self.env['res.partner'].browse(self.partner_id.id)
            partner.write({"ocr_partner_template": self._origin.id})