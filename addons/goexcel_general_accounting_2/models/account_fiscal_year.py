from odoo import fields, models, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    @api.model
    def create(self, vals):
        create_count = 20
        rec = super(AccountFiscalYear, self).create(vals)
        if self._context.get('create_one_only'):
            return rec

        def create_from(record):
            #kashif 11 march 24: fix code issue to capture next FY date from End date of current selection +1
            new_rec_year = record.date_from.year + 1
            new_rec_date_from = record.date_to+ relativedelta(days=1)
            new_rec_date_to = record.date_to + relativedelta(years=1)
            is_exist = record.search([
                ('date_from', '=', new_rec_date_from),
                ('company_id', '=', record.company_id.id)
            ], limit=1)
            if is_exist:
                return is_exist
            new_rec_vals = {
                'state': 'draft',
                'company_id': record.company_id.id,
                'code': str(new_rec_year),
                'name': f'Fiscal Year {new_rec_year}',
                'date_from': new_rec_date_from,
                'date_to': new_rec_date_to
            }
            return record.with_context(create_one_only=True).create(new_rec_vals)

        for i in range(create_count):
            rec = create_from(rec)

        return rec