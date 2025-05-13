from odoo import api, models, fields


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def write(self, values):
        res = super(HRPayslip, self).write(values)

        return res


class HRContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def write(self, values):
        res = super(HRContract, self).write(values)

        return res
