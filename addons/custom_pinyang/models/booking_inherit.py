from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo import exceptions
from odoo.tools import float_round
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = 'freight.booking'
    booking_date_time = fields.Date(string='ETA/ETD Date', copy=False,
                                    track_visibility='onchange', index=True, required=True)
    original_direction = ''

    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            if not self._origin or not self._origin.id:
                raise exceptions.ValidationError(
                    _("Please save the booking before selecting a Sales Quotation.")
                )
        self.original_direction = self.direction
        # original_service_type = self.service_type

        res = super(FreightBooking, self).onchange_sq_reference()
        return res

    def set_booking_no(self, vals=False):
        # if not self.booking_date_time:
        #     raise ValidationError(_('Please Enter ETA/ETD Date!'))
        # else:
        eta_etd = self.booking_date_time
        if isinstance(eta_etd, str):
            _logger.info("LOGGER: ETA/ETD is a string, %s", eta_etd)
            eta_etd = fields.Date.from_string(eta_etd)
        sequence = self.env['ir.sequence'].with_context(ir_sequence_date=eta_etd)

        if self.direction == 'import':
            # raw = self.booking_no
            raw = sequence.next_by_code('impt')
            dir_letter = 'I'
        elif self.direction == 'export':
            raw = sequence.next_by_code('expt')
            dir_letter = 'E'
        else:
            raw = sequence.next_by_code('tnpt')
            dir_letter = 'T'
        if not raw:
            raise ValidationError(_('Can\'t find sequence: Sequence does not exist or is not currently active'))

        year = eta_etd.strftime('%y')
        month = eta_etd.strftime('%m')

        run_no = raw.split('-')[-1]

        new_no = f"PY{dir_letter}{year}{month}-{run_no}"
        if self.booking_no != new_no:
            self.booking_no = new_no

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'booking_no': self.env['ir.sequence'].next_by_code('draft'),
            'booking_date_time': fields.Date.context_today(self)
        })
        return super(FreightBooking, self).copy(default)

    @api.multi
    def write(self, vals):
        # res = super(FreightBooking, self).write(vals)
        # for rec in self:
        #     if rec.booking_no.startswith('DRAFT-'):
        #         rec.set_booking_no()
        # return res
        res = super(FreightBooking, self).write(vals)
        if 'booking_date_time' in vals:
            for rec in self:
                if isinstance(rec.booking_no, str) and rec.booking_no.startswith('DRAFT-'):
                    rec.set_booking_no()
        return res

    @api.model
    def create(self, vals):
        # if not vals['booking_date_time']:
        #     raise ValidationError(_('Please Enter ETA/ETD Date!'))
        raw_booking_no = vals.get('booking_no')
        booking_no_str = raw_booking_no if isinstance(raw_booking_no, str) else ''
        is_draft = booking_no_str.startswith('DRAFT-')

        res = super(FreightBooking, self).create(vals)
        if is_draft:
            res.booking_no = raw_booking_no
        else:
            res.set_booking_no(vals)
        return res
        # raw_no = vals.get('booking_no')
        # is_draft = isinstance(raw_no, str) and raw_no.startswith('DRAFT-')
        # _logger.info("CREATE.START: is_draft=%s, incoming booking_no=%r", is_draft, raw_no)
        #
        # # 2) Call the super-create (this will pull from fb sequence)
        # rec = super(FreightBooking, self).create(vals)
        # _logger.info("CREATE.AFTER_SUPER: rec.booking_no=%r", rec.booking_no)
        #
        # # 3) If it really was a draft copy, force that back onto the record
        # if is_draft:
        #     rec.booking_no = raw_no
        #     _logger.info("CREATE.DRAFT: forced draft booking_no=%r back on rec.id=%s",
        #                  raw_no, rec.id)
        #     return rec
        #
        # # 4) Otherwise it’s a brand-new booking — generate the real number
        # _logger.info("CREATE.FINAL: generating real sequence")
        # rec.set_booking_no()
        # _logger.info("CREATE.DONE: rec.booking_no=%r", rec.booking_no)
        # return rec

    # @api.model
    # def create(self, vals):
    #     if not vals['booking_date_time']:
    #         raise ValidationError(_('Please Enter ETA/ETD Date!'))
    #     _logger.info("LOGGER:In Create function, %s", vals['booking_no'])
    #
    #     eta_etd = self.booking_date_time
    #     if isinstance(eta_etd, str):
    #         _logger.info("LOGGER: ETA/ETD is a string, %s", eta_etd)
    #         eta_etd = fields.Date.from_string(eta_etd)
    #     sequence = self.env['ir.sequence'].with_context(ir_sequence_date=eta_etd)
    #
    #     if self.direction == 'import':
    #         # raw = self.booking_no
    #         raw = sequence.next_by_code('fb')
    #     elif self.direction == 'export':
    #         raw = sequence.next_by_code('expt')
    #
    #     if not raw:
    #         raise ValidationError(_('Cannot find sequence or is not yet set'))
    #     _logger.info("LOGGER:In Set function, %s", raw)
    #
    #     year = eta_etd.strftime('%y')
    #     month = eta_etd.strftime('%m')
    #
    #     # Direction letter: I or E
    #     dir_letter = 'I' if self.direction == 'import' else 'E'
    #     run_no = raw.split('-')[-1]
    #
    #     new_no = f"PY{dir_letter}{year}{month}-{run_no}"
    #     vals['booking_no'] = new_no
    #
    #     return super(FreightBooking, self).create(vals)

    # @api.multi
    # def write(self, vals):
    #     original_direction = self.original_direction
    #     booking_no_changed = False
    #     # original_service_type = self.service_type
    #     _logger.info("LOG: Original Direction = %s", self.original_direction)
    #
    #     res = super(FreightBooking, self).write(vals)
    #
    #     new_direction = vals.get('direction', self.direction)
    #
    #     # Detect direction change
    #     if self.booking_no and original_direction != new_direction:
    #         direction_code = new_direction[:1].upper()
    #         new_booking_no = self.booking_no[:2] + direction_code + self.booking_no[3:]
    #
    #         if self.booking_no != new_booking_no:
    #             _logger.info("Updating booking number due to direction change: %s -> %s",
    #                          self.booking_no, new_booking_no)
    #             super(FreightBooking, self).write({'booking_no': new_booking_no})
    #             booking_no_changed = True
    #
    #     # Optionally regenerate booking_no if direction/service_type changed and not already handled
    #     if not booking_no_changed and 'booking_no' not in vals:
    #         self.set_booking_no(vals)
    #     return res


