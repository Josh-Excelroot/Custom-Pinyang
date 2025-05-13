from odoo import fields, models
from odoo.exceptions import UserError
import calendar
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
class HrPayslipAction(models.Model):
    _inherit = 'hr.payslip'


    def last_business_day_in_month(self,year, month):
        return max(calendar.monthcalendar(year, month)[-1][:5])


    def get_current_month(self):
        today = datetime.today()

        first_day = today.replace(day=1)

        last_day = (today.replace(day=1, month=today.month % 12 + 1, year=today.year + today.month // 12) - timedelta(
            days=1))
        return first_day,last_day

    def get_last_month(self):
        today = datetime.today()
        first_day_previous_month = today - relativedelta(months=1, day=1)
        last_day_previous_month = today.replace(day=1) - timedelta(days=1)

        return first_day_previous_month,last_day_previous_month

    def create_payslips(self,employee,months):
        for rec in employee:
            contract = self.env['hr.contract'].search([("employee_id",'=',rec.id),('state','=','open')],limit=1)
            self.env['hr.payslip'].create({
                "employee_id": rec.id,
                "date_from": months[0],
                "date_to": months[1],
                "name": "Salary Slip of" + " " + rec.name + " for " + str(months[0].strftime("%B")) + "-" + str(
                    months[0].year),
                "contract_id":contract.id if contract else False
            })

    def  main_fun(self):
        frequency_payslip = self.env['ir.config_parameter'].get_param('l10n_my_payroll.frequency_payslip')
        employee = self.env['hr.employee'].search([])
        if frequency_payslip == "last_working_day":
            last_working_daye = self.last_business_day_in_month(datetime.now().year, datetime.now().month)
            if datetime.now().day == last_working_daye:
                month = self.get_current_month()
                self.create_payslips(employee,month)

        elif frequency_payslip == "last_month_day":
            today = datetime.today()
            last_day = (today.replace(day=1, month=today.month % 12 + 1,
                                      year=today.year + today.month // 12) - timedelta(
                days=1))
            if datetime.now().day == last_day.day:
                month = self.get_current_month()
                self.create_payslips(employee, month)
        elif frequency_payslip == "next_1st_day":

            today = datetime.today()
            first_day = today.replace(day=1)
            if datetime.now().day == first_day.day:
                month = self.get_last_month()
                self.create_payslips(employee, month)



        elif frequency_payslip == "next_scnd_day":
            today = datetime.today()
            second_day = today.replace(day=2)
            if datetime.now().day == second_day.day:
                month = self.get_last_month()
                self.create_payslips(employee, month)


        elif frequency_payslip == "thrd_day_nxt_mnth":
            today = datetime.today()
            third_day = today.replace(day=3)
            if datetime.now().day == third_day.day:
                month = self.get_last_month()
                self.create_payslips(employee, month)

        elif frequency_payslip == "forth_day_nxt_mnth":
            today = datetime.today()
            fourth_day = today.replace(day=4)
            if datetime.now().day == fourth_day.day:
                month = self.get_last_month()
                self.create_payslips(employee, month)

        elif frequency_payslip == "fifth_next_month":
            today = datetime.today()
            fifth_day = today.replace(day=5)
            if datetime.now().day == fifth_day.day:
                month = self.get_last_month()
                self.create_payslips(employee, month)

        elif frequency_payslip == "specific":
            today = datetime.today()


            specific_day = self.env['ir.config_parameter'].get_param('l10n_my_payroll.specific_day')
            days = []
            for i in range(1,6):
                day = today.replace(day=i)
                days.append(str(day.day))
            if specific_day in days:
                month = self.get_last_month()
                if specific_day == datetime.now().day:
                    self.create_payslips(employee, month)

            else:
                last_day_of_month = (today.replace(day=1, month=today.month % 12 + 1,
                                                   year=today.year + today.month // 12) - timedelta(days=1)).day
                dates_25_to_last = [today.replace(day=i) for i in range(25, last_day_of_month + 1)]
                days = []
                for i in dates_25_to_last:
                    days.append(str(i.day))
                if specific_day in days:

                    month = self.get_current_month()
                    if specific_day == datetime.now().day:
                        self.create_payslips(employee, month)
