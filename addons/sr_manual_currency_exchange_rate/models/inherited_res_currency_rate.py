from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResCurrency(models.Model):
    _inherit = 'res.currency.rate'

    date_to = fields.Date(string='Date-To', track_visibility='onchange')
    name = fields.Date(string='Date-From', track_visibility='onchange')

    @api.constrains('name', 'date_to')
    def _check_date_range(self):
        for rate in self:
            today = fields.Date.today()
            # Check if date_to is greater than or equal to name
            if rate.date_to and rate.name and rate.date_to < rate.name:
                raise ValidationError(_("Date-To must be greater than or equal to Date-From"))

            # Check if date_to is not in the past
            if rate.date_to and rate.date_to < today:
                raise ValidationError(
                    _("Date-To cannot be earlier than today's date. Current rate would be expired."))

            # Check for overlapping date ranges
            if rate.date_to:  # Only check if date_to is set
                overlapping = self.env['res.currency.rate'].search([
                    ('id', '!=', rate.id),
                    ('currency_id', '=', rate.currency_id.id),
                    ('company_id', '=', rate.company_id.id or self.env.user.company_id.id),
                    '|',
                    '&', ('name', '<=', rate.name), ('date_to', '>=', rate.name),
                    '&', ('name', '<=', rate.date_to), ('date_to', '>=', rate.date_to)
                ])

                if overlapping:
                    raise ValidationError(
                        _("The date range overlaps with existing currency rate records for the same currency and company"))