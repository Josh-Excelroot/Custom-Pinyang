# See LICENSE file for full copyright and licensing details

from odoo import models, fields


class AttendancePolicies(models.Model):
    """Attendance Policies."""

    _name = 'hr.attendance.policies'
    _description = 'HR Attendance Policies'

    name = fields.Char(string="Name",)
    overtime_id = fields.Many2one(
        'hr.attendance.overtime',
        string='Overtime Rule', ondelete="restrict",
    )
    diff_rule_id = fields.Many2one(
        "hr.attendance.diff", string="Difference Rule",
        ondelete="restrict")
    late_id = fields.Many2one(
        "hr.attendance.late", string="Late Rule",
        ondelete="restrict")
    absent_id = fields.Many2one(
        "hr.attendance.absence", string="Absence Rule",
        ondelete="restrict")
