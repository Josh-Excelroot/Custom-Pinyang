# See LICENSE file for full copyright and licensing details

from datetime import datetime
from odoo import models, api


class HrPayslipEpfReport(models.AbstractModel):
    _name = 'report.my_pf_report.hr_payslip_epf_report'
    _description = "EPF Report"

    def get_companyname(self):
        user_rec = self.env.user
        comp_list = [{
            'company_name': user_rec.company_id.name,
            'company_street': user_rec.company_id.street,
            'company_zip': user_rec.company_id.zip,
            'company_city': user_rec.company_id.city,
        }]
        return comp_list

    def get_payroll_admin(self):
        grp_result = self.env.ref('l10n_my_payroll.group_hr_payroll_admin')
        result = {}
        if grp_result and grp_result.users:
            for user in grp_result.users[0]:
                emp_rec = self.env['hr.employee'].search([
                    ('user_id', '=', user.id)], limit=1)
                result.update({
                    'name': user.name,
                    'position': emp_rec.job_id.name,
                    'department': emp_rec.job_id.department_id.name,
                    'telephone': emp_rec.work_phone,
                    'email': emp_rec.work_email,
                    'identification_no': emp_rec.identification_id
                })
        return result

    def get_monthyear(self, datas):
        date_to = datas.get('date_to')
        monthyear = date_to.strftime('%m%Y')
        return monthyear

    def get_from_to_dates(self, datas):
        res = {'form_date': '', 'to_date': ''}
        if datas.get('date_to'):
            res['to_date'] = datas.get('date_to').strftime('%b-%Y')
        if datas.get('date_from'):
            res['form_date'] = datas.get('date_from').strftime('%b-%Y')
        return res

    def get_date(self):
        date_formate = datetime.today().date().strftime('%d/%m/%Y')
        return date_formate

    def get_name(self, datas):
        records = []
        res = {}
        payslip_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', datas.get('date_from')),
            ('date_to', '<=', datas.get('date_to')),
            ('employee_id', 'in', datas.get('employee_ids')),
            ('state', 'in', ['draft', 'done', 'verify'])])
        totalrecord = 0
        net = 0.0
        name = []
        for payslip in payslip_ids:
            if payslip.employee_id.name not in name:
                name.append(payslip.employee_id.name)
            totalrecord += 1
            epfy = 0.0
            epfe = 0.0
            if payslip.contract_id:
                net = payslip.contract_id.wage
            for line in payslip.line_ids:
                if line.code == 'EPFY':
                    epfy = line.total
                elif line.code == 'EPFE':
                    epfe = line.total
            res = {
                'seq': totalrecord,
                'name': payslip.employee_id.name,
                'identification_no': payslip.employee_id.identification_id,
                'userid': payslip.employee_id.user_id.name,
                'ahli': payslip.employee_id.epf_no,
                'epfy': epfy or 0.0,
                'epfe': epfe,
                'net': net,
                'employee': len(name),
            }
            records.append(res)
        new_list = []
        new_list.append(res)
        epfy_grand_total_after = 0.0
        epfe_grand_total_after = 0.0
        epfy_grand_total_before = 0.0
        epfe_grand_total_before = 0.0
        page_no = 0
        for row in range(0, int(len(records) / 11 + 1)):
            page_no += 1
            epfy_total = 0.0
            epfe_total = 0.0
            val = records[row * 11: row * 11 + 11]
            if not new_list:
                epfy_grand_total_before = 0.0
            else:
                epfy_grand_total_before = epfy_grand_total_after
            if not new_list:
                epfe_grand_total_before = 0.0
            else:
                epfe_grand_total_before = epfe_grand_total_after
            for i in range(0, len(val)):
                epfy_total = val[i].get('epfy')
                epfy_grand_total_after += epfy_total or 0.0
                totalrecord += 1
                epfe_total = val[i].get('epfe')
                epfe_grand_total_after += epfe_total or 0.0
            if val:
                new_list.append({
                    'page_number': page_no,
                    'total_after_1': epfy_grand_total_after,
                    'total_after_2': epfe_grand_total_after,
                    'total_before_1': epfy_grand_total_before,
                    'total_before_2': epfe_grand_total_before,
                    'records': val
                })
        return new_list

    def get_totalrm1(self, datas):
        res = {}
        totalepfy = 0.0
        totalepfe = 0.0
        payslip_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', datas.get('date_from')),
            ('date_to', '<=', datas.get('date_to')),
            ('employee_id', 'in', datas.get('employee_ids')),
            ('state', 'in', ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            epfy = 0.0
            epfe = 0.0
            net = 0.0
            for line in payslip.line_ids:
                if line.code == 'EPFY':
                    epfy = line.total
                elif line.code == 'EPFE':
                    epfe = line.total
                elif line.code == 'NET':
                    net = line.total
            res = {
                'epfy': epfy,
                'epfe': epfe,
                'net': net,
            }
            totalepfy += res['epfy']
            totalepfe += res['epfe']
        totalrm = totalepfe + totalepfy
        return totalrm or 0.00

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])[0]
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'data': data,
            'get_payroll_admin': self.get_payroll_admin(),
            'get_monthyear': self.get_monthyear(datas),
            'get_from_to_dates': self.get_from_to_dates(datas),
            'get_date': self.get_date(),
            'get_totalrm1': self.get_totalrm1(datas),
            'get_name': self.get_name(datas),
            'get_companyname': self.get_companyname(),
        }
        return docargs
