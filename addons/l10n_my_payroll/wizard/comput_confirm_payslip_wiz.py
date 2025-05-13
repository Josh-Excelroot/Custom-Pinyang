# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class comput_confirm_payslip_wiz(models.TransientModel):

    _name = 'comput.confirm.payslip.wiz'
    _description = "Compute Confirm Pay slip Wizard"

    @api.model
    def default_get(self, fields_list):
        res = super(comput_confirm_payslip_wiz, self).default_get(fields_list)
        context = dict(self._context) or {}
        payslip_obj = self.env['hr.payslip']
        payslip_ids = context.get('active_ids')
        lang_ids = self.env['res.lang'].search([('code', '=', self.env.user.lang)])
        net_amount = 0.0
        for payslip in payslip_obj.browse(payslip_ids):
            for line in payslip.line_ids:
                if line.code == 'NET':
                    net_amount += line.amount
        if lang_ids and lang_ids.ids:
            net_amount = lang_ids.format("%.2f", net_amount, True)
        foramte_string = "Total Amount Before Compute is %s" % net_amount
        for payslip in payslip_obj.browse(payslip_ids):
            payslip.compute_sheet()
        net_amount = 0.0
        for payslip in payslip_obj.browse(payslip_ids):
            for line in payslip.line_ids:
                if line.code == 'NET':
                    net_amount += line.amount
        if lang_ids and lang_ids.ids:
            net_amount = lang_ids.format("%.2f", net_amount, True)
        foramte_string += "\nTotal Amount After Compute is %s" % net_amount
        res['name'] = foramte_string
        return res

    def confirm_selected_payslip(self):
        context = dict(self._context) or {}
        if not context.get('active_ids'):
            return {}
        for payslip in self.env['hr.payslip'].browse(context.get('active_ids', [])):
            if payslip.state == 'done':
                continue
            payslip.compute_sheet()
            payslip.write({'state': 'done'})
        return {}

    name = fields.Text('Employee Net Amount Information', readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: