from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz


def datetime_difference_in_string(datetime1, datetime2):
    delta = relativedelta(datetime1, datetime2)
    yrs, mns, dys, hrs, mins, secs = abs(delta.years), abs(delta.months), abs(delta.days), abs(delta.hours), abs(delta.minutes), abs(
        delta.seconds)
    string_list = [f'{delta} {string}{"s" if delta > 1 else ""}' if delta else ''
                   for delta, string in zip([yrs, mns, dys, hrs, mins, secs], ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second'])]
    return ', '.join(t for t in string_list if t)


def datetime_difference_in_hrs(datetime1, datetime2):
    return abs((datetime1 - datetime2).total_seconds() / 3600)


class CrmStageHistory(models.Model):
    _name = 'crm.stage.history'
    _description = 'Stages History for CRM Leads'

    stage_id = fields.Many2one('crm.stage')
    lead_id = fields.Many2one('crm.lead')
    duration = fields.Char(compute='_compute_duration', help='For how much time lead has been in this stage')
    duration_in_hrs = fields.Float(compute='_compute_duration')

    def _compute_duration(self):
        histories = self.search([('lead_id', '=', self[0].lead_id.id)], order='create_date asc')
        for idx, rec in enumerate(histories):
            # if last, pick current time as next record time
            next_rec_createdate = datetime.utcnow() if rec == histories[-1] else histories[idx + 1].create_date
            rec.duration = datetime_difference_in_string(next_rec_createdate, rec.create_date)
            rec.duration_in_hrs = datetime_difference_in_hrs(next_rec_createdate, rec.create_date)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'kanban':
            self.get_expired_stage_leads().write({'color': 1})
        return super(CRMLead, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                    submenu=submenu)

    new_type = fields.Many2one('crm.won.reason', string='Type')
    won_reason_id = fields.Many2many('crm.won.reason', string='Won Reason')
    industry_id = fields.Many2one('crm.industry',track_visibility="onchange")

    stage_history_ids = fields.One2many('crm.stage.history', 'lead_id')
    stage_stay_time_limit = fields.Datetime(compute='_compute_stage_stay_time_limit')
    reminder_sent = fields.Boolean('Reminder Sent',default=False)

    @api.onchange('stage_id')
    def onchange_stage_reminder_sent(self):
        self.reminder_sent = False

    def send_reminder_email(self):
        crm_lead_record = self.env['crm.lead'].search([])
        ctx = {}
        for record in crm_lead_record:
            total_second = datetime.today() - record.date_last_stage_update
            if record.stage_id.stay_check_duration and total_second.seconds > record.stage_id.stay_check_duration*3600 and not record.reminder_sent:
                ctx['email_from'] = self.env.user.company_id.email
                ctx['email_to'] = record.user_id.login
                ctx['partner_name'] = record.user_id.name
                ctx['duration'] = record.stage_id.stay_check_duration
                # ctx['customer_name'] = self.partner_id.name
                # ctx['amount_total'] = self.amount_total
                ctx['lang'] = self.env.user.lang
                ctx['company_name'] = self.env.user.company_id.name
                print(ctx)
                template = self.env.ref('goexcel_crm_general.crm_lead_reminder_email_template_id')
                template.with_context(ctx).sudo().send_mail(self.id, force_send=True, raise_exception=False)
                record.reminder_sent = True
                # template_obj = self.env['mail.mail']
                # message_body =("Dear "+  record.user_id.name +"<br><br><br> Your lead's state duration has exceeded. Please update.<br><br><br>This is Computer Generated. Please Do Not Reply.")

                # sender = self.env.user.company_id.email
                # email_to = record.user_id.login
                # template_data = {
                #     'subject': 'CRM Leads Status',
                #     'body_html': message_body,
                #     'email_from': sender,
                #     'email_to': email_to
                # }
                # template_id = template_obj.sudo().create(template_data)
                # template_id.sudo().send()
                # print(message_body)
    def get_last_stage_history(self):
        return self.env['crm.stage.history'].search([('lead_id', '=', self.id)], order='create_date desc', limit=1)

    def calculate_stage_stay_time_limit(self):
        stage = self.stage_id
        if self.stage_history_ids:
            stage_changed_on = self.get_last_stage_history().create_date
            if stage.stay_check_type == 'duration':
                return stage_changed_on + timedelta(hours=stage.stay_check_duration)
            elif stage.stay_check_type == 'time':
                stage_changed_next_date = stage_changed_on.date() + timedelta(days=1)
                # convert date obj to datetime, then add hours, then return time based on creator tz
                stage_stay_time_limit_utc = datetime.combine(stage_changed_next_date, datetime.min.time()) \
                                            + timedelta(hours=stage.stay_check_time)
                utc_diff_creator_tz = pytz.timezone(self.create_uid.tz).utcoffset(stage_stay_time_limit_utc)
                return stage_stay_time_limit_utc - relativedelta(hours=utc_diff_creator_tz.total_seconds() / 3600)

        return False

    def _compute_stage_stay_time_limit(self):
        for rec in self:
            rec.stage_stay_time_limit = rec.calculate_stage_stay_time_limit()

    def get_expired_stage_leads(self, stage_name=False):
        leads = self.search([('stage_id.name', '=', stage_name)]) if stage_name else self.search([])
        return leads.filtered(lambda l: l.stage_id.stay_check_type != 'none' and
                                        l.stage_stay_time_limit and
                                        datetime.now() > l.stage_stay_time_limit
                              )

    # won_reason_id = fields.

    # @api.multi
    # def _convert_opportunity_data(self, customer, team_id=False):
    #     """ Extract the data from a lead to create the opportunity
    #         :param customer : res.partner record
    #         :param team_id : identifier of the Sales Team to determine the stage
    #     """
    #     if not team_id:
    #         team_id = self.team_id.id if self.team_id else False
    #     value = {
    #         'planned_revenue': self.planned_revenue,
    #         'probability': self.probability,
    #         'name': self.name,
    #         'partner_id': self.partner_id.id or False,
    #         # 'partner_id': customer.id if customer else False,
    #         'type': 'opportunity',
    #         'date_open': fields.Datetime.now(),
    #         'email_from': customer and customer.email or self.email_from,
    #         'phone': customer and customer.phone or self.phone,
    #         'date_conversion': fields.Datetime.now(),
    #     }
    #     print("Partner_id.id = ", self.partner_id.id)
    #     print(value)
    #     if not self.stage_id:
    #         stage = self._stage_find(team_id=team_id)
    #         value['stage_id'] = stage.id
    #         if stage:
    #             value['probability'] = stage.probability
    #     return value
    #
    # @api.multi
    # def convert_opportunity(self, partner_id, user_ids=False, team_id=False):
    #     customer = False
    #     if partner_id:
    #         #Id=153 Vs Object
    #         customer = self.env['res.partner'].browse(partner_id)
    #          #customer.name = Panjatan Limited.
    #         # customer = partner_id
    #     for lead in self:
    #         if not lead.active or lead.probability == 100:
    #             continue
    #         vals = lead._convert_opportunity_data(customer, team_id)
    #         print(vals)
    #         lead.write(vals)
    #
    #     if user_ids or team_id:
    #         self.allocate_salesman(user_ids, team_id)
    #
    #     return True

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
                'views': [(self.env.ref('goexcel_crm_general.crm_lead_won_view_form').id, 'form')],
                'view_id': self.env.ref('goexcel_crm_general.crm_lead_won_view_form').id,
                'target': 'new',
                'res_id': wiz_id.id,
            }

    @api.multi
    def set_crm_analysis_history(self):
        for res in self:
            print("DSA")

            # # opportunity copy when ,mark as done
            # if res.partner_id and res.partner_id.opportunity_id:
            #     res.partner_id.opportunity_id.id == res.opportunity_id.id
            # if res.pain_identification_id and res.partner_id:
            #     pain_obj = self.env['customer.pain.analysis']
            #     old_id = pain_obj.search(
            #         [('pain_id', '=', res.pain_identification_id.id), ('partner_id', '=', res.partner_id.id),
            #          ('company_id', '=', res.company_id.id)])
            #     if not old_id:
            #         data = {
            #             'pain_id': res.pain_identification_id.id,
            #             'analysis': res.pain_analysis or '',
            #             'partner_id': res.partner_id.id,
            #             'company_id': res.company_id.id
            #         }
            #         pain_obj.create(data)
            # if res.needs_analysis_id and res.partner_id:
            #     needs_obj = self.env['customer.needs.analysis']
            #     old_id = needs_obj.search(
            #         [('need_id', '=', res.needs_analysis_id.id), ('partner_id', '=', res.partner_id.id),
            #          ('company_id', '=', res.company_id.id)])
            #     if not old_id:
            #         data = {
            #             'need_id': res.needs_analysis_id.id,
            #             'partner_id': res.partner_id.id,
            #             'company_id': res.company_id.id
            #         }
            #         needs_obj.create(data)
            # if res.challenges_analysis_id and res.partner_id:
            #     challenges_obj = self.env['customer.challenges.analysis']
            #     old_id = challenges_obj.search(
            #         [('challenges_id', '=', res.challenges_analysis_id.id), ('partner_id', '=', res.partner_id.id),
            #          ('company_id', '=', res.company_id.id)])
            #     if not old_id:
            #         data = {
            #             'challenges_id': res.challenges_analysis_id.id,
            #             'partner_id': res.partner_id.id,
            #             'company_id': res.company_id.id
            #         }
            #         challenges_obj.create(data)
            # if len(res.valu_solu_ids) > 0 and res.partner_id:
            #     cust_val_sol_obj = self.env['customer.value.solution']
            #     for rec in res.valu_solu_ids:
            #         cust_val_id = cust_val_sol_obj.search([('name', '=', rec.name), ('partner_id', '=', res.partner_id),
            #                                                ('company_id', '=', res.company_id.id)])
            #         if not cust_val_id:
            #             data = {
            #                 'name': rec.name,
            #                 'solution': rec.solution,
            #                 'partner_id': res.partner_id.id,
            #                 'company_id': res.company_id.id
            #             }
            #             cust_val_sol_obj.create(data)

    def create_stage_history(self, stage_id):
        self.env['crm.stage.history'].create({
            'stage_id': stage_id,
            'lead_id': self.id,
        })

    @api.model
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        res.create_stage_history(res.stage_id.id)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('stage_id', False):
            self.create_stage_history(vals.get('stage_id'))
            if self.color == 1:
                vals['color'] = 0  # color will set to default after stage change
        return super(CRMLead, self).write(vals)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}
        # auto set the medium to “website” of leads generating from incoming mail server
        custom_values['medium_id'] = self.env['utm.medium'].search([('name', '=', 'Website')], limit=1).id
        return super(CRMLead, self).message_new(msg_dict, custom_values=custom_values)


class CrmWonReason(models.Model):
    _name = 'crm.won.reason'
    _description = 'Won Reason'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CrmIndustry(models.Model):
    _name = 'crm.industry'
    _description = 'CRM Industry'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})
    sequence = fields.Integer(default=10)
    full_name = fields.Char(translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]
