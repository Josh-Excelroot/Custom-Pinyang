from odoo import models, fields, api
from odoo.exceptions import Warning

# -*- coding: utf-8 -*-
from odoo import fields, models


class RftJobStatus(models.Model):
    _name = "rft.job.status"

    rft_status_wizard = fields.Selection([('01', 'New'),
                                          ('02', 'Job Assigned'),
                                          ('03', 'Job Completed'),
                                          ('04', 'Invoicing Completed'),
                                          ('05', 'POD Attached'), ('06', 'Cancel'), ('07', 'On Hold')],
                                         string="RFT Status",
                                         default="01", copy=False,
                                         track_visibility='onchange', store=True)

    notification_parties = fields.Many2many(
        "res.users", string="Notification Parties",
    )



class TripType(models.Model):
    _name = "trip.type"
    _description = 'Trip Type'
    name = fields.Char(string='Name')

