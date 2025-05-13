from odoo import models, fields, api


class VisitPurpose(models.Model):
    _name = 'visit.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class VisitOutcome(models.Model):
    _name = 'visit.outcome'
    _description = 'Visit Outcome'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    is_unsucessfull = fields.Boolean(string="UnSuccessfull")
    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class VisitSpanco(models.Model):
    _name = 'visit.spanco'
    _description = "Visit CRM Stage"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    stage = fields.Many2one('crm.stage', string='CRM Stage', required=True)
    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class VisitSpancoValue(models.Model):
    _name = "visit.spanco.value"
    _description = "Visit Value"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class VisitSpancoPurpose(models.Model):
    _name = "visit.spanco.purpose"
    _description = "Visit CRM Purpose"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


class VisitSpancoLine(models.Model):
    _name = "visit.spanco.line"
    _description = "Visit CRM Line"

    visit_id = fields.Many2one('visit', string="Visit")
    visit_spanco_purpose_id = fields.Many2one('visit.spanco.purpose', string="Objective")
    visit_spanco_value_id = fields.Many2one('visit.spanco.value', string="Value")


class VisitMethod(models.Model):
    _name = 'visit.method'
    _description = 'Visit Method'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)', 'Name must be unique within an application!')]


# class VisitAddress(models.Model):
#     _name = 'visit.location'
#     _description = "Visit Location"


#     name = fields.Char(string="Name")
#     street = fields.Char(string='Street')
#     street2 = fields.Char(string='Street 2')
#     city = fields.Char(string='City')
#     state_id = fields.Many2one('res.country.state', string='State')
#     zip = fields.Char(string='Zip')
#     country_id = fields.Many2one('res.country', string='Country')
#     phone = fields.Char(string='Phone')
#     mobile = fields.Char(string='Mobile')
#     fax = fields.Char(string='Fax')
#     email = fields.Char(string='Email')