class CostProfitInherit(models.Model):
    _inherit = 'freight.cost_profit'

    @api.model
    def create(self, vals):
        # If cost_currency is empty, set it to company currency (MYR)
        if not vals.get('cost_currency'):
            company = self.env.user.company_id
            vals['cost_currency'] = company.currency_id.id
        
        return super(CostProfitInherit, self).create(vals)
    
    @api.onchange('profit_currency')
    def _onchange_profit_currency(self):
        """Update profit_currency_rate when profit_currency changes"""
        # _logger.info("LOG: Profit Currency Onchange function entered")
        if self.profit_currency:
            company_currency = self.env.user.company_id.currency_id
            # _logger.info("LOG: profit currency = %s, company_currency  = %s", self.profit_currency.name, company_currency.name)
            if self.profit_currency != company_currency:
                # _logger.info("LOG: Company currency != profit currency")
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.profit_currency.id),
                                                                 ('company_id', '=', self.env.user.company_id.id),
                                                                 ('name', '<=', datetime.now().date()),
                                                                 ('date_to', '>=', datetime.now().date())], limit=1)
                # _logger.info("LOG: Rate Found = %s", rate_rec)
                if rate_rec:
                    # Update the rate field
                    self.profit_currency_rate = rate_rec.rate
                else:
                    self.profit_currency_rate = 1.0
            else:
                # If same as company currency, rate is 1
                self.profit_currency_rate = 1.0
    
    @api.onchange('cost_currency')
    def _onchange_cost_currency(self):
        """Update cost_currency_rate when cost_currency changes"""
        if self.cost_currency:
            company_currency = self.env.user.company_id.currency_id
            if self.cost_currency != company_currency:
                # Get the current exchange rate
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.profit_currency.id),
                                                                 ('company_id', '=', self.env.user.company_id.id),
                                                                 ('name', '<=', datetime.now().date()),
                                                                 ('date_to', '>=', datetime.now().date())], limit=1)

                if rate_rec:
                    # Update the rate field
                    self.cost_currency_rate = rate_rec.rate
                else:
                    # If no specific company rate, try to get the general rate
                    self.cost_currency_rate = 1.0
            else:
                # If same as company currency, rate is 1
                self.cost_currency_rate = 1.0