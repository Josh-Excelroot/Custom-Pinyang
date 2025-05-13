import odoo.http as http
from odoo.http import request
from odoo import SUPERUSER_ID
from datetime import datetime, timedelta, time
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import odoo.http as http
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# class Payroll(http.Controller):
class PayrollPortal(CustomerPortal):
    # _inherit = 'hr.payslip'
    # _inherit = 'hr.payslip.employees'

    # 1 - will be trigger by the menu.xml url to render the page.
    @http.route("/payroll_generate", type="http", auth="public", website=True)
    def payroll_webform(self, **kw):
        return http.request.render(
            "payroll_web.payroll_generate"
        )

    # 2 - will be trigger when user submit the payroll data
    @http.route(['/payroll_generate/create'], type='http', auth="public", website=True)
    def payroll_generate(self, **post):
        if post.get("debug"):
            return request.render("payroll_web.payroll_thank_you")
        if post:
            # state = "rfr"
            # partner_id = int(post["partner_id"]) if "partner_id" in post else False
            # Bilal 06/10/2022 ******fsfsf
            salary = post["salary"]
            bonus = post["bonus"]
            marital = post["marital"]
            employee_epf_rate = post["employee_epf_rate"]
            employer_epf_rate = post["employer_epf_rate"]
            tax_resident = post["tax_resident"]
            socso_category = post["socso_category"]
            pcb_mtd = post["pcb_mtd"]
            eis_contribution = post["eis_contribution"]
            # allowable_deduction = post["allowable_deduction"]
            zakat_fund = post["zakat_fund"]
            emp_add_rate = "emp_add_rate"
            empr_add_rate = "empr_add_rate"

            vals = {
                "salary": salary,
                "bonus": bonus,
                "marital": marital,
                "employee_epf_rate": employee_epf_rate,
                "employer_epf_rate": employer_epf_rate,
                "tax_resident": tax_resident,
                "socso_category": socso_category,
                "pcb_mtd": pcb_mtd,
                "eis_contribution": eis_contribution,
                # "allowable_deduction": allowable_deduction,
                "zakat_fund": zakat_fund,
                # "emp_add_rate": emp_add_rate,

            }

            # print(vals)
            # payroll = request.env["res.partner"].sudo().update(vals)
            # if employee_epf_rate == 'c' or == 'd':

            employee_id_epf = request.env['hr.employee'].sudo().search(
                [('work_email', '=', 'excelroot.dev@gmail.com')])
            # print(employee_id)
            if employee_id_epf:
                employee_data = {
                    "residence_status": tax_resident,
                    "marital": marital,
                    "socso_category": socso_category,
                }
                print(employee_data)

                if salary > "0" and employee_epf_rate == "a":
                    employee_data = {
                        "emp_epf_rate_less_60": "a",
                        "emp_add_rate": "0",
                    }

                elif salary > "0" and employee_epf_rate == "b":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "0",
                    }

                elif salary > "0" and employee_epf_rate == "c":
                    employee_data = {
                        "emp_epf_rate_less_60": "a",
                        "emp_add_rate": "1",
                    }

                elif salary > "0" and employee_epf_rate == "d":
                    employee_data = {
                        "emp_epf_rate_less_60": "a",
                        "emp_add_rate": "2",
                    }

                elif salary > "0" and employee_epf_rate == "e":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "1",
                    }

                elif salary > "0" and employee_epf_rate == "f":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "2",
                    }

                elif salary > "0" and employee_epf_rate == "g":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "3",
                    }

                elif salary > "0" and employee_epf_rate == "h":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "4",
                    }
                elif salary > "0" and employee_epf_rate == "i":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "5",
                    }

                elif salary > "0" and employee_epf_rate == "j":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "6",
                    }
                elif salary > "0" and employee_epf_rate == "k":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "7",
                    }
                elif salary > "0" and employee_epf_rate == "l":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "8",
                    }
                elif salary > "0" and employee_epf_rate == "m":
                    employee_data = {
                        "emp_epf_rate_less_60": "b",
                        "emp_add_rate": "9",
                    }

                employee_id_epf.update(employee_data)

            employer_id_epf = request.env['hr.employee'].sudo().search(
                [('work_email', '=', 'excelroot.dev@gmail.com')])

            if employer_id_epf:
                if salary >= '4001' and employer_epf_rate == "a":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "0",
                    }

                elif salary >= '4001' and employer_epf_rate == "b":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "2",
                    }
                elif salary >= '4001' and employer_epf_rate == "c":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "3",
                    }
                elif salary >= '4001' and employer_epf_rate == "d":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "4",
                    }
                elif salary >= '4001' and employer_epf_rate == "e":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "5",
                    }
                elif salary >= '4001' and employer_epf_rate == "f":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "6",
                    }
                elif salary >= '4001' and employer_epf_rate == "g":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "7",
                    }
                elif salary >= '4001' and employer_epf_rate == "h":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "8",
                    }

                if salary <= '4000' and employer_epf_rate == "a":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "0",
                    }

                elif salary <= '4000' and employer_epf_rate == "b":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "1",
                    }
                elif salary <= '4000' and employer_epf_rate == "c":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "2",
                    }
                elif salary <= '4000' and employer_epf_rate == "d":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "3",
                    }
                elif salary <= '4000' and employer_epf_rate == "e":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "4",
                    }
                elif salary <= '4000' and employer_epf_rate == "f":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "5",
                    }
                elif salary <= '4000' and employer_epf_rate == "g":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "6",
                    }
                elif salary <= '4000' and employer_epf_rate == "h":
                    employer_data = {
                        "empr_epf_rate_cond_a": "a",
                        "empr_add_rate": "7",
                    }

                employer_id_epf.update(employer_data)

            # contract_id = request.env['hr.contract'].search([('name', '=', '003/2022')])
            contract_id = request.env['hr.contract'].search([('state', '=', 'open')])
            # contract_id_1 = contract_id[0].get('id')
            # contract_id_2 = contract_id[1].get('id')
            # contract_id = sock.execute(dbname, uid, pwd, 'res.country.state', 'search_read',
            #                       [('country_id', '=', country_id), ])
            print("contract....", contract_id)
            # print("contract  1....", contract_id_1)
            # print("contract  2....", contract_id_2)
            # contract = contract_id[0].get('id')
            # print(contract_id)
            # print(contract)
            contract_data = {
                "wage": salary,
                # "total_ytd_pcd_ded": allowable_deduction,
            }
            contract_id.update(contract_data)

            # print('part B')
            # payslip_id_bonus = request.env['hr.payslip'].search([('number', '=', 'SLIP/01/22/0001')])
            payslip_id_bonus = request.env['hr.payslip.input'].search([('code', '=', 'PBONUS')])
            # print(payslip_id_bonus)
            bonus_data = {
                "amount": bonus,
            }
            payslip_id_bonus.update(bonus_data)

            # print('part C')
            payslip_id_zakat = request.env['hr.payslip.input'].search([('code', '=', 'ZAKAT')])
            # print(payslip_id_bonus)
            zakat_data = {
                "amount": zakat_fund,
            }
            payslip_id_zakat.update(zakat_data)
            # data = []
            # if payslip_id_bonus:
            #     for input_line_id in payslip_id_bonus.input_line_ids:
                    # bonuses = {
                    #     "name": input_line_id.name,
                    #     "code": input_line_id.code,
                    #     "amount": input_line_id.amount,
                    # }
                    # print("bonuses>>>>", bonuses)
                    #
                    # data = []
                    # if input_line_id.code == "PBONUS":
                    #     # data.append(bonuses)
                    #     # print("bonus_data>>>>>", data)
                    #     final_bonus_list = {
                    #             "name": "Performance Bonus",
                    #             "code": "PBONUS",
                    #             "amount": bonus,
                    #         }
                    #     data.append(final_bonus_list)
                    #     print(">>>>data = ", data)
                    #
                    #     payslip_id_bonus.update(data)
                    #     # payslip_id_bonus.update(data[0])


        # bonus_dict = {}
        # for d in data:
        #     if d.get('name') not in bonus_dict:
        #         bonus_dict.update({d.get('name'): []})
        #         print("bonus>>>", bonus_dict)
                # payslip_id_bonus.update(bonuses.get("amount"))
                # payslips_id.update({"amount": []})
                # print("data 2>>>>", payslips_id)

            #         print(' >>>>>>name=', input_line_id.name, ' , code=', input_line_id.code, ' , total=',
            #               input_line_id.amount)
            #         bonuses = {
            #             "input_line_ids": bonus,
            #         }
            #
            #         payslips_id.update(bonuses)
            #         print(bonuses)
        # print("Part D")
        payslip_id = request.env['hr.payslip'].search([('number', '=', 'SLIP/01/22/0001')])
        # print(payslip_id)
        if payslip_id:
            payslip_id.compute_sheet()
            for line_id in payslip_id.line_ids:
                print(' >>>>>>name=', line_id.name, ' , code=', line_id.code, ' , total=', line_id.total)
                vals = {
                    "payslip_id": payslip_id,
                }
                # print(vals)
            # two_decimal_vals = number_format(vals, 2)
        return request.render("payroll_web.new_line_id_edit", vals)
        # return request.render("l10n_my_payroll.report_my_payslip")
        # return request.render("l10n_my_payroll.report_hr_payslip_detail")

# class AutoComputeSheet(models.Model):
#     _inherit = 'hr.payslip.employees'

#     def auto_compute_sheet(self):

# wage =
#
# if fiscal_years[0].date_to < current_date:
#     # Add 12 months to the last fiscal year
#     new_date_from = fiscal_years[0].date_from + relativedelta(months=12)
#     new_date_to = fiscal_years[0].date_to + relativedelta(months=12)
#     vals = {
#         'name': 'Fiscal Year ' + str(new_date_to.year),
#         'date_from': new_date_from,
#         'date_to': new_date_to,
#     }
