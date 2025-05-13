from odoo import api, fields, models, exceptions
from odoo.exceptions import AccessError, ValidationError


class DataCatalogue(models.Model):
    _name = "msic.code"
    _rec_name = "msic_code"

    msic_code = fields.Char(string="MSCI Code")
    msic_name = fields.Char(string="MSCI Name")

    def name_get(self):
        result = []
        for record in self:
            # Combine msic_name and msic_code in the display
            name = f"{record.msic_code}  {record.msic_name} " if record.msic_code else record.msic_name
            result.append((record.id, name))
        return result



class FrequencyOfBilling(models.Model):
    _name = "frequency.of.billing"

    billing_code = fields.Char(string="Billing Code")
    billing_name = fields.Char(string="Billing Name")


class Classification(models.Model):
    _name = "classification.type"
    _rec_name = "classification_name"

    classification_code = fields.Char(string="Classification Code")
    classification_name = fields.Char(string="Classification Name")

class TaxType(models.Model):
    _name = "tax.type"

    tax_code = fields.Char(string="Tax Code")
    tax_name = fields.Char(string="Tax Name")


class PaymentMethod(models.Model):
    _name = "payment.method"

    payment_code = fields.Char(string="Payment Code")
    payment_name = fields.Char(string="Payment Name")





class Country(models.Model):
    _name = 'einvoice.res.country'

    country_code = fields.Char(string="Country Code")
    country_name = fields.Char(string="Country Name")



class ResCountry(models.Model):
    _inherit = 'res.country'

    code = fields.Char(
        string='Country Code', size=3,
        help='The ISO country code in two chars. \nYou can use this field for quick search.')


class EinvoiceUom(models.Model):
    _name = 'einvoice.uom'
    _rec_name = "uom_name"

    uom_code = fields.Char(string="E-Invoice UOM Code")
    uom_name = fields.Char(string="E-Invoice UOM Name")
