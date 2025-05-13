# See LICENSE file for full copyright and licensing details
import logging

import odoo.exceptions
import re
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from datetime import date
from bs4 import BeautifulSoup
import requests
from selenium import webdriver #pip install selenium
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager #pip install webdriver_manager
from selenium_stealth import stealth #pip install selenium_stealth

from odoo.addons.resource.models.resource import Intervals

from pytz import timezone, utc
from datetime import datetime, time


class HrHolidayPublic(models.Model):
    '''
        This class stores a list of public holidays
    '''

    _name = 'hr.holiday.public'
    _description = 'Public holidays'
    _rec_name = 'hr_year_id'

# ============================================
#    Public holidays: constrains
# ============================================

    # @api.constrains('holiday_line_ids')
    # def _check_holiday_line_year(self):
    #     '''
    #     The method used to Validate duplicate public holidays.
    #     @param self : Object Pointer
    #     @return : True or False
    #     ------------------------------------------------------
    #     '''
    #     for holiday in self:
    #         for line in holiday.holiday_line_ids:
    #             if str(holiday.hr_year_id.name) != str(line.holiday_date.year):
    #                 raise ValidationError(_('You can not create \
    #                         holidays for different year!'))
    #             holiday_ids = line.search([('holiday_date', '=',
    #                                         line.holiday_date)])
    #             if len(holiday_ids) > 1:
    #                 raise ValidationError(_('You can not have same '
    #                                         'holiday date!'))

    @api.constrains('name')
    def _check_public_holiday(self):
        for rec in self:
            pub_holiday_ids = rec.search(
                [('hr_year_id.name', '=', rec.hr_year_id.name)])
            if pub_holiday_ids and len(pub_holiday_ids) > 1:
                raise ValidationError(_('You can not have multiple public \
                            holiday for same year!'))

    # name = fields.Integer('Holiday', required=True,
    #                       help='Name of holiday list')
    hr_year_id = fields.Many2one('hr.year', 'HR Year')

    holiday_line_ids = fields.One2many('hr.holiday.lines', 'holiday_id',
                                   'Holidays', copy=True)
    email_body = fields.Text('Email Body',
                             default='Dear Manager,\n\nKindly find attached '
                             'pdf document containing Public Holiday '
                             'List.\n\nThanks,')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('validated', 'Validated'),
                              ('refused', 'Refused'),
                              ('cancelled', 'Cancelled'),
                              ], 'State', index=True, readonly=True,
                             default='draft')
    country_id = fields.Many2one('res.country', 'Country')
    company_ids = fields.Many2many(
        'res.company', string="Companies", default=lambda self: self.env.user.company_id)
    #### This field shows which state the company is in / Lo Gee Yen / 12/10/2023
    company_state = fields.Text(string="States")
    #### This field shows which state the company is in / Lo Gee Yen / 12/10/2023

# ============================================
#    Public holidays: Button Methods
# ============================================
    @api.multi
    def set_state_draft(self):
        '''Sets state to draft'''
        self.write({'state': 'draft'})
        return True

    @api.multi
    def set_state_cancel(self):
        '''Sets state to cancelled'''
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def set_state_refuse(self):
        '''Sets state to refused'''
        self.write({'state': 'refused'})
        return True

    @api.multi
    def set_state_confirm(self):
        '''Sets state to confirmed'''
        if not self.holiday_line_ids:
            raise ValidationError(_('Please add holidays.'))
        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def set_state_validate(self):
        '''Sets state to validated'''
        if not self.holiday_line_ids:
            raise ValidationError(_('Please add holidays.'))
        for holiday in self:
            holiday.write({'state': 'validated'})
        return True

    def create_report(self, report_name=False):
        '''
        Creates report from report_name that contains records of res_ids
        and saves in report directory of module as
        file_name.
        @param res_ids : List of record ids
        @param report_name : Report name defined in .py file of report
        @param file_name : Name of temporary file to store data
        @return: On success returns tuple (True,filename)
                 otherwise tuple (False,execeotion)
        '''
        if not report_name or not self._ids:
            return (False, Exception('Report name and Resources \
            ids are required !'))
        try:
            domain = [('report_name', '=', report_name)]
            report = self.env['ir.actions.report'
                              ].search(domain, limit=1)
            result, rpt_format = report.render(self._ids, {})
        except Exception as e:
            return (False, str(e))
        return (True, result)

# ============================================
#    Public holidays: ORM Methods
# ============================================

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You cannot delete a public'
                                        ' holiday which is not in draft state !'))
        return super(HrHolidayPublic, self).unlink()

