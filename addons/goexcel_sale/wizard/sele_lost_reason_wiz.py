from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class SaleLostReason(models.TransientModel):
    _name = "sale.lost.reason.wiz"
    _description = "Sale Lost reason"

    lost_reason_id = fields.Many2one('crm.lost.reason', string="Lost Reason")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    @api.multi
    def action_set_lost_reason(self):
        if self.sale_order_id and self.lost_reason_id:
            self.sale_order_id.write({'sale_lost_reason_id': self.lost_reason_id.id, 'state': 'lost'})
            if self.sale_order_id and self.sale_order_id.opportunity_id:
                self.sale_order_id.opportunity_id.stage_id = self.env['crm.stage'].search([('stage_type', '=', 'close')], limit=1).id or False
            # set lost reason and date in customer
            if self.sale_order_id.partner_id:
                data = {
                    #'status': 'lost_customer',
                    'lost_reason_id': self.lost_reason_id.id,
                    'lost_date': date.today()
                }
                self.sale_order_id.partner_id.write(data)

            if self.sale_order_id.opportunity_id:
                other_sale_ids = self.env['sale.order'].search([('opportunity_id', '=', self.sale_order_id.opportunity_id.id), ('id', '!=', self.sale_order_id.id)])
                if len(other_sale_ids) == 0:
                    stage_id = self.env['crm.stage'].search([('stage_type', '=', 'close')], limit=1)
                    data = {
                        'lost_stage_id': stage_id and stage_id.id or False,
                        'lost_date': date.today(),
                        'probability': 0,
                        'stage_id': stage_id and stage_id.id or False,
                    }
                    self.sale_order_id.opportunity_id.write(data)

            # send mail
            # template = self.env.ref('goexcel_sale.email_set_lost_reason')
            # assert template._name == 'mail.template'
            # with self.env.cr.savepoint():
            #     template.with_context(lang=self.sale_order_id.user_id.partner_id.lang).sudo().send_mail(self.sale_order_id.id, force_send=True, raise_exception=True)


class SalewonReason(models.TransientModel):
    _name = "sale.won.reason.wiz"
    _description = "Sale won reason"

    sale_won_reason_id = fields.Many2one('crm.won.reason', string='Won Reason')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    @api.multi
    def action_set_won_reason(self):
        if self.sale_order_id and self.sale_won_reason_id:
            self.sale_order_id.write({'sale_won_reason_id': self.sale_won_reason_id.id})
            flag = False
            # base action confirm method
            if self.sale_order_id._get_forbidden_state_confirm() & set(self.sale_order_id.mapped('state')):
                raise UserError(_('It is not allowed to confirm an order in the following states: %s') % (', '.join(self.sale_order_id._get_forbidden_state_confirm())))

            for order in self.sale_order_id.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                order.message_subscribe([order.partner_id.id])
            if self.sale_order_id.partner_id.is_prospect:
                flag = True
                partner_data = {
                    'customer': True,
                    'is_prospect': False
                }
                self.sale_order_id.partner_id.write(partner_data)
            self.sale_order_id.write({
                'state': 'sale',
                'confirmation_date': fields.Datetime.now()
            })
            self.sale_order_id._action_confirm()
            if self.sale_order_id.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
                self.sale_order_id.action_done()
            self.sale_order_id.sale_won_reason_id = self.sale_won_reason_id.id
            # return True

            # update  at Crm lead
            if self.sale_order_id.opportunity_id:
                self.sale_order_id.opportunity_id.won_reason = self.sale_won_reason_id.id
                self.sale_order_id.opportunity_id.action_set_won()
                self.sale_order_id.opportunity_id.stage_id = self.env['crm.stage'].search([('stage_type', '=', 'order')], limit=1).id or False
            if self.sale_order_id:
                self.sale_order_id.with_context({'add': True}).check_so_status_in_truck()
                self.sale_order_id.set_delivery_line()
            if flag:
                context = dict(self._context or {})
                view = self.env.ref('goexcel_crm.sh_message_wizard')
                context['message'] = "Please contact your Accounting team to fill in with the Accounting information."
                return {
                    'name': 'Success',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                    }


    @api.multi
    def action_set_cancel(self):
        for rec in self:
            if not rec.sale_won_reason_id:
                raise UserError(_("Please Select Won Reason"))
