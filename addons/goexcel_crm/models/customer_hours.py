from odoo import api, models, fields

DAYS = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ]

VISITING_HOUR = [
    ('00:00', '00:00'),
    ('01:00', '01:00'),
    ('02:00', '02:00'),
    ('03:00', '03:00'),
    ('04:00', '04:00'),
    ('05:00', '05:00'),
    ('06:00', '06:00'),
    ('07:00', '07:00'),
    ('08:00', '08:00'),
    ('09:00', '09:00'),
    ('10:00', '10:00'),
    ('11:00', '11:00'),
    ('12:00', '12:00'),
    ('13:00', '13:00'),
    ('14:00', '14:00'),
    ('15:00', '15:00'),
    ('16:00', '16:00'),
    ('17:00', '17:00'),
    ('18:00', '18:00'),
    ('19:00', '19:00'),
    ('20:00', '20:00'),
    ('21:00', '21:00'),
    ('22:00', '22:00'),
    ('23:00', '23:00'),
    ('24:00', '24:00')
]


# class CustomerHours(models.Model):
#     _name = 'customer.hours'
#     _description = 'Customer Hours'
#     _order = 'id desc'
#     _rec_name = 'partner_id'

#     @api.model
#     def _get_company(self):
#         return self.env.user.company_id

#     partner_id = fields.Many2one('res.partner', string="Customer", required=True)
#     # visiting_housr_ids = fields.One2many('visiting.hours', 'customer_hourse_id')
#     company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
#     active = fields.Boolean('Active', default=True)
#     sequence = fields.Integer(default=10)
    

class OperatingHourse(models.Model):
    _name = 'operating.hours'
    _description = 'Customer Operating Hours'
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    # customer_hourse_id = fields.Many2one('customer.hours', string="Operating Hours", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    from_day = fields.Selection(DAYS, string='From Day', required=True)
    to_day = fields.Selection(DAYS, string="To day")
    open_time = fields.Selection(VISITING_HOUR, string="Opening Time")
    close_time = fields.Selection(VISITING_HOUR, string="Close Time")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=10)


class VisitingHourse(models.Model):
    _name = "visiting.hours"
    _description = "Customer Visiting Hourse"
    _order = 'id desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    # customer_hourse_id = fields.Many2one('customer.hours', string="Operating Hours", ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    from_day = fields.Selection(DAYS, string='From Day', required=True)
    to_day = fields.Selection(DAYS, string="To day")
    open_time = fields.Selection(VISITING_HOUR, string="Opening Time")
    close_time = fields.Selection(VISITING_HOUR, string="Close Time")
    contact_person_id = fields.Many2one('res.partner', string="Contact Person")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=10)


class PreferedVisiting(models.Model):
    _name = 'prefered.visiting'
    _description = "Prefered Visiting"

    @api.depends('day', 'from_time', 'to_time')
    def compute_prefered_day(self):
        for res in self:
            name = ""
            time = ""
            name = res.day or ''
            if res.from_time and not res.to_time:
                time = res.from_time
            if res.to_time and not res.from_time:
                time = res.to_time
            if res.from_time and res.to_time:
                time = res.from_time + '-' + res.to_time
            if name and time:
                name += " -> " + "(" + time + ")"
            res.name = name

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Visiting", readonly=True, copy=False, compute=compute_prefered_day, store=True)
    day = fields.Selection(DAYS, string='From Day', required=True)
    from_time = fields.Selection(VISITING_HOUR, string="From Time", required=True)
    to_time = fields.Selection(VISITING_HOUR, string="To Time")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company, help='The company this user is currently working for.', context={'user_preference': True})
    color = fields.Integer(string='Color Index')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=10)
