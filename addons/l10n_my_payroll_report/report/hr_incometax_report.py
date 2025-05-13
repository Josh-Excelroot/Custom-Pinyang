# See LICENSE file for full copyright and licensing details

from odoo import models, api


class HrPayslipIncometaxReport(models.AbstractModel):

    _name = 'report.l10n_my_payroll_report.hr_payslip_report'
    _description = "Pay Slip Report"

    def get_companyname(self, datas):
        user_rec = self.env.user
        emp_id = self.env['hr.employee'].search(
            [('user_id', '=', user_rec.id)], limit=1)
        emp_lst=[]
        employer_tax_e_number = ''
        if user_rec.company_id.employer_e_no:
            employer_tax_e_number = user_rec.company_id.employer_e_no.replace('-', '')
        res = {
             'emp_name':emp_id.name,
             'emp_designation':emp_id.job_id.name,
             'emp_identification_id':emp_id.identification_id,
             'emp_telephone':emp_id.work_phone,
             'company_name':user_rec.company_id.name,
             'company_street':user_rec.company_id.street,
             'company_zip':user_rec.company_id.zip,
             'company_city':user_rec.company_id.city,
             'company_ref_no':employer_tax_e_number,
             'company_regstration_no':user_rec.company_id.company_registry,
             'business_no':user_rec.company_id.business_rn
             }
        emp_lst.append(res)
        return emp_lst

    def get_monthname(self, datas):
        date_to = datas.get('date_to') or False
        return date_to and date_to.strftime('%B')

    def get_year(self, datas):
        date_to = datas.get('date_to') or False
        return date_to and date_to.strftime('%Y')

    def get_name(self, datas):
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        name = datas.get('employee_ids') or False
        states = ['draft', 'done', 'verify']
        res = {}
        data_lst=[]
        totalpcb = 0
        totalcp38 = 0
        totalrecord = 0
        payslip_ids = self.env['hr.payslip'
                               ].search([('date_from', '>=', date_from),
                                         ('date_from', '<=', date_to),
                                         ('employee_id', 'in', name),
                                         ('state', 'in', states)])
        for payslip in payslip_ids:
            totalrecord += 1
            PCB = 0.0
            CP38 = 0.0
            for line in payslip.line_ids:
                if line.code == 'PCBCURRMONTH':
                    PCB = line.total
                if line.code == 'PCBCP38':
                    CP38 = line.total
            res = {
                'seq': totalrecord,
                'incometax_no': payslip.employee_id.pcb_number or '',
                'name': payslip.employee_id.name,
                'identification_no': payslip.employee_id.identification_id,
                'userid': payslip.employee_id.user_id.name,
                'passportno': payslip.employee_id.passport_id,
                'statecode': payslip.employee_id.country_id.code,
                'pcb': PCB,
                'cp38': CP38,
                'company_name': payslip.employee_id.company_id.name,
            }
            totalpcb += res['pcb']
            totalcp38 += res['cp38']
            data_lst.append(res)
        return data_lst

    def get_totalpcb1(self, datas):
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        name = datas.get('employee_ids') or False
        res = {}
        totalpcb = 0.0
        payslip_ids = self.env['hr.payslip'
                               ].search([('date_from', '>=', date_from),
                                         ('date_from', '<=', date_to),
                                         ('employee_id', 'in', name),
                                         ('state', 'in',
                                          ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            PCB = 0.0
            for line in payslip.line_ids:
                if line.code == 'PCBCURRMONTH':
                    PCB = line.total
            res = {'pcb': PCB}
            totalpcb += res['pcb']
        return totalpcb

    def get_totalcp381(self, datas):
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        name = datas.get('employee_ids') or False
        res = {}
        totalcp38 = 0.0
        totalrecord = 0
        payslip_ids = self.env['hr.payslip'
                               ].search([('date_from', '>=', date_from),
                                         ('date_from', '<=', date_to),
                                         ('employee_id', 'in', name),
                                         ('state', 'in',
                                          ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            totalrecord += 1
            CP38 = 0.0
            for line in payslip.line_ids:
                if line.code == 'PCBCP38':
                    CP38 = line.total
            res = {'cp38': CP38}
            totalcp38 += res['cp38']
        return totalcp38

    def get_totalpcb_cp381(self, datas):
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        name = datas.get('employee_ids') or False
        res = {}
        totalpcb = 0.0
        totalcp38 = 0.0
        payslip_ids = self.env['hr.payslip'
                               ].search([('date_from', '>=', date_from),
                                         ('date_from', '<=', date_to),
                                         ('employee_id', 'in', name),
                                         ('state', 'in',
                                          ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            PCB = 0.0
            CP38 = 0.0
            for line in payslip.line_ids:
                if line.code == 'PCBCURRMONTH':
                    PCB = line.total
                if line.code == 'PCBCP38':
                    CP38 = line.total
            res = {'pcb': PCB,
                   'cp38': CP38,
                   }
            totalpcb += res['pcb']
            totalcp38 += res['cp38']
        return totalpcb + totalcp38

    def get_totalrecord(self, datas):
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        name = datas.get('employee_ids') or False
        pcb_totalrecord = 0
        cp38_total_record = 0
        emp = []
        res = {}
        payslip_ids = self.env['hr.payslip'
                               ].search([('date_from', '>=', date_from),
                                         ('date_from', '<=', date_to),
                                         ('employee_id', 'in', name),
                                         ('state', 'in',
                                          ['draft', 'done', 'verify'])])
        for payslip in payslip_ids:
            if not payslip.employee_id.name in emp:
                emp.append(payslip.employee_id.name)
                for line in payslip.line_ids:
                    if line.code == 'PCBCURRMONTH' and line.amount != 0:
                        pcb_totalrecord += 1
                    if line.code == 'PCBCP38':
                        cp38_total_record += 1
        res.update({
            'pcb_totalrecord': pcb_totalrecord,
            'cp38_total_record': cp38_total_record
        })
        return res

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
            'get_monthname': self.get_monthname(datas),
            'get_year': self.get_year(datas),
            'get_companyname': self.get_companyname(datas),
            'get_name': self.get_name(datas),
            'get_totalpcb1': self.get_totalpcb1(datas),
            'get_totalcp381': self.get_totalcp381(datas),
            'get_totalpcb_cp381': self.get_totalpcb_cp381(datas),
            'get_totalrecord': self.get_totalrecord(datas)
        }
        return docargs
