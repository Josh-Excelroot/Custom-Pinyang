from odoo import api, models, fields
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_team(self):
        user_id = self.env.user.id,
        company_id = self.env.user.company_id.id,
        team_id = self.env['crm.team'].search([
            '|', ('user_id', '=', user_id), ('member_ids', '=', user_id),
            '|', ('company_id', '=', False), ('company_id', 'child_of', [company_id])
        ], limit=1)
        return team_id

    team_id = fields.Many2one('crm.team', 'Sales Team', default=_get_default_team)

    @api.model
    # Ahmad Zaman - 23/9/24 - Displaying an error when partner name is duplicated
    def create(self, vals):
        param_config = self.env['ir.config_parameter'].sudo()
        error_message_enabled = param_config.get_param('restrict_product_partner.show_error') == 'True'

        partner_name = vals.get('name', '')
        if partner_name:
            existing_partner = self.search(
                [('name', '=', partner_name),
                 ('company_id', '=', self.env.user.company_id.id),
                 ('company_type', '=', 'company')],
                limit=1)
            if existing_partner and error_message_enabled:
                raise ValidationError("A partner with the same name already exists in the system.")

        partner = super(ResPartner, self).create(vals)
        return partner

    @api.multi
    # Ahmad Zaman - 23/9/24 - Displaying an error when partner name is duplicated
    def write(self, vals):
        param_config = self.env['ir.config_parameter'].sudo()
        error_message_enabled = param_config.get_param('restrict_product_partner.show_error') == 'True'

        partner_name = vals.get('name', '')
        if partner_name:
            existing_partner = self.search(
                [('name', '=', partner_name),
                 ('company_id', '=', self.env.user.company_id.id),
                 ('company_type', '=', 'company')],
                limit=1)
            if existing_partner and error_message_enabled:
                raise ValidationError("A partner with the same name already exists in the system.")

        partner = super(ResPartner, self).write(vals)
        return partner