#### Fill Holiday System / Lo Gee Yen / 12/10/2023
    #### Changes the state field and the country field when the company_ids field is interacted / Lo Gee Yen / 12/10/2023
    @api.onchange('company_ids')
    def set_selected_country_state(self):
        for rec in self:
            for each_company_ids in rec.company_ids:
                if rec.company_ids:
                    rec.company_state = (str(each_company_ids.state_id.name))
                    rec.country_id = each_company_ids.country_id
    #### Changes the state field and the country field when the company_ids field is interacted / Lo Gee Yen / 12/10/2023

    #### Convert string month to numerical so that it can be converted into DateTime Object / Lo Gee Yen / 12/10/2023
    def convert_to_numeric_month(self, x):
        months = {
            'jan': 1,
            'feb': 2,
            'mar': 3,
            'apr': 4,
            'may': 5,
            'jun': 6,
            'jul': 7,
            'aug': 8,
            'sep': 9,
            'oct': 10,
            'nov': 11,
            'dec': 12
        }
        formatted = x.strip()[:3].lower()
        try:
            numeric_month = months[formatted]

            return numeric_month
        except:
            raise ValueError('Not a month')
    #### Convert string month to numerical so that it can be converted into DateTime Object / Lo Gee Yen / 12/10/2023

    #### This function uses Selenium to access the public holiday website
    def use_selenium(self, link):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("start-maximized")
            options.add_argument("--headless")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            s = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=s, options=options)

            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            driver.get(link)
            html_string = BeautifulSoup(driver.page_source, 'html.parser')
            return html_string
        except:
            print('')
    #### This function uses Selenium to access the public holiday website

    #### This function uses Request.get to access the public holiday website
    def use_request(self, link):
        headers = {
            # 'User-Agent': ''
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0) Gecko/20100101 Firefox/33.0'
        }

        page = requests.get(link, headers=headers)
        html_string = BeautifulSoup(page.content, 'html.parser')
        return html_string
    #### This function uses Request.get to access the public holiday website

    #### This function scrap data from a holiday website & format the retrieved data / Lo Gee Yen / 12/10/2023
    def action_fill_holidays(self):
        _logger = logging.getLogger(__name__)
        if self.hr_year_id.name != False:
            blocked = False  # Assume not blocked by cloudflare
            loop_index = 0
            input_year = str(self.hr_year_id.date_start.year)
            link = "https://publicholidays.com.my/" + input_year.strip() + "-dates/"
            html_string = self.use_request(link)  # Get Html from page
            for title in html_string.find_all('title'):
                if 'Attention Required!' in title.get_text():
                    print('Blocked on First try')
                    _logger.info('Blocked on First try')
                    blocked = True  # blocked by cloudflare
                else:
                    print('Request.get Successful')
                    _logger.info('Request.get Successful')

            # keep looping until can access or tried 3 times
            while blocked is True and loop_index < 3:
                loop_index = loop_index + 1
                # If blocked use Selenium
                print('Using Selenium')
                _logger.info('Using Selenium')
                self.use_selenium(link)  # After using selenium, call request again
                html_string = self.use_request(link)  # try again
                for title in html_string.find_all('title'):
                    print(title.get_text())
                    if 'Attention Required!' not in title.get_text():
                        print('Unblocked')
                        _logger.info('Unblocked')
                        blocked = False

            if blocked is False:
                index = 0
                list_data = []

                mainElement = html_string.find('table', class_='publicholidays phgtable')

                # store all data in a list
                for tbody in mainElement.find_all('tbody'):
                    rows = tbody.find_all('tr', {'class': ['even', 'odd']})
                    for row in rows:
                        each = row.find_all('td')
                        holiday_date = each[0].text
                        day = each[1].text
                        holiday = each[2].text
                        state = ((each[3].text).strip()).replace('\n', '')  # get rid of \n in the string
                        if day.lower() != 'sun':
                            data = [holiday_date, day, holiday, state]

                            #check if the holiday includes the current company state
                            valid = self.check_valid_holiday(state)
                            #check if dates are the same with previous entry. If same then combine them
                            if(index > 0):
                                previous_entry_date = (list_data[index - 1])[0]
                                # print(previous_entry_date + " : "+str(index))
                                if (valid==True):  # check if same state
                                    if(previous_entry_date == holiday_date):
                                        (list_data[index - 1])[2] = (list_data[index - 1])[2] + ", " +holiday
                                        (list_data[index - 1])[3] = (list_data[index - 1])[3] + ", " + state
                                        recorded_state = str((list_data[index - 1])[3]).lower()
                                        if "national" in recorded_state:
                                            (list_data[index - 1])[3] = "National"
                                    else:
                                        list_data.append(data)  # add each data array to the list only if previous date is not the same
                                        recorded_state = str((list_data[index])[3]).lower()
                                        if "national" in recorded_state:
                                            list_data[index][3] = "National"
                                        index = index + 1
                            else:
                                if(valid==True): #check if valid state
                                    list_data.append(data)
                                    recorded_state = str((list_data[index])[3]).lower()
                                    if "national" in recorded_state:
                                        list_data[index][3] = "National"
                                    index = index + 1

                # for entry in list_data:
                #     print(entry)
                self.action_fill_holidays_insert_in(list_data, input_year)
            else:
                raise odoo.exceptions.UserError("Data cannot be grabbed from the public holidays website")
        else:
            raise odoo.exceptions.UserError("Year HR Year cannot be empty")
    #### This function scrap data from a holiday website & format the retrieved data / Lo Gee Yen / 12/10/2023

    #### This function checks whether a holiday is valid for the company's location / Lo Gee Yen / 12/10/2023
    def check_valid_holiday(self, in_state):
        valid = False

        if((in_state.strip()).lower() == "national"): #if state only equals to national then every state gets a holiday
            valid = True
        else:
            if "except" in in_state:
                all_states = re.split(' except|except | except |, |,| & | &|& ', in_state)#get all the states from the string
                found_in_except = False
                for each in all_states:
                    if ((each.strip()).lower() == (self.company_state.strip()).lower() or (each.strip()).lower() == ((self.company_state.strip()).lower()).replace(" ","")):
                        found_in_except = True
                        break

                if(found_in_except==True):#if found in except, means that the holiday is not valid for this state
                    valid = False
                else:
                    valid = True
            else:
                all_states = re.split(', |,| & | &|& ', in_state)#get all the states from the string
                for each in all_states:
                    if ((each.strip()).lower() == (self.company_state.strip()).lower() or (each.strip()).lower() == ((self.company_state.strip()).lower()).replace(" ","")):
                        valid = True
                        break

        return valid
    #### This function checks whether a holiday is valid for the company's location / Lo Gee Yen / 12/10/2023

    #### This function inputs the provided values into the holiday lines / Lo Gee Yen / 12/10/2023
    def action_fill_holidays_insert_in(self, list_data, input_year):
        for entry in list_data:
            # data = [holiday_date, day, holiday, state]
            holiday_day = entry[1]
            holiday_name = entry[2]
            holiday_state = entry[3]
            # format the date so that a date Object can be created
            holiday_date_splitted = entry[0].split(" ")
            numeric_month = self.convert_to_numeric_month(holiday_date_splitted[1])
            numeric_date = int(holiday_date_splitted[0])

            if(holiday_state.strip()=="National"):
                state_option = "national"
            else:
                state_option = ""

            self.holiday_line_ids = [(0, 0, {
                'name': holiday_name,
                'holiday_date': date(int(input_year), numeric_month, numeric_date),
                'day': holiday_day,
                'holiday_type': state_option,
            })]
    #### This function inputs the provided values into the holiday lines / Lo Gee Yen / 12/10/2023

