# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import models, api, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class Pcb2Form(models.AbstractModel):
    _name = 'report.my_mtd_report.report_mtd_pcb2'
    _description = "MTD PCB2 Report"

    @api.multi
    def get_data(self, form):
        employee_obj = self.env['hr.employee']
        from_date = form.get('start_date', False)
        to_date = form.get('end_date', False)
        vals = []
        emp_ids = employee_obj.search([('id', 'in', form.get('employee_ids'))])
        for employee in emp_ids:
            res = {}
            user_ids = self.env.ref('hr.group_hr_manager').users.ids
            if SUPERUSER_ID in user_ids:
                user_ids.remove(SUPERUSER_ID)
            employee_ids = employee_obj.search([('user_id', 'in', user_ids)],
                                               limit=1)
            if employee_ids and employee_ids.ids:
                emp = employee_ids
                res['hr_emp'] = emp.name
                res['hr_designation'] = emp.job_id.name
                res['hr_contact'] = emp.work_phone
                res['hr_cmp_name'] = emp.company_id.name
                res['hr_cmp_street'] = emp.company_id.street
                res['hr_cmp_city'] = emp.company_id.city
                res['hr_cmp_zip'] = emp.company_id.zip
                res['hr_cmp_state'] = emp.company_id.state_id.name
                res['hr_cmp_country'] = emp.company_id.country_id.name
            res['name'] = employee.name
            res['emp_tax_no'] = employee.pcb_number or ''
            res['tax_ded_yr'] = from_date.year
            res['staff_no'] = employee.badge_id or ''

            emplyr_E_no = ''
            if employee.company_id and employee.company_id.e_number:
                emplyr_E_no = str(employee.company_id.e_number)
                if employee.company_id.e_number1:
                    emplyr_E_no += ' ' + str(employee.company_id.e_number1)
                if employee.company_id.e_number2:
                    emplyr_E_no += '-' + str(employee.company_id.e_number2)
            res['emplyr_E_no'] = emplyr_E_no

            res['emp_ident_no'] = ''
            if employee.identification_id:
                res['emp_ident_no'] = employee.identification_id
            if not employee.identification_id:
                if employee.passport_id:
                    res['emp_ident_no'] = employee.passport_id

            payslip_ids = self.env['hr.payslip'
                                   ].search([('employee_id', '=', employee.id),
                                             ('date_from', '>=', from_date),
                                             ('date_to', '<=', to_date)
                                             ], order='create_date desc')

            res['jan_mtd'] = res['jan_cp38'] = res['feb_mtd'] = \
                res['feb_cp38'] = res['mar_mtd'] = res['mar_cp38'] = \
                res['apr_mtd'] = res['apr_cp38'] = res['may_mtd'] = \
                res['may_cp38'] = res['jun_mtd'] = res['jun_cp38'] = \
                res['july_mtd'] = res['july_cp38'] = res['aug_mtd'] = \
                res['aug_cp38'] = res['sep_mtd'] = res['sep_cp38'] = \
                res['oct_mtd'] = res['oct_cp38'] = res['nov_mtd'] = \
                res['nov_cp38'] = res['dec_mtd'] = res['dec_cp38'] = \
                res['total_mtd'] = res['total_cp38'] = 0.00
            rec = []

            for payslip in payslip_ids:
                start_date = payslip.date_from
                month = start_date.month
                if month == 1:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['jan_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['jan_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.
                                strptime(start_date, '%Y-%m-%d')
                                .strftime('%B'),
                                'year': datetime.
                                strptime(start_date,
                                         DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 2:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['feb_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['feb_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.
                                strptime(start_date,
                                         '%Y-%m-%d').strftime('%B'),
                                'year': datetime.
                                strptime(start_date,
                                         DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 3:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['mar_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['mar_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.
                                strptime(start_date,
                                         '%Y-%m-%d').strftime('%B'),
                                'year': datetime.
                                strptime(start_date,
                                         DEFAULT_SERVER_DATE_FORMAT
                                         ).year,
                                'income_type': line.name
                            })
                elif month == 4:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['apr_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['apr_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.
                                strptime(start_date,
                                         '%Y-%m-%d').strftime('%B'),
                                'year': datetime.
                                strptime(start_date,
                                         DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 5:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['may_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['may_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 6:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['jun_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['jun_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 7:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['july_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['july_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 8:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['aug_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['aug_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 9:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['sep_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['sep_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 10:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['oct_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['oct_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 11:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['nov_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['nov_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
                elif month == 12:
                    for line in payslip.line_ids:
                        if line.code == 'PCBCURRMONTH':
                            res['dec_mtd'] = line.total
                            res['total_mtd'] += line.total
                        if line.code == 'PCBCP38':
                            res['dec_cp38'] = line.total
                            res['total_cp38'] += line.total
                        if line.code == 'ARR_OTHRS':
                            rec.append({
                                'arr_other': line.total,
                                'month': datetime.strptime(start_date,
                                                           '%Y-%m-%d').strftime('%B'),
                                'year': datetime.strptime(start_date,
                                                          DEFAULT_SERVER_DATE_FORMAT).year,
                                'income_type': line.name
                            })
            res.update({'other': rec})
            vals.append(res)
        return vals

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])
        report_lines = self.get_data(datas[0])
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': datas,
            'docs': docs,
            'get_data': report_lines,
        }
        return docargs
