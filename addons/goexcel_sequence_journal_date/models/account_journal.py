# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    outbound_sequence_id = fields.Many2one('ir.sequence', string="PV sequence")
    inbound_sequence_id = fields.Many2one('ir.sequence', string="OR sequence")
