from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_slot_owner = fields.Boolean(string='Is Slot Owner')