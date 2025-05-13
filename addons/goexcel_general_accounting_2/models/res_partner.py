
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    active = fields.Boolean(default=True)

    @api.multi
    def write(self, vals):
        if 'active' in vals and vals['active'] == False:
            for partner in self:
                # Check for posted invoices, bills, credit notes, and debit notes
                invoices = self.env['account.invoice'].search([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['open','in_payment','paid' ]),
                    ('type', 'in', ['out_invoice','in_invoice','out_refund','in_refund'])
                ])
                if invoices:
                    invoice_refs = ', '.join(invoices.mapped('number'))
                    raise UserError(
                        _("You are not allowed to archive this partner because some records are present in the posted state. The records are: %s") % invoice_refs
                    )
        return super(Partner, self).write(vals)