from odoo import api, fields, models,exceptions, _
import logging
from datetime import date
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"

    default_ar_ap = fields.Boolean(string='Default AR or AP', default=False,
                                   help="Check this box if to set the default AR or AP for Customer or Vendor")

    @api.onchange('name', 'user_type_id')
    def _onchange_name(self):
        if self.name and self.user_type_id:
            if self.name.upper() == 'TRADE CREDITORS' and self.user_type_id.id == 2:
                self.default_ar_ap = True
            elif self.name.upper() == 'TRADE DEBTORS' and self.user_type_id.id == 1:
                self.default_ar_ap = True


