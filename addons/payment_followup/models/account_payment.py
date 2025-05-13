from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if self.partner_type == 'customer':
            # Comment line - 16-17 /Add line - 12 - 15 -> Issue: Followup Level is not working properly - 9 aug'22
        	move_lines = self.env['account.move.line'].search([('partner_id', '=', self.partner_id.id), ('followup_line_id', '!=', False), ('followup_date', '!=', False)])
        	if move_lines:
        		move_lines.write({'followup_line_id': False, 'followup_date': False})
        	self.partner_id.write({'last_sent_date': False, 'last_sent_by': False, 'last_followup_level_id': False, 'last_action_type': False, 'last_send_type': False})
            # self._cr.execute("update account_move_line set followup_line_id=NULL, followup_date=NULL where partner_id = %s and followup_line_id != NULL and followup_date != NULL" % self.partner_id.id)
            # self._cr.execute("update res_partner set last_sent_date=NULL, last_sent_by=NULL, last_followup_level_id=NULL,last_action_type=NULL, last_send_type=NULL where id = %s" % self.partner_id.id)
        return res
