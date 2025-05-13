from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr

from odoo.addons import decimal_precision as dp

from odoo.tools import pycompat

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            if rec.company_id.name:
                res.append((rec.id, '%s For %s' % (rec.name, rec.company_id.name)))
            else:
                res.append((rec.id, f"{rec.name} ({rec.currency_id.name})"))
        return res