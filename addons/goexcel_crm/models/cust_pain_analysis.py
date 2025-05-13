from odoo import api, models, fields


class PainAnalysis(models.Model):
    _name = 'pain.analysis'
    _description = 'Pain Analysis'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    cust_pain_analysis_ids = fields.One2many('customer.pain.analysis', 'pain_id', string="Brand Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CustomerPainAnalysis(models.Model):
    _name = 'customer.pain.analysis'
    _description = "Customer Pain Analysis"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    pain_id = fields.Many2one('pain.analysis', string="Identification", ondelete="cascade")
    description = fields.Text(string="Description")
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    @api.onchange('pain_id')
    def onchange_pain_id(self):
        if self.pain_id:
            self.description = self.pain_id.description


class NeedsAnalysis(models.Model):
    _name = 'needs.analysis'
    _description = 'Needs Analysis'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    cust_needs_analysis_ids = fields.One2many('customer.needs.analysis', 'need_id', string="Needs Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CustomerNeedsAnalysis(models.Model):
    _name = 'customer.needs.analysis'
    _description = "Customer Pain Analysis"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    need_id = fields.Many2one('needs.analysis', string="Needs", ondelete="cascade")
    description = fields.Text(string="Description")
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    @api.onchange('need_id')
    def onchange_need_id(self):
        if self.need_id:
            self.description = self.need_id.description

class ChallengesAnalysis(models.Model):
    _name = 'challenges.analysis'
    _description = 'Challenges Analysis'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    cust_challenges_analysis_ids = fields.One2many('customer.challenges.analysis', 'challenge_id', string="Challenges Detail")
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class CustomerChallengesAnalysis(models.Model):
    _name = 'customer.challenges.analysis'
    _description = "Customer Challenges Analysis"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    challenge_id = fields.Many2one('challenges.analysis', string="Challenges", ondelete="cascade")
    description = fields.Text(string="Description")
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    @api.onchange('challenge_id')
    def onchange_challenge_id(self):
        if self.challenge_id:
            self.description = self.challenge_id.description
    
class CustValSolution(models.Model):
    _name = 'customer.value.solution'
    _description = "Customer Value and Solution"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Value", required=True)
    solution = fields.Char(string="Solution", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class CRMValSolution(models.Model):
    _name = 'crm.value.solution'
    _description = "Customer CRM Value and Solution"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Value", required=True)
    solution = fields.Char(string="Solution", required=True)
    crm_lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)


class OpporyunityType(models.Model):
    _name = 'opportunity.type'
    _description = 'Opportunity'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", translate=True)
    description = fields.Text('Description', translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    sequence = fields.Integer(default=10)

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]
