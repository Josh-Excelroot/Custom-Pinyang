from odoo import models, fields

class ContactUs(models.Model):
    _name = 'alan_customize.contactus'
    _description = 'Contact Us Submission'

    name = fields.Char('Subject')
    contact_name = fields.Char('Your Name')
    email_from = fields.Char('Email')
    phone = fields.Char('Phone')
    partner_name = fields.Char('Company')
    description = fields.Text('Message')