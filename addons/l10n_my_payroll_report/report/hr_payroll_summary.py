# See LICENSE file for full copyright and licensing details

from odoo import models, api


class HrPayrollSummary(models.AbstractModel):

    _name = 'report.l10n_my_payroll_report.ppt_hr_payroll_summary_receipt'
    _description = "Payroll Summary Receipt"

    def get_groupname(self, datas):
        user = self.env.user
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        month = date_from.strftime('%m')
        year = date_from.strftime('%Y')
        lst = []
        res = {
               'period': month,
               'year': year,
               'start_date': date_from,
               'end_date': date_to,
               'user': user.partner_id.company_id.name,
            }
        lst.append(res)
        return lst

    def get_name(self, datas):
        result = {}
        total = {}
        emp_ids = datas.get('employee_ids')
        date_from = datas.get('date_from') or False
        date_to = datas.get('date_to') or False
        employee_ids = self.env['hr.employee'].search([('id', 'in', emp_ids)])
        final_group_total = []
        for employee in employee_ids:
            payslip_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', employee.id),
                 ('date_from', '>=', date_from),
                 ('date_from', '<=', date_to),
                 ('state', 'in', ['draft', 'done', 'verify'])])
            net = twage = exa = exd = gross = cpf = pf = overtime = backpay = oth_alw = epfy = scsy = eisy = hrdf = comm = exp = eise = pcb = zkt = 0.0
            if not payslip_ids:
                continue
            for payslip in payslip_ids:
                for rule in payslip.line_ids:
                    if rule.code == 'BASIC':
                        twage += rule.total
                    elif rule.code == 'NET':
                        net += rule.total
                    elif rule.code == 'BONUS':
                        exa += rule.total
                    elif rule.code == 'COMM':
                        comm += rule.total
                    elif rule.category_id.code == 'DED':
                        exd += rule.total
                    elif rule.code == 'GROSS':
                        gross += rule.total
                    elif rule.code == 'DEPFE':
                        cpf += rule.total
                    elif rule.code == 'SCSE':
                        pf += rule.total
                    elif rule.code in ['ADDOT', 'OTPH']:
                        overtime += rule.total
                    elif rule.code == 'BACKPAY':
                        backpay += rule.total
                    elif rule.category_id.code == 'ALW':
                        oth_alw += rule.total
                    elif rule.code == 'EPF_Y_NORMAL':
                        epfy += rule.total
                    elif rule.code == 'SCSY':
                        scsy += rule.total
                    elif rule.code == 'EISY':
                        eisy += rule.total
                    elif rule.code == 'HRDF':
                        hrdf += rule.total
                    elif rule.code == 'EXP':
                        exp += rule.total
                    elif rule.code == 'EISE':
                        eise += rule.total
                    elif rule.code == 'PCBCURRMONTH':
                        pcb += rule.total
                    elif rule.code == ' ZAKAT':
                        zkt += rule.total
                    total_sum = round(twage + epfy + scsy + eisy + hrdf + exa + comm + exp + oth_alw + overtime, 2)
            payslip_result = {
                  'ename': payslip.employee_id.name or '',
                  'eid': payslip.employee_id and payslip.employee_id.user_id and payslip.employee_id.user_id.login or '',
                  # 'twage': payslip.employee_id.contract_id.wage or 0.0,
                  'twage': twage or 0.0,
                  'net': net or 0.0,
                  # 'lvd': lvd or 0.0,
                  'exa': exa or 0.0,
                  'exd': exd or 0.0,
                  'gross': gross or 0.0,
                  'cpf': cpf or 0.0,
                  'pf': pf or 0.0,
                  'overtime': overtime or 0.0,
                  'backpay': backpay or 0.0,
                  'oth_alw': oth_alw or 0.0,
                  'epfy': epfy or 0.0,
                  'scsy': scsy or 0.0,
                  'eisy': eisy or 0.0,
                  'hrdf': hrdf or 0.0,
                  'comm': comm or 0.0,
                  'exp': exp or 0.0,
                  'eise': eise or 0.0,
                  'pcb': pcb or 0.0,
                  'zkt': pcb or 0.0,
                  'total_pay': total_sum or 0.0
                  }
            if payslip.employee_id.department_id:
                if payslip.employee_id.department_id.id in result:
                    result.get(payslip.employee_id.department_id.id
                               ).append(payslip_result)
                else:
                    department = payslip.employee_id.department_id.id
                    result.update({department: [payslip_result]})
            else:
                if 'Undefine' in result:
                    result.get('Undefine').append(payslip_result)
                else:
                    result.update({'Undefine': [payslip_result]})
        finaltwage = finalnet = finallvd = finalexa = finalexd = 0
        finalgross = finalcpf = finalpf = finalovertime = finalbackpay = \
            finaloth_alw = finalepfy = finalscsy = finalhrdf = finalcomm = finalexp = finaleisy = finaleise = finalpcb = finalzkt = 0
        final_result = {}
        for key, val in result.items():
            if key == 'Undefine':
                category_name = 'Undefine'
            else:
                category_name = self.env['hr.department'].browse(key).name
            total = {'name': category_name, 'twage': 0.0, 'net': 0.0,
                     'lvd': 0.0, 'exa': 0.0, 'exd': 0.0, 'gross': 0.0,
                     'cpf': 0.0, 'pf': 0.0, 'overtime': 0.0, 'backpay': 0.0,
                     'oth_alw': 0.0, 'epfy': 0.0, 'scsy': 0.0, 'hrdf': 0.0,
                     'comm': 0.0, 'exp': 0.0, 'eisy': 0.0, 'eise': 0.0,
                     'pcb': 0.0, 'zkt': 0.0}
            for line in val:
                for field in line:
                    if field in total:
                        total.update({field: total.get(field) + line.get(field)})
            final_result[key] = {'lines': val, 'total': total}
            finaltwage += total['twage']
            finalnet += total['net']
            finallvd += total['lvd']
            finalexa += total['exa']
            finalexd += total['exd']
            finalgross += total['gross']
            finalcpf += total['cpf']
            finalpf += total['pf']
            finalovertime += total['overtime']
            finalbackpay += total['backpay']
            finaloth_alw += total['oth_alw']
            finalepfy += total['epfy']
            finalscsy += total['scsy']
            finalhrdf += total['hrdf']
            finalcomm += total['comm']
            finalexp += total['exp']
            finaleisy += total['eisy']
            finaleise += total['eise']
            finalpcb += total['pcb']
            finalzkt += total['zkt']
        final_total = {
                       'twage': finaltwage,
                       'net': finalnet,
                       'lvd': finallvd,
                       'exa': finalexa,
                       'exd': finalexd,
                       'gross': finalgross,
                       'cpf': finalcpf,
                       'pf': finalpf,
                       'overtime': finalovertime,
                       'backpay': finalbackpay,
                       'oth_alw': finaloth_alw,
                       'epfy': finalepfy,
                       'scsy': finalscsy,
                       'hrdf': finalhrdf,
                       'comm': finalcomm,
                       'exp': finalexp,
                       'eisy': finaleisy,
                       'eise': finaleise,
                       'pcb': finalpcb,
                       'zkt': finalzkt,
                }
        final_group_total.append(final_total)
        return final_result.values()

    @api.multi
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])[0]
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'docs': docs,
                   'data': data,
                   'get_name': self.get_name(datas),
                   'get_groupname': self.get_groupname(datas),
                   }
        return docargs
