from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    planned_revenue = fields.Monetary('Expected Yearly Revenue', currency_field='company_currency', track_visibility='always')
    yearly_volume = fields.Float(string="Expected Yearly Volume", track_visibility='always')

    def _compute_active_lead(self):
        for res in self:
            if res.stage_id:
                res.is_lead_open = True
            else:
                res.is_lead_open = False

    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        # super(CRMLead, self)._compute_sale_amount_total()
        for lead in self:
            total = 0.0
            nbr = 0
            company_currency = lead.company_currency or self.env.user.company_id.currency_id
            for order in lead.order_ids:
                if order.state in ['draft', 'sent', 'approve', 'approved', 'cancel', 'lost']:
                    nbr += 1
                if order.state in ['sale', 'done']:
                    total += order.currency_id._convert(order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.sale_number = nbr

    stage_history_ids = fields.One2many('crm.leam.history', 'crm_lead_id', string="Stage History")
    is_lead_open = fields.Boolean('Is the Current User Working', compute='_compute_active_lead', help="Technical field indicating whether the current user is working. ")
    won_reason = fields.Many2one('crm.won.reason', string='Won Reason', index=True, track_visibility='onchange', copy=False)
    pain_identification_id = fields.Many2one('pain.analysis', string="Pain Analysis", track_visibility='onchange', copy=False)
    pain_analysis = fields.Text(string="Pain Detail", help="Identify the possible value proposition and opportunity", copy=False)
    needs_analysis_id = fields.Many2one('needs.analysis', string="Need Analysis", track_visibility='onchange', help="Need Analysis for this CRM.", copy=False)
    needs_analysis = fields.Text(string="Need Detail", copy=False)
    challenges_analysis_id = fields.Many2one('challenges.analysis', string="Challenges Analysis", track_visibility='onchange', copy=False)
    challenges_analysis = fields.Text(string="Challenges Detail", copy=False)
    opportunity_id = fields.Many2one('opportunity.type', string="Opportunity Type", track_visibility='onchange', copy=False)
    valu_solu_ids = fields.One2many('crm.value.solution', 'crm_lead_id', string="Value Solution", copy=False)
    buying_journary_detail_ids = fields.One2many('buying.journary.detail', 'crm_id', string="Buyer Journary", copy=False)
    stage_color = fields.Char(string="stage color", default="#FFFFFF", readonly=True, copy=False)
    is_lead_assigned = fields.Boolean(string="Assigned Lead", default=False, copy=False)
    lost_stage_id = fields.Many2one('crm.stage', string="Lost Stage", readonly=True, copy=False)
    lost_date = fields.Date(string="Lost Date", copy=False)
    source_partner_id = fields.Many2one('res.partner', string="Refferal By", copy=False)
    is_referred = fields.Boolean(string="from Reffered", copy=False)

    # @api.constrains('partner_name')
    # def check_partner_name(self):
    #     for res in self:
    #         if res.partner_name:
    #             old_ids = self.env['crm.lead'].search([('partner_name', '=', res.partner_name), ('id', '!=', res.id)])
    #             if old_ids:
    #                 raise UserError(_("The customer name is existed in the system!"))

    # @api.onchange('partner_name')
    # def onchange_partner_name(self):
    #     if self.partner_name:
    #         old_ids = self.env['crm.lead'].search([('partner_name', '=', self.partner_name)])
    #         if len(old_ids) > 1:
    #             raise UserError(_("The customer name is existed in the system!"))

    @api.onchange('source_id')
    def onchange_source_id(self):
        for res in self:
            if res.source_id and res.source_id.is_referred:
                res.is_referred = True
            else:
                res.is_referred = False

    @api.onchange('pain_identification_id')
    def onchange_pain(self):
        if self.pain_identification_id and self.pain_identification_id.description:
            self.pain_analysis = self.pain_identification_id.description

    @api.onchange('needs_analysis_id')
    def onchnage_need(self):
        if self.needs_analysis_id and self.needs_analysis_id.description:
            self.needs_analysis = self.needs_analysis_id.description

    @api.onchange('challenges_analysis_id')
    def onchange_challenges(self):
        if self.challenges_analysis_id and self.challenges_analysis_id.description:
            self.challenges_analysis = self.challenges_analysis_id.description

    @api.multi
    def action_set_won_rainbowman(self):
        wiz_id = self.env['crm.lead.won'].create({'crm_lead_id': self.id})
        if wiz_id:
            return {
                'name': _('Lead Won Reason'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.lead.won',
                'views': [(self.env.ref('goexcel_crm.crm_lead_won_view_form').id, 'form')],
                'view_id': self.env.ref('goexcel_crm.crm_lead_won_view_form').id,
                'target': 'new',
                'res_id': wiz_id.id,
            }

    @api.model
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        line_obj = self.env['crm.leam.history']
        if res.stage_id:
            res.is_lead_open = True
            data = {
                'from_stage_id': res.stage_id.id,
                'crm_lead_id': res.id
            }
            line_obj.create(data)
        return res

    @api.multi
    def write(self, values):
        line_obj = self.env['crm.leam.history']
        if 'stage_id' in values:
            old_stage_id = self.stage_id
            new_stage_id = self.env['crm.stage'].browse([values['stage_id']])
            if new_stage_id and new_stage_id.sequence < self.stage_id.sequence or 0.0:
                values['stage_color'] = '#FF0000'  # #FF0000- red
            else:
                values['stage_color'] = '#008000'  # #008000- green
        if 'user_id' in values:
            values['is_lead_assigned'] = True
        res = super(CRMLead, self).write(values)
        if res:
            # if 'is_lead_assigned' in values and self.is_lead_assigned and 'user_id' in values:
                # self.send_assign_mail_to_user()
            if 'stage_id' in values:
                if self.stage_id.stage_type == 'order':  # ['order', 'close']:
                    self.set_crm_stage_won_lost_history(old_stage_id, self.stage_id)
                old_data = line_obj.search([('crm_lead_id', '=', self.id), ('to_stage_id', '=', False)], limit=1)
                if old_data:
                    data = {'to_stage_id': values['stage_id'], 'date_end': fields.Datetime.now(), 'stage_change_by_id': self.env.user.id}
                    if self.stage_id.stage_type == 'close':
                        data.update({'lost_lead': True})
                    old_data.write(data)
                data = {'from_stage_id': self.stage_id.id, 'crm_lead_id': self.id}
                if self.stage_id.stage_type not in ['order', 'close']:
                    line_obj.create(data)
        return res

    @api.multi
    def send_assign_mail_to_user(self):
        pass
        # template = self.env.ref('goexcel_crm.lead_assign_mail_template')
        # assert template._name == 'mail.template'
        # if self.user_id:
        #     with self.env.cr.savepoint():
        #         template.with_context(lang=self.user_id.partner_id.lang).sudo().send_mail(self.id, force_send=True, raise_exception=True)

    @api.multi
    def set_crm_stage_won_lost_history(self, last_stage, current_stage):
        line_obj = self.env['crm.leam.history']
        stage_ids = self.env['crm.stage'].search(['&', ('sequence', '>=', last_stage.sequence), ('sequence', '<=', current_stage.sequence)], order="sequence asc")
        cnt = 1
        old_data = False
        for s in stage_ids:
            # find old data is avaible
            if cnt == 1:
                old_data = line_obj.search([('crm_lead_id', '=', self.id), ('from_stage_id', '=', s.id), ('to_stage_id', '=', False)], limit=1)
                if old_data:
                    data = {'to_stage_id': s.id, 'date_end': fields.Datetime.now(), 'stage_change_by_id': self.env.user.id}
                    old_data.write(data)
                cnt += 1
            else:
                last_data = line_obj.search([('crm_lead_id', '=', self.id), ('to_stage_id', '=', False)], limit=1)
                if last_data:
                    data = {'to_stage_id': s.id, 'date_end': fields.Datetime.now(), 'stage_change_by_id': self.env.user.id}
                    last_data.write(data)
                data = {'from_stage_id': s.id, 'crm_lead_id': self.id}
                if s.stage_type != 'order':
                    line_obj.create(data)
                cnt += 1

    @api.multi
    def _run_crm_color_change(self):
        for res in self.search([]):
            last_update_stage_id = self.env['crm.leam.history'].search([('crm_lead_id', '=', res.id), ('to_stage_id', '=', False)], limit=1)
            if last_update_stage_id:
                d1 = fields.Datetime.from_string(last_update_stage_id.date_start)
                d2 = fields.Datetime.from_string(fields.Date.today())
                diff = d2 - d1
                if diff.days > last_update_stage_id.from_stage_id.duration:
                    res.stage_color = '#FFFF00'  # #FFFF00- yellow
                else:
                    if not res.stage_color:
                        res.stage_color = '#008000'  # #008000-green

    @api.multi
    def set_crm_analysis_history(self):
        for res in self:
            # opportunity copy when ,mark as done
            if res.partner_id and res.partner_id.opportunity_id:
                res.partner_id.opportunity_id.id == res.opportunity_id.id
            if res.pain_identification_id and res.partner_id:
                pain_obj = self.env['customer.pain.analysis']
                old_id = pain_obj.search([('pain_id', '=', res.pain_identification_id.id), ('partner_id', '=', res.partner_id.id), ('company_id', '=', res.company_id.id)])
                if not old_id:
                    data = {
                        'pain_id': res.pain_identification_id.id,
                        'analysis': res.pain_analysis or '',
                        'partner_id': res.partner_id.id,
                        'company_id': res.company_id.id
                    }
                    pain_obj.create(data)
            if res.needs_analysis_id and res.partner_id:
                needs_obj = self.env['customer.needs.analysis']
                old_id = needs_obj.search([('need_id', '=', res.needs_analysis_id.id), ('partner_id', '=', res.partner_id.id), ('company_id', '=', res.company_id.id)])
                if not old_id:
                    data = {
                        'need_id': res.needs_analysis_id.id,
                        'partner_id': res.partner_id.id,
                        'company_id': res.company_id.id
                    }
                    needs_obj.create(data)
            if res.challenges_analysis_id and res.partner_id:
                challenges_obj = self.env['customer.challenges.analysis']
                old_id = challenges_obj.search([('challenges_id', '=', res.challenges_analysis_id.id), ('partner_id', '=', res.partner_id.id), ('company_id', '=', res.company_id.id)])
                if not old_id:
                    data = {
                        'challenges_id': res.challenges_analysis_id.id,
                        'partner_id': res.partner_id.id,
                        'company_id': res.company_id.id
                    }
                    challenges_obj.create(data)
            if len(res.valu_solu_ids) > 0 and res.partner_id:
                cust_val_sol_obj = self.env['customer.value.solution']
                for rec in res.valu_solu_ids:
                    cust_val_id = cust_val_sol_obj.search([('name', '=', rec.name), ('partner_id', '=', res.partner_id), ('company_id', '=', res.company_id.id)])
                    if not cust_val_id:
                        data = {
                            'name': rec.name,
                            'solution': rec.solution,
                            'partner_id': res.partner_id.id,
                            'company_id': res.company_id.id
                        }
                        cust_val_sol_obj.create(data)

    @api.multi
    def action_set_lost(self):
        wiz_id = self.env['crm.lead.lost'].create({'crm_lead_id': self.id})
        if wiz_id:
            return {
                'name': _('Lead lost Reason'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.lead.lost',
                'views': [(self.env.ref('goexcel_crm.crm_lead_lost_view_form').id, 'form')],
                'view_id': self.env.ref('goexcel_crm.crm_lead_lost_view_form').id,
                'target': 'new',
                'res_id': wiz_id.id,
            }


class CRMLeadHistory(models.Model):
    _name = 'crm.leam.history'
    _description = 'CRM Stage History'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.depends('date_end', 'date_start')
    def _compute_duration(self):
        for blocktime in self:
            if blocktime.date_end:
                d1 = fields.Datetime.from_string(blocktime.date_start)
                d2 = fields.Datetime.from_string(blocktime.date_end)
                diff = d2 - d1
                seconds = diff.total_seconds()
                # days = seconds // (3600 * 24)
                days = seconds // (24 * 3600)
                n = seconds % (24 * 3600)
                hours = n // 3600
                n %= 3600
                minutes = (n // 60)
                n %= 60
                sec = n

                duration = ""
                if days > 0:
                    duration += str(int(days)) + " Days "
                if hours > 0:
                    duration += str(int(hours)) + " Hours "
                if minutes > 0:
                    duration += str(int(minutes)) + " Minutes "
                if sec > 0:
                    duration += str(int(sec)) + " seconds"
                blocktime.duration = duration
                # blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                blocktime.duration = "0"

    from_stage_id = fields.Many2one('crm.stage', string="From Stage")
    to_stage_id = fields.Many2one('crm.stage', string="To Stage")
    date_start = fields.Datetime('Start Date', default=fields.Datetime.now, required=True)
    date_end = fields.Datetime('End Date')
    duration = fields.Char('Duration', compute='_compute_duration', store=True)
    stage_change_by_id = fields.Many2one('res.users', string="Changed By")
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)
    lost_lead = fields.Boolean(string="Opportunity Lost")


class WonReason(models.Model):
    _name = 'crm.won.reason'
    _description = 'Won Reason'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class LeadStage(models.Model):
    _inherit = "crm.stage"

    duration = fields.Float(string="Duration In days", default=1)
    stage_type = fields.Selection([('close', 'Close'), ('order', 'Order')], string="Stage Type")

    @api.constrains('stage_type')
    def check_constrain(self):
        for res in self:
            # for corol
            close_id = self.env['crm.stage'].search([('stage_type', '=', 'close')])
            if len(close_id) > 1:
                raise ValidationError(_("You can not set Close stage for multiple time"))
            order_id = self.env['crm.stage'].search([('stage_type', '=', 'order')])
            if len(order_id) > 1:
                raise ValidationError(_("You can not set Order stage for multiple time"))


class UtmSource(models.Model):
    _inherit = 'utm.source'

    is_referred = fields.Boolean(string="Referred")
