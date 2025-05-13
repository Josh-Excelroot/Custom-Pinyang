# See LICENSE file for full copyright and licensing details
from odoo import models, api, SUPERUSER_ID
from datetime import date

class IncometaxForm(models.AbstractModel):

    _name = 'report.my_mtd_report.income_tax_report_my'
    _description = "Income Tax Report"

    @api.multi
    def get_data(self, form):
        employee_obj = self.env['hr.employee']
        from_date = form.get('from_date', False)
        year = from_date.year
        from_date = from_date.strftime('%Y-%m-%d')
        to_date = form.get('to_date', False)
        to_date = to_date.strftime('%Y-%m-%d')
        current_year = date.today().year
        vals = []
        user_ids = self.env.ref('hr.group_hr_manager').users.ids
        emp_ids = employee_obj.search([
            ('id', 'in', form.get('employee_ids'))])
        for employee in emp_ids:
            res = {}
            if SUPERUSER_ID in user_ids:
                user_ids.remove(SUPERUSER_ID)
            employee_ids = employee_obj.search([('user_id', 'in', user_ids)])
            if employee_ids:
                emp = employee_ids[0]
                res['hr_emp'] = self.env.user.name
                res['hr_designation'] = emp.job_title
                res['hr_cmp_contact'] = emp.company_id.phone
                res['hr_cmp_name'] = emp.company_id.name
                res['hr_cmp_street'] = emp.company_id.street
                res['hr_cmp_city'] = emp.company_id.city
                res['hr_cmp_state'] = emp.company_id.state_id.name
                res['hr_cmp_zip'] = emp.company_id.zip
                res['hr_cmp_country'] = emp.company_id.country_id.name
            res['payroll_no'] = employee.emp_reg_no
            res['name'] = employee.name
            res['designation'] = employee.job_title or False
            res['id_no'] = employee.identification_id or False
            res['passport'] = employee.passport_id or False
            res['socso'] = employee.no_perkeso or ''
            res['epf_no'] = employee.epf_no or ''
            res['no_child'] = len(employee.emp_child_ids)
            employer_tax_e_number = ''
            if employee.company_id.employer_e_no:
                employer_tax_e_number = employee.company_id.employer_e_no.replace('-', '')
            res['e_number'] = employer_tax_e_number or ''
            res['c_income_tax'] = employee.pcb_number or False
            res['child_relif'] = len(employee.emp_child_ids) * 2000
            res['year'] = year
            res['current_year'] = current_year
            # if employee.badge_id:
            #     res['payroll_no'] = employee.badge_id
            contract_id = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '>=', from_date),
                ('date_end', '<=', to_date)], limit=1)
            if contract_id.date_start and contract_id.date_start < from_date:
                res['commencement'] = contract_id.date_start
            # else:
            #     res['commencement'] = False
            res['cessation'] = contract_id.date_end or False
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_from', '>=', from_date),
                ('date_to', '<=', to_date)])
            # if not employee.badge_id:
            #     if payslip_ids and payslip_ids.ids:
            #         res['payroll_no'] = payslip_ids[0].number
            commission = bonus = allowance = MTD = CP38 = benefit_in_kind = \
                ytd_gross = incm_tx_born_by_emplr = gratuity = pension = zakat = \
                zakat_tp1 = epf_e = scs_e = eis_e = zakat_mnthly = dir_fees = \
                arr_others = 0.0
            total_income = 0.0
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code in ('BASIC', 'ADDOT', 'OTPH', 'ADJADD'):
                        ytd_gross += line.total
                    elif line.code == 'COMM':
                        commission += line.total
                    elif line.code == 'BONUS':
                        bonus += line.total
                    elif line.code == 'PBONUS':
                        bonus += line.total
                    elif line.code == 'DIR_FEES':
                        dir_fees += line.total
                    elif line.code == 'PCBCURRMONTH':
                        MTD += line.total
                    elif line.code == 'PCBCURRMONTHNOR':
                        CP38 += line.total
                    elif line.code == 'BIK':
                        benefit_in_kind += line.total
                    elif line.code == 'NET-BEFOREMTD':
                        incm_tx_born_by_emplr += line.total
                    elif line.code == 'GRATUITY':
                        gratuity += line.total
                    elif line.code == 'ZAKAT':
                        zakat += line.total
                    elif line.code == 'ZAKAT_TP1':
                        zakat_tp1 += line.total
                    elif line.code == 'ZKT_CURRENT':
                        zakat_mnthly += line.total
                    elif line.code == 'ARR_OTHRS':
                        arr_others += line.total

                    if line.code in ('ALW', 'NONTAXALW'):
                        allowance += line.total
                    elif line.category_id.code == 'ALW':
                        pension += line.total
                    elif line.category_id.code == 'DEPFE':
                        epf_e += line.total
                    # elif line.category_id.code == 'EPF_E':
                    #     epf_e += line.total
                    elif line.category_id.code == 'SCS_E':
                        scs_e += line.total
                    elif line.category_id.code == 'EIS_E':
                        eis_e += line.total
            res['tot_fees'] = commission + bonus + dir_fees
            res['total_income'] = commission + bonus + dir_fees + ytd_gross
            res['allow'] = allowance
            res['MTD'] = MTD
            res['CP38'] = MTD
            res['benefit_in_kind'] = benefit_in_kind
            res['ytd_gross'] = ytd_gross
            res['incm_tx_born_by_emplr'] = incm_tx_born_by_emplr
            res['gratuity'] = gratuity
            res['pension'] = pension
            res['zakat'] = zakat
            res['zakat_tp1'] = zakat_tp1
            res['epf_e'] = epf_e
            res['eis_e'] = eis_e
            res['scs_e'] = scs_e
            res['zakat_mnthly'] = zakat_mnthly
            res['arr_others'] = arr_others
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
            'get_data': report_lines
        }
        return docargs
