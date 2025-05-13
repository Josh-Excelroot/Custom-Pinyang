# -*- coding: utf-8 -*-
import base64
import numpy
import pytz
from PIL import Image #pip install Pillow
from huggingface_hub import InferenceClient

from odoo.exceptions import ValidationError
import pytesseract #pip install pytesseract
import io
import re # pip install regex
import calendar#pip install calendar
from datetime import datetime #pip install datetime
from pdf2image import convert_from_path, convert_from_bytes #pip install pdf2image
from datetime import date #pip install datetime
# sudo apt-get install tesseract-ocr
# pip3 install pytesseract

from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils, float_round
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class HrExpenseCategory(models.Model):
    _name = "hr.expense.categoty"
    _description = "Hr Expense Category"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name")
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.', context={'user_preference': True})

    _sql_constraints = [('name_uniq', 'unique (company_id, name)',
                         'Name must be unique within an application!')]

class HrExpense(models.Model):
    _inherit = "hr.expense"
    total_amount = fields.Monetary("Total", store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    document = fields.Binary(string='Documents')
    document_filename = fields.Char("File name")
    # modified_lo

    # @api.model
    # def create(self, vals):
    #     res = super(HrExpense, self).create(vals)
    #     if self.document:
    #         byte_document = base64.b64decode(self.document)  # convert document to byte
    #         image_data = base64.b64encode(byte_document).decode('utf-8')
    #         saved_attachment = self.env['ir.attachment'].create({
    #             'name': self.document_filename,
    #             'datas': image_data,
    #             'type': 'binary',
    #             'datas_fname': self.document_filename,
    #             'res_model': 'hr.expense',
    #             'res_id': res.id,
    #         })
    #     return res

    # @api.model
    # def _default_employee_id(self):
    #     print("HERE")
    #     old_function = super(HrExpense, self)._default_employee_id()
    #     expense = self.env['hr.expense.sheet'].browse(self._context.get('sheet_id', []))
    #     print(expense.name)
    #     print(expense.employee_id.name)
    #     return expense.employee_id.id

    employee_id = fields.Many2one('hr.employee', related='sheet_id.employee_id', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=lambda self: self._get_employee_id_domain())

    #this function checks the validity of the OCR dates and return a date object
    def check_date(self, OCR_date):
        # check if date is correct
        if ' ' in OCR_date:# if there is other data besides date such as 11/9/2023 3:00
            split_date_space = OCR_date.split(" ")
            for each in split_date_space:
                if '-' or '/' in each:
                    OCR_date = each

        date_input = date.today()
        if '/' in OCR_date:
            split_date = OCR_date.split("/")
        else:
            split_date = OCR_date.split("-")

        if len(split_date) >= 3:
            try:
                date_input = date(int(split_date[0]), int(split_date[1]), int(split_date[2]))
            except:  # if retrieved date is an incorrect date, the system will just get today's date
                try:
                    date_input = date(int(split_date[2]), int(split_date[1]), int(split_date[0]))
                except:
                    date_input = date.today()
                    print('Invalid date, using today\'s date')
        return date_input

    #This function uses AI to scan the OCR result
    def OCR_AI_Scan(self, OCR_result, hugging_face_ai_api_key):
        error_occurred = False
        client = InferenceClient(
            "mistralai/Mistral-7B-Instruct-v0.2",
            hugging_face_ai_api_key,
        )

        prompt = """You are an ai that helps extract data from an OCRed receipt. The OCRed data will be provided in the Assistant message. The targeted data are 
    1. shop name, 
    2. total amount, 
    3. tax amount, 
    4. date, 
    5. currency type. 
    Double check and make sure that shop name, total amount, tax amount, date and currency type are in the output.
    the output format shown below,
    1. ShopName:
    2. Date:
    3. TaxAmount:
    4. Total:
    5. CurrencyType:
    The end of the Format
    [INST]
    Please give me the shop name, total amount, tax amount, date and currency type. For currency type please provide only the currency code, dont add anymore information. Please only include the symbol for . Double check and make sure that shop name, total amount, tax amount, date and currency type are in the response. Don't include anything else other than the requested data in your response. Make sure you do this. This is very important to my career. Take pride in your work!
    [/INST]
    """+OCR_result
        try:
            res = client.text_generation(prompt, max_new_tokens=95)
            print(res)
            print('AI_OCR___________________')
            return res, error_occurred
        except:
            error_occurred = True
            return '', error_occurred
            # raise ValidationError('Error running the Hugging Face AI, either the API key is invalid or the user has reached the AI call limit')


    #This function takes in the result generated by the AI and extract the relavant data
    def AIDataExtraction(self, res):
        total = ""
        shop = ""
        c_type = ""
        tax = ""
        dateOCR = ""
        lines = res.split('\n')
        for line in lines:
            print(line)
            if 'name:' in line.lower():
                if len(line.split(':')) > 1:
                    shop = line.split(':')[1].strip()
            elif 'date:' in line.lower():
                if len(line.split(':')) > 1:
                    dateOCR = line.split(':')[1].strip()
            elif 'tax' in line.lower():
                if len(line.split(':')) > 1:
                    tax = line.split(':')[1].strip()
            elif 'total' in line.lower():
                if len(line.split(':')) > 1:
                    total = line.split(':')[1].strip()
                    total = total.replace(',', '')
            elif 'type:' in line.lower():
                if len(line.split(':')) > 1:
                    c_type = line.split(':')[1].strip()
        return total, c_type, shop, tax, dateOCR

    def test_respond(self):
        test_response = """1. ShopName: test name
    2. Date: 20/12/2023
    3. TaxAmount: test tax
    4. Total: 0
    5. CurrencyType: rm
    """

        return test_response, False

    # This function OCRs the provided image. After that it extracts and return relevant data
    def get_relevant_data(self, ocr_result, hugging_face_ai_api_key):
        ai_respond, error_occurred = self.OCR_AI_Scan(ocr_result, hugging_face_ai_api_key) #TESTING HERE
        # ai_respond, error_occurred = self.test_respond()
        total, currency_type, shop, tax, date_receipt = self.AIDataExtraction(ai_respond)

        return total, currency_type, shop, tax, date_receipt, error_occurred

    # This function gets the incoming mail server that called the message new function
    def get_incoming_mail_server_item(self, email_to):
        mail_server = self.env['fetchmail.server'].search([('user', '=', email_to)], limit=1)
        return mail_server

    # This function checks what language the document is in
    # if document is chinese, convert only using the Chinese parameters to get better results. Same with the English language
    def check_langauge(self, ocr_result, image):
        if '計' in ocr_result:
            return_ocr_result = pytesseract.image_to_string(image, lang='chi_tra')
        else:
            return_ocr_result = pytesseract.image_to_string(image, lang='eng')

        return return_ocr_result

    ###non OCR email call###
    def create_message_monitor_entry_success(self, sheet_name, has_attachment, selected_company,
                                             each_expense_item_line):
        # Obtain datetime
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_time = datetime.now(malaysia_tz)

        message_monitor = self.env['message.monitor.expense'].create({
            'name': current_time,
            'company_id': selected_company,
            'type': 'hr.expense',
            'sheet_name': sheet_name,
            'object_id': each_expense_item_line.id,
            'has_attachment': has_attachment,
        })

    #This function creates a message monitor entry
    def create_message_monitor_entry(self, sheet_name, has_attachment, selected_company):
        # Obtain datetime
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_time = datetime.now(malaysia_tz)

        message_monitor = self.env['message.monitor.expense'].create({
            'name': current_time,
            'company_id': selected_company,
            'type': 'hr.expense',
            'sheet_name': sheet_name,
            'has_attachment': has_attachment,
        })

    #This function searches for the correct expense sheet. If no expense sheet with the correct parameters were found, create a new one
    def sheet_function(self, date_input, employee_sender):
        # search for the sheet first
        # search for the expense report with the correct date
        expense = self.env['hr.expense.sheet'].search([
            ('start_date', '<=', date_input),
            ('end_date', '>=', date_input),
            ('employee_id', '=', employee_sender.id),
            ('state', '=', 'draft'),
        ])
        # if the sheet hasn't been created yet, create it. time frame is within the month.
        if len(expense) == 0:  # If len(expense) == 0 means that no expense report with the correct criteria have been found
            try:
                calendar.month_name[int(date_input.month)] # check the provider date's validity
                str(date_input.year)
            except Exception as e:
                print('except ', e)
                date_input = datetime.now().date()# if there is an error, set date time as today
                print('date_input ', date_input)

            expense_sheet_name = employee_sender.display_name + " EXPENSE " + calendar.month_name[int(date_input.month)] + " " + str(date_input.year)
            current_month_day_len = int(calendar.monthrange(int(date_input.year), int(date_input.month))[1])  # this field is used to record how many days the current month has

            expense = self.env['hr.expense.sheet'].create({
                'name': expense_sheet_name,
                'employee_id': employee_sender.id,
                'user_id': employee_sender.expense_manager_id.id,
                'company_id': employee_sender.company_id.id,
                'start_date': date(int(date_input.year), int(date_input.month), 1),
                'end_date': date(int(date_input.year), int(date_input.month), current_month_day_len),
            })
        return expense

    def get_expense_type(self, expense_description):
        # expense type
        expense_type_selections = self.env['product.product'].search([('can_be_expensed', '=', True)])
        expense_type = ""

        for each in expense_type_selections:
            if expense_description.strip().lower() in str(each.name).strip().lower():
                expense_type = each.name

        if expense_type == "":  # if an expense type is not found then set it to default
            expense_type = expense_type_selections[0].name  # chose the first one if non match

        expense_type_id = self.env['product.product'].search([('name', '=', expense_type)])
        return expense_type_id

    ###non OCR email call###
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        hugging_face_ai_api_key = self.env['ir.config_parameter'].sudo().get_param('hr_expense.api_key_expense_ocr')
        latest_expense_line = ""#contains the latest record only
        total = ""
        shop = ""
        tax = ""
        date_receipt = ""
        print("expenses incoming email")
        expense_description = msg_dict.get('subject', '')#email title
        email_from = msg_dict.get('from') or ''
        email_to = msg_dict.get('to') or ''
        email_from = email_escape_char(email_split(email_from)[0])
        email_to = email_escape_char(email_split(email_to)[0])
        employee_sender = self.env['hr.employee'].search([('work_email', '=', email_from)])
        mail_server = self.get_incoming_mail_server_item(email_to)

        #get attachment from email
        attachments = msg_dict.get('attachments', [])
        #After getting the attachment data, delete the attachments from the msg_dict so that the system doesn't automatically attach the attachment
        if msg_dict.get('attachments'):
            del msg_dict['attachments']

        ###Non-OCR Version###
        if hugging_face_ai_api_key == False:
            #No API Key then call the non OCR version
            if (employee_sender.display_name == False):  # no employee with the emails was found
                sheet_name = "No employee with the email [" + email_from + "] has been found, expense not created"
                selected_company = mail_server.company_id.id
                self.create_message_monitor_entry(sheet_name, False, selected_company)
            else:
                expense = self.sheet_function(datetime.now().date(), employee_sender)#Only possible to have 1 sheet as no possibility of different date as date is always today, and there is only 1 employee sender
                expense_type_id = self.get_expense_type(expense_description)#only 1 title for each email
                company_id_custom = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
                default_custom_company_currency_id = self.env['res.company'].browse(company_id_custom).currency_id  # use the company's id

                for each_attachment in attachments:
                    for each_expense_item in expense:  # if there is multiple expense report that meets the criteria
                        each_expense_item_line = self.env['hr.expense'].create({
                            'date': date.today(),
                            'name': "Email Title:" + expense_description + ", Attachment: " + each_attachment[0],
                            'employee_id': employee_sender.id,
                            'company_id': employee_sender.company_id.id,
                            'foreigh_currency_id': default_custom_company_currency_id.id,
                            'product_id': expense_type_id[0].id,
                            # [0] ensures that if multiple items of the same name is found, only give the id of the first item found
                            'foregh_unit_price': 0,
                            'unit_amount': 0,
                            'sheet_id': each_expense_item.id,
                            # 'analytic_account_id': 1,
                            'diff_cur_active': False,
                        })
                        each_expense_item_line.foreigh_currency_id = default_custom_company_currency_id.id
                        image_data = base64.b64encode(each_attachment[1]).decode('utf-8')

                        saved_attachment = self.env['ir.attachment'].create({
                            'name': each_attachment[0],
                            'datas': image_data,
                            'type': 'binary',
                            'datas_fname': each_attachment[0],
                            'res_model': 'hr.expense',
                            'res_id': each_expense_item_line.id,
                        })

                        latest_expense_line = each_expense_item_line#for returning
                        selected_company = mail_server.company_id.id
                        self.create_message_monitor_entry_success(each_expense_item.name + " - " + each_expense_item_line.name, True, selected_company, each_expense_item_line)
        ###OCR Version###
        else:
            #loop through each attachment
            for each_attachment in attachments:
                all_orc_result = ""

                # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'#comment this out when using ubuntu server

                img_file = io.BytesIO(each_attachment[1])#[x][1]<- 1 is the binary data!, [0] is filename and [2] is path
                img_name = each_attachment[0]
                if img_name.lower().endswith('.pdf'):
                    image_pdf = convert_from_bytes(each_attachment[1])
                    # for page in image: #just OCR the first page
                    image = numpy.array(image_pdf[0].convert('RGB')) # just OCR the first page
                    ocr_result = pytesseract.image_to_string(image, lang='chi_tra+eng')
                    all_orc_result = all_orc_result + ocr_result
                    all_orc_result = self.check_langauge(all_orc_result, image)

                else:
                    image = Image.open(img_file)
                    ocr_result = pytesseract.image_to_string(image, lang='chi_tra+eng')  # gray the image
                    all_orc_result = self.check_langauge(ocr_result, image)

                print(all_orc_result)
                total, currency_type_OCR, shop, tax, date_receipt, error_occurred = self.get_relevant_data(all_orc_result, hugging_face_ai_api_key)
                if error_occurred == True:
                    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
                    current_time = datetime.now(malaysia_tz)
                    message_monitor = self.env['message.monitor.expense'].create({
                        'name': current_time,
                        'type': 'hr.expense',
                        'sheet_name': 'Error while running the Hugging Face AI, please check your Hugging Face API Key or you have already reached the AI call limit.\nIf you have reached your Hugging Face Limit, please create another free Hugging Face account and re-new the API key under configurations.',
                        'has_attachment': False,
                    })
                else:
                    print("-----------")
                    print("Shop: " + shop)
                    print("Tax: " + tax)
                    print("Total: " + total)
                    print("Currency Type: " + currency_type_OCR)
                    print("Date: " + date_receipt)

                    #format data
                    # date
                    date_input = self.check_date(date_receipt)
                    # date

                    # get total
                    if total == "":
                        total = '0'
                    else:
                        total = total.replace(",", "")  # some currency have 3,000 comma, remove it

                    total_split = total.split(" ")
                    currency = ""
                    currency_type = ""
                    total_float = 0
                    try:
                        if(len(total_split)>=2):
                            if total_split[0][0].isdigit(): # 1000 USD [0][0] to get first character of a string
                                total_float = float(total_split[0].replace(",", "")) # some currency have 3,000 comma, remove it
                            else: # USD 1000
                                total_float = float(total_split[1].replace(",", ""))
                        else:
                            total_float = float(total)
                    except:
                        print('total is an invalid number, set to 0')
                        total_float = 0

                    currency_type = self.env['res.currency'].search([('symbol', '=ilike', currency_type_OCR)])
                    if currency_type.name == False:  # If cannot find using symbol, search the currency name
                        currency_type = self.env['res.currency'].search([('name', '=ilike', currency_type_OCR)])
                    # get total
                    # data needed

                    if(employee_sender.display_name == False):# no employee with the emails was found
                        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
                        current_time = datetime.now(malaysia_tz)
                        print("employee not found.")
                        title = "No employee with the email [" + email_from + "] has been found, expense not created"
                        selected_company = ""
                        selected_company = mail_server.company_id.id
                        message_monitor = self.env['message.monitor.expense'].create({
                            'name': current_time,
                            'company_id': selected_company,
                            'type': 'hr.expense',
                            'sheet_name': title,
                            'has_attachment': False,
                        })

                    else:
                        # search for the sheet first
                        # search for the expense report with the correct date
                        expense = self.env['hr.expense.sheet'].search([
                            ('start_date', '<=', date_input),
                            ('end_date', '>=', date_input),
                            ('employee_id', '=', employee_sender.id),
                            ('state', '=', 'draft'),
                        ])
                        # if the sheet hasn't been created yet, create it. time frame is within the month.
                        if len(expense) == 0: #If len(expense) == 0 means that no expense report with the correct criteria have been found
                            try:
                                calendar.month_name[int(date_input.month)]
                                str(date_input.year)
                            except Exception as e:
                                print('except ', e)
                                date_input = datetime.now().date()
                                print('date_input ', date_input)
                            expense_sheet_name = employee_sender.display_name + " EXPENSE " + calendar.month_name[int(date_input.month)] + " " + str(date_input.year)
                            current_month_day_len = int(calendar.monthrange(int(date_input.year), int(date_input.month))[1])# this field is used to record how many days the current month has

                            expense = self.env['hr.expense.sheet'].create({
                                'name': expense_sheet_name,
                                'employee_id': employee_sender.id,
                                'user_id': employee_sender.expense_manager_id.id,
                                'company_id': employee_sender.company_id.id,
                                'start_date': date(int(date_input.year), int(date_input.month), 1),
                                'end_date': date(int(date_input.year), int(date_input.month), current_month_day_len),
                            })

                        # expense type
                        expense_type_selections = self.env['product.product'].search([('can_be_expensed', '=', True)])
                        expense_type = ""

                        for each in expense_type_selections:
                            if expense_description.strip().lower() in str(each.name).strip().lower():
                                expense_type = each.name

                        if expense_type == "":# if an expense type is not found then set it to default
                            print('expense_type_selections', expense_type_selections)
                            expense_type = expense_type_selections[0].name# chose the first one if non match

                        expense_type_id = self.env['product.product'].search([('name', '=', expense_type)])
                        # expense type


                        for each_expense_item in expense:# if there is multiple expense report that meets the criteria
                            # if currency_type.id != employee_sender.company_id.currency_id.id:
                            # for rec in self:
                            #     if employee_sender.company_id.currency_id is not False:
                            #         rec.custom_company_currency_id = employee_sender.company_id.currency_id #use the company's id
                            company_id_custom = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
                            default_custom_company_currency_id = self.env['res.company'].browse(company_id_custom).currency_id #use the company's id

                            if currency_type.id != default_custom_company_currency_id.id:
                                diff_cur_active = True
                                foregh_unit_price = total_float
                            else:
                                diff_cur_active = False
                                foregh_unit_price = 0 # currency type is same as company, so no need to set foregh_unit_price
                            each_expense_item_line = self.env['hr.expense'].create({
                                'date': date_input,
                                'name': shop + " Tax: " + tax,
                                'employee_id': employee_sender.id,
                                'company_id': employee_sender.company_id.id,
                                'foreigh_currency_id': currency_type.id,
                                'product_id': expense_type_id[0].id, # [0] ensures that if multiple items of the same name is found, only give the id of the first item found
                                'foregh_unit_price': foregh_unit_price,
                                'unit_amount': total_float,
                                'sheet_id': each_expense_item.id,
                                # 'analytic_account_id': 1,
                                'diff_cur_active': diff_cur_active,
                            })

                            each_expense_item_line.foreigh_currency_id = currency_type.id

                            image_data = base64.b64encode(each_attachment[1]).decode('utf-8')


                            saved_attachment = self.env['ir.attachment'].create({
                                'name': each_attachment[0],
                                'datas': image_data,
                                'type': 'binary',
                                'datas_fname': each_attachment[0],
                                'res_model': 'hr.expense',
                                'res_id': each_expense_item_line.id,
                            })

                            latest_expense_line = each_expense_item_line

                            if attachments:
                                has_attachment = True
                            else:
                                has_attachment = False
                            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
                            current_time = datetime.now(malaysia_tz)
                            selected_company = ""
                            selected_company = mail_server.company_id.id
                            message_monitor = self.env['message.monitor.expense'].create({
                                'name': current_time,
                                'type': 'hr.expense',
                                'company_id': selected_company,
                                'sheet_name': each_expense_item.name + " - " + each_expense_item_line.name,
                                'object_id': each_expense_item_line.id,
                                'has_attachment': has_attachment,
                            })
        return latest_expense_line #comment out for testing purposes

    # currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id
    expense_category_id = fields.Many2one('hr.expense.categoty', string="Category")
    foreigh_currency_id = fields.Many2one('res.currency', string="Currency", default=_default_currency_id)
    foregh_unit_price = fields.Float(string="Unit Price(FC)")


    custom_company_currency_id = fields.Many2one('res.currency', default=_default_currency_id, readonly=True, string="Company Currency")

    exchange_rate = fields.Float(string="Exchange Rate", default="1.0000", compute='_compute_exchange_rate')

    @api.depends('unit_amount', 'foregh_unit_price')
    def _compute_exchange_rate(self):
        for rec in self:
            rec.exchange_rate = 1# default exchange rate to 1
            if rec.foregh_unit_price != 0: # cannot divide by zero
                rec.exchange_rate = rec.unit_amount / rec.foregh_unit_price
            # force exchange rate to not be 0
                if not rec.exchange_rate:
                    rec.exchange_rate = 1.00
            # if rec.company_id.currency_id != rec.foreigh_currency_id:
                rec.unit_amount = rec.foregh_unit_price * rec.exchange_rate
                rec.total_amount = rec.unit_amount * rec.quantity

    diff_cur_active = fields.Boolean(
        string="is Other Currency?", default=False)

    @api.onchange('foreigh_currency_id', 'foregh_unit_price', 'exchange_rate', 'diff_cur_active')
    def onchange_set_product_price(self):
        # if self.diff_cur_active:
        if not self.exchange_rate:
            self.exchange_rate = 1.00
        self.unit_amount = self.foregh_unit_price * self.exchange_rate

    @api.onchange('foreigh_currency_id')
    def check_currency(self):
        if self.company_id.currency_id != self.foreigh_currency_id:
            self.diff_cur_active = True
        else:
            self.diff_cur_active = False

    @api.multi
    def write(self, vals):
        # if vals.get('unit_amount'):
        #     if float(vals['unit_amount']) == 0.0:
        #         raise ValidationError('Unit price cannot be 0!')
        res = super(HrExpense, self).write(vals)
        return res

    # @api.model
    # def create(self, vals):
    #     res = super(HrExpense, self).create(vals)
    #     return res

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.multi
    def approve_expense_sheets(self):
        res = super(HrExpenseSheet, self).approve_expense_sheets()
        for rec in self:
            if rec.user_id and rec.user_id.email:
                template_id = self.env.ref(
                    'goexcel_expense.email_template_event')
                if template_id:
                    template_id.write({
                        'email_from': rec.user_id.email,
                        'email_to': rec.employee_id.user_id.email
                    })
                    template_id.send_mail(rec.id, force_send=True)
        return res


    @api.multi
    def write(self, vals):
        res = super(HrExpenseSheet, self).write(vals)
        return res


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        for rec in self:
            if rec.parent_id:
                rec.expense_manager_id = rec.parent_id.user_id.id


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_expenses_to_pay_query(self):
        """
        Overwrite from hr_expense module
        """
        query = """SELECT total_amount as amount_total, currency_id AS currency
                  FROM hr_expense_sheet
                  WHERE state = 'approve'
                  and journal_id = %(journal_id)s"""
        return (query, {'journal_id': self.id})