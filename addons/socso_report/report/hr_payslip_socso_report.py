# See LICENSE file for full copyright and licensing details

from odoo import models, api


class HrPayslipSocsoReport(models.AbstractModel):

    _name = 'report.socso_report.ppt_hr_payslip_summary_receipt'
    _description = "SOCSO Report"

    def get_name(self, datas):
        records = []
        res = {}
        finaltotalscsey = 0
        payslip_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', datas.get('date_from')),
            ('date_from', '<=', datas.get('date_to')),
            ('employee_id', 'in', datas.get('employee_ids')),
            ('state', 'in', ['draft', 'done', 'verify'])
            ])
        for payslip in payslip_ids:
            join_date = payslip.employee_id.join_date and \
                payslip.employee_id.join_date.strftime('%d-%m-%Y') or ''
            totalscsey = 0.0
            for line in payslip.line_ids:
                if line.code in ['SCSY', 'SCSE']:
                    totalscsey += line.total
            res = {
               'name': payslip.employee_id.name,
               'identification_no': payslip.employee_id.identification_id,
               'no_perkeso': payslip.employee_id.no_perkeso,
               'joindate': join_date,
               'totalscsey': totalscsey,
               }
            finaltotalscsey += res['totalscsey']
            records.append(res)
        new_list = []
        page_no = 0
        scsey_grand_total_after = 0.0
        scsey_grand_total_before = 0.0
        totalrecord = 0
        for row in range(0, int(len(records) / 30 + 1)):
            scsey_total = 0.0
            page_no += 1
            val = records[row * 30: row * 30 + 30]
            if not new_list:
                scsey_grand_total_before = 0.0
            else:
                scsey_grand_total_before = scsey_grand_total_after
            for i in range(0, len(val)):
                scsey_total = val[i].get('totalscsey')
                scsey_grand_total_after += scsey_total or 0.0
                totalrecord += 1
            if val:
                user = self.env['hr.employee'].search([
                    ('user_id', '=', self._uid)], limit=1)
                new_list.append({
                    'page_number': page_no,
                    'total_after_1': scsey_grand_total_after,
                    'total_before_1': scsey_grand_total_before,
                    'records': val,
                    'totalrecord': totalrecord,
                    'name': user.name,
                    'phone': user.work_phone
                    })
        return new_list

    def get_companyname(self):
        user_rec = self.env.user
        com_list = [{
            'company_name': user_rec.company_id.name,
            'company_street': user_rec.company_id.street,
            'company_zip': user_rec.company_id.zip,
            'company_city': user_rec.company_id.city,
            }]
        return com_list

    def get_socso_details(self):
        return self.env.user.company_id and self.env.user.company_id.sosco_number or ''

    def get_month(self, datas):
        date_to = datas.get('date_to') or False
        return date_to and date_to.strftime('%m')

    def get_year(self, datas):
        date_to = datas.get('date_to') or False
        return date_to and date_to.strftime('%Y')

    def get_date(self, datas):
        date_to = datas.get('date_to') or False
        return date_to and date_to.strftime('%d/%m/%Y')

    def get_final_total_scsey(self, datas):
        finaltotalscsey = 0.0
        payslip_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', datas.get('date_from')),
            ('date_from', '<=', datas.get('date_to')),
            ('employee_id', 'in', datas.get('employee_ids')),
            ('state', 'in', ['draft', 'done', 'verify'])
            ])
        for payslip in payslip_ids:
            for line in payslip.line_ids:
                if line.code in ['SCSY', 'SCSE']:
                    finaltotalscsey += line.total
        return finaltotalscsey

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
            'get_name': self.get_name(datas),
            'get_companyname': self.get_companyname(),
            'get_month': self.get_month(datas),
            'get_year': self.get_year(datas),
            'get_socso_details': self.get_socso_details(),
            'get_date': self.get_date(datas),
            'get_final_total_scsey': self.get_final_total_scsey(datas),
          }
        return docargs
