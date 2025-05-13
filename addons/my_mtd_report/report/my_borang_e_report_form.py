# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, ustr


class IncometaxForm(models.AbstractModel):

    _name = 'report.my_mtd_report.borang_e_report_my'
    _description = "Borang E Report"

    @api.multi
    def get_data(self, data):
        data = data['form']
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        vals = []
        emp_ids = self.env['hr.employee'].search([
            ('id', 'in', data.get('employee_ids'))])
        year = datetime.today().year
        start_date = datetime.strptime('%s-01-01' % ustr(int(year)),
                                       DEFAULT_SERVER_DATE_FORMAT).date()
        stop_date = '%s-12-31' % ustr(int(year))
        for employee in emp_ids:
            res = {}
            user = self.env['hr.employee'].search([
                ('user_id', '=', self._uid)], limit=1)
            res['hr_user'] = user.name
            if user.identification_id:
                res['hr_user_ident'] = user.identification_id
            elif user.passport_id:
                res['hr_user_ident'] = user.passport_id
            else:
                res['hr_user_ident'] = ''
            res['hr_position'] = user.job_id.name
            res['total_join_emp'] = 0
            res['total_wrk_stp_emp'] = 0
            if employee.join_date:
                if employee.join_date > start_date:
                    res['total_join_emp'] += 1
            if employee.emp_status == 'in_notice' and employee.last_date:
                emp_last_date = employee.last_date
                if emp_last_date > start_date and emp_last_date < stop_date:
                    res['total_wrk_stp_emp'] += 1
            total_pcb = 0
            if employee.pcb_number:
                total_pcb += 1
            res['total_emp_pcb'] = total_pcb
            res['emp_name'] = employee.name
            res['emp_incometax'] = employee.pcb_number
            if employee.identification_id:
                res['identification_no'] = employee.identification_id
            elif employee.passport_id:
                res['identification_no'] = employee.passport_id
            else:
                res['identification_no'] = ''
            res['child_no'] = len(employee.emp_child_ids)
            res['qua_child'] = len(employee.emp_child_ids) * 2000
            if employee.pcb_borner_by_emp is True:
                res['tax_accured'] = "1"
            else:
                res['tax_accured'] = "2"
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_from', '>=', from_date),
                ('date_to', '<=', to_date)])
            total_gross = total_addition = ytd_bik = ytd_vola = ytd_esos = \
                non_tx_allw = ytd_dedu = ytd_zakat_tp1 = ytd_epf_e = \
                ytd_zakat_ded = ytd_pcb_ded = ytd_cp38_ded = 0.00
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.category_id.code == 'ADDT':
                        total_addition += line.total
                    elif line.category_id.code == 'ALWNT':
                        non_tx_allw += line.total
                    elif line.category_id.code == 'DED':
                        ytd_dedu += line.total
                    elif line.category_id.code == 'EPF_E':
                        ytd_epf_e += line.total
                    elif line.category_id.code == 'ZAKAT':
                        ytd_zakat_ded += line.total

                    if line.code == 'GROSS':
                        total_gross += line.total
                    elif line.code == 'BIK':
                        ytd_bik += line.total
                    elif line.code == 'VOLA':
                        ytd_vola += line.total
                    elif line.code == 'ESOS':
                        ytd_esos += line.total
                    elif line.code == 'ZAKAT_TP1':
                        ytd_zakat_tp1 += line.total
                    elif line.code == 'PCBCURRMONTH':
                        ytd_pcb_ded += line.total
                    elif line.code == 'PCBCP38':
                        ytd_cp38_ded += line.total
            res['gross'] = total_gross - total_addition
            res['ytd_bik'] = ytd_bik
            res['ytd_vola'] = ytd_vola
            res['ytd_esos'] = ytd_esos
            res['non_tx_allw'] = non_tx_allw
            res['ytd_dedu'] = ytd_dedu
            res['ytd_zakat_tp1'] = ytd_zakat_tp1
            res['ytd_epf_e'] = ytd_epf_e
            res['ytd_zakat_ded'] = ytd_zakat_ded
            res['ytd_pcb_ded'] = ytd_pcb_ded
            res['ytd_cp38_ded'] = ytd_cp38_ded
            vals.append(res)
        return vals

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
            'get_data': self.get_data(data)
        }
        return docargs