#### Fill Holiday System / Lo Gee Yen / 12/10/2023

class HrHolidayLines(models.Model):
    '''
       This model stores holiday lines
    '''

    _name = 'hr.holiday.lines'
    _description = 'Holiday Lines'
    _order = 'holiday_date'

    holiday_date = fields.Date('Date', help='Holiday date', required=True)
    holiday_type = fields.Selection(
        [('national', 'National'), ('state', 'State')], default='national', string="Holiday Type")
    state_ids = fields.Many2many('res.country.state', string="States")
    name = fields.Char('Reason', size=128, help='Reason for holiday')
    day = fields.Char('Day', size=16, help='Day')
    holiday_id = fields.Many2one('hr.holiday.public', 'Holiday List',
                                 help='Holiday list', ondelete="cascade")
    meeting_id = fields.Many2one('calendar.event', string='Meeting')
    rate = fields.Float(string="OT Rate")

    @api.multi
    @api.onchange('holiday_date')
    def onchange_holiday_date(self):
        '''
            This methods returns name of day of holiday_date
        '''
        for holiday_rec in self:
            holiday_dt = holiday_rec.holiday_date or False
            if holiday_dt:
                daylist = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                           'Friday', 'Saturday', 'Sunday']
                day = holiday_dt.weekday()
                self.day = daylist[day]

    @api.multi
    def _prepare_holidays_meeting_values(self):
        self.ensure_one()
        categ_id = self.env.ref('my_holiday.event_type_holiday', False)
        meeting_values = {
            'name': self.name,
            'description': ', '.join(self.state_ids.mapped('name')),
            'categ_ids': [(6, 0, categ_id.ids if categ_id else [])],
            'start': self.holiday_date,
            'stop': self.holiday_date,
            'allday': True,
            'partner_ids': False,
            'user_id': SUPERUSER_ID,
            'state': 'open',
            'privacy': 'confidential',
            'show_as': 'busy',
        }
        return meeting_values

    @api.constrains('holiday_date', 'name', 'state_ids')
    def _update_calendar_event(self):
        print('>>>>>>>>>>>  _update_calendar_event')
        for rec in self:
            if rec.meeting_id:
                rec.meeting_id.write(rec._prepare_holidays_meeting_values())
                rec._prepare_public_holiday()


    @api.multi
    def _prepare_public_holiday(self):
        print('>>>>>>>>>>>  _prepare_public_holiday')
        self.ensure_one()
        ph = self.env['hr.leave.type'].search([
            ('name', '=', 'Public Holiday'),
        ],limit=1)
        if ph:
            date_from = datetime.combine(self.holiday_date, datetime.min.time())
            date_to = datetime.combine(self.holiday_date, datetime.max.time())
            ph_vals = {'holiday_status_id': ph.id,
                            'request_date_from': self.holiday_date,
                            'request_date_to': self.holiday_date,
                            'date_from': date_from,
                            'date_to': date_to,
                            'number_of_days_display': 1,
                            'name': self.name,
                            'holiday_type': 'company',
                            'mode_company_id': self.env.user.company_id.id,
                            'state': 'validate',
                            }
            print('>>>>>>>>>>>  _prepare_public_holiday ph_val=', ph_vals)
            self.env['hr.leave'].create(ph_vals)

        #categ_id = self.env.ref('my_holiday.event_type_holiday', False)
        # meeting_values = {
        #     'name': self.name,
        #     'description': ', '.join(self.state_ids.mapped('name')),
        #     'categ_ids': [(6, 0, categ_id.ids if categ_id else [])],
        #     'start': self.holiday_date,
        #     'stop': self.holiday_date,
        #     'allday': True,
        #     'partner_ids': False,
        #     'user_id': SUPERUSER_ID,
        #     'state': 'open',
        #     'privacy': 'confidential',
        #     'show_as': 'busy',
        # }


    @api.model
    def create(self, values):
        print('>>>>>>>>>>>  hr.holiday.lines Create=')
        res = super().create(values)
        res.meeting_id = self.env['calendar.event'].create(
            res._prepare_holidays_meeting_values())
        res._prepare_public_holiday()
        return res

    @api.multi
    def unlink(self):
        self.mapped('meeting_id').unlink()
        return super().unlink()


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _leave_intervals(self, start_dt, end_dt, resource=None, domain=None):
        result = super(ResourceCalendar, self)._leave_intervals(
            start_dt=start_dt, end_dt=end_dt, resource=resource, domain=domain)
        tz = timezone((resource or self).tz)
        public_holiday_res = self.fetch_public_holidays(start_dt, end_dt, tz)
        result = result | public_holiday_res
        return result

    def fetch_public_holidays(self, start_dt, end_dt, tz):
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        public_domain = [('holiday_date', '>=', start_dt),
                         ('holiday_date', '<=', end_dt),
                         ('holiday_id.state', '=', 'validated')
                         ]
        for leave in self.env['hr.holiday.lines'].search(public_domain):
            dt0 = datetime.combine(
                leave.holiday_date, time.min).replace(tzinfo=tz)
            dt1 = datetime.combine(
                leave.holiday_date, time.max).replace(tzinfo=tz)
            result.append((dt0, dt1, self.env['resource.calendar.leaves']))
        return Intervals(result)


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"
    _description = 'Resource Mixin'

    def list_leaves(self, from_datetime, to_datetime, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a list of tuples (day, hours, resource.calendar.leaves)
            for each leave in the calendar.
        """
        context = dict(self._context) or {}
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        attendances = calendar._attendance_intervals(
            from_datetime, to_datetime, resource)
        leaves = calendar._leave_intervals(
            from_datetime, to_datetime, resource, domain)
        if 'without_public_holiday' in context:
            public_holidays = calendar.fetch_public_holidays(
                from_datetime, to_datetime, timezone((resource or self).tz))
            leaves = (leaves - public_holidays)
        result = []
        for start, stop, leave in (leaves & attendances):
            hours = (stop - start).total_seconds() / 3600
            result.append((start.date(), hours, leave))
        return result