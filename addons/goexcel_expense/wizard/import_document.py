import base64
import io
from datetime import datetime

import numpy
import pytesseract
import pytz
from PIL import Image
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from pdf2image import convert_from_bytes
from datetime import date

class ExpenseWizardUpload(models.TransientModel):
    _name = 'expense.document.wizard'
    _description = "Upload Documents"

    document = fields.Binary(string='Documents')
    document_filename = fields.Char("File name")

    def read_document_OCR(self):
        print("MANUAL_READ_OPERATION")
        hr_expense_class = self.env['hr.expense']
        hugging_face_ai_api_key = self.env['ir.config_parameter'].sudo().get_param('hr_expense.api_key_expense_ocr')
        print("check here")
        print(hugging_face_ai_api_key)

        if hugging_face_ai_api_key == False:
            print("No Hugging Face API key, using non-OCR function")
            byte_document = base64.b64decode(self.document)#convert document to byte
            expense = self.env['hr.expense.sheet'].browse(self._context.get('active_ids', [])[0])
            expense_type_id, default_custom_company_currency_id, diff_cur_active, foregh_unit_price, currency_type = self.get_expense_line_data("None", 0)
            company_id_custom = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
            default_custom_company_currency_id = self.env['res.company'].browse(company_id_custom).currency_id  # use the company's id


            each_expense_item_line = self.env['hr.expense'].create({
                'date': date.today(),
                'name': self.document_filename,
                'employee_id': expense.employee_id.id,
                'company_id': expense.employee_id.company_id.id,
                'foreigh_currency_id': default_custom_company_currency_id.id,
                'product_id': expense_type_id[0].id,
                # [0] ensures that if multiple items of the same name is found, only give the id of the first item found
                'foregh_unit_price': 0,
                'unit_amount': 0,
                'sheet_id': expense.id,
                # 'analytic_account_id': 1,
                'diff_cur_active': False,
            })

            each_expense_item_line.foreigh_currency_id = default_custom_company_currency_id.id# set
            self.save_attachment(byte_document, each_expense_item_line)# save image
            self.create_success_message_monitor_entry(expense.name + " - " + each_expense_item_line.name, expense.employee_id.company_id, True,each_expense_item_line)  # company id here is following the selected employee's company


        else:
            # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # comment this out when using ubuntu server
            byte_document = base64.b64decode(self.document)
            all_orc_result = ""
            if self.document_filename.lower().endswith('.pdf'):
                image_pdf = convert_from_bytes(byte_document)
                # for page in image:# just OCR the first page
                image = numpy.array(image_pdf[0].convert('RGB')) # just OCR the first page
                ocr_result = pytesseract.image_to_string(image, lang='chi_tra+eng')
                all_orc_result = all_orc_result + ocr_result
                all_orc_result = hr_expense_class.check_langauge(all_orc_result, image)
            else:
                img_file = io.BytesIO(byte_document)
                image = Image.open(img_file)
                ocr_result = pytesseract.image_to_string(image, lang='chi_tra+eng')  # gray the image
                all_orc_result = hr_expense_class.check_langauge(ocr_result, image)

            print(all_orc_result)
            print("_End_Of_OCR_Result_")

            total, currency_type_OCR, shop, tax, date_receipt, error_occurred = hr_expense_class.get_relevant_data(all_orc_result, hugging_face_ai_api_key)
            if error_occurred == True:#Error Occured with AI
                self.create_message_monitor_entry('Error while running the Hugging Face AI, please check your Hugging Face API Key or you have already reached the AI call limit.\nIf you have reached your Hugging Face Limit, please create another free Hugging Face account and re-new the API key under configurations.', False)
                raise ValidationError("Error while running the Hugging Face AI, please check your Hugging Face API Key or you have already reached the AI call limit.\nIf you have reached your Hugging Face Limit, please create another free Hugging Face account and re-new the API key under configurations.")
            else:
                print("Shop: " + shop)
                print("Tax: " + tax)
                print("Total: " + total)
                print("Currency Type: " + currency_type_OCR)
                print("Date: " + date_receipt)
                print("_End_Of_Result_")

                total_float, date_input = self.format_data(hr_expense_class, date_receipt, total)
                expense = self.env['hr.expense.sheet'].browse(self._context.get('active_ids', [])[0])
                print(expense.employee_id)

                #get required data to create the expense line
                expense_type_id, default_custom_company_currency_id, diff_cur_active, foregh_unit_price, currency_type = self.get_expense_line_data(currency_type_OCR, total_float)

                #create the expense line
                each_expense_item_line = self.env['hr.expense'].create({
                    'date': date_input,
                    'name': shop + " Tax: " + tax,
                    'employee_id': expense.employee_id.id,
                    'company_id': expense.employee_id.company_id.id,
                    'foreigh_currency_id': currency_type.id,
                    'product_id': expense_type_id[0].id,# [0] ensures that if multiple items of the same name is found, only give the id of the first item found
                    'foregh_unit_price': foregh_unit_price,
                    'unit_amount': total_float,
                    'sheet_id': expense.id,
                    # 'analytic_account_id': 1,
                    'diff_cur_active': diff_cur_active,
                })

                each_expense_item_line.foreigh_currency_id = currency_type.id
                self.save_attachment(byte_document, each_expense_item_line)#save image
                self.create_success_message_monitor_entry(expense.name + " - " + each_expense_item_line.name, expense.employee_id.company_id, True, each_expense_item_line)#company id here is following the selected employee's company

    def save_attachment(self, byte_document, each_expense_item_line):
        image_data = base64.b64encode(byte_document).decode('utf-8')
        saved_attachment = self.env['ir.attachment'].create({
            'name': self.document_filename,
            'datas': image_data,
            'type': 'binary',
            'datas_fname': self.document_filename,
            'res_model': 'hr.expense',
            'res_id': each_expense_item_line.id,
        })

    def get_expense_line_data(self, currency_type_OCR, total_float):
        #expense type
        expense_type_selections = self.env['product.product'].search([('can_be_expensed', '=', True)])
        expense_type = expense_type_selections[0].name  # chose the first one since there is no option for the user to choose
        expense_type_id = self.env['product.product'].search([('name', '=', expense_type)])

        #company default currency
        company_id_custom = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        default_custom_company_currency_id = self.env['res.company'].browse(company_id_custom).currency_id  # use the company's id

        currency_type = self.env['res.currency'].search([('symbol', '=ilike', currency_type_OCR)])
        if currency_type.name == False: #If cannot find using symbol, search the currency name
            currency_type = self.env['res.currency'].search([('name', '=ilike', currency_type_OCR)])

        if currency_type.id != default_custom_company_currency_id.id:
            diff_cur_active = True
            foregh_unit_price = total_float
        else:
            diff_cur_active = False
            foregh_unit_price = 0  # currency type is same as company, so no need to set foregh_unit_price
        return expense_type_id, default_custom_company_currency_id, diff_cur_active, foregh_unit_price, currency_type

    #this function formats the retrieved data
    def format_data(self, hr_expense_class, date_receipt, total):
        # date
        date_input = hr_expense_class.check_date(date_receipt)

        # get total
        if total == "":
            total = '0'
        else:
            total = total.replace(",", "")# some currency have 3,000 comma, remove it

        total_split = total.split(" ")
        try:
            if (len(total_split) >= 2): # in the case where the total has the prefix attached eg, RM 2000
                if total_split[0][0].isdigit():  # 1000 USD [0][0] to get first character of a string
                    total_float = float(total_split[0])
                else:  # USD 1000
                    total_float = float(total_split[1])
            else:
                total_float = float(total)
        except:
            print('total is an invalid number, set to 0')
            total_float = 0
        return total_float, date_input

    def create_message_monitor_entry(self, sheet_name, has_attachment):
        # Obtain datetime
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_time = datetime.now(malaysia_tz)

        message_monitor = self.env['message.monitor.expense'].create({
            'name': current_time,
            'type': 'hr.expense',
            'sheet_name': sheet_name,
            'has_attachment': has_attachment,
        })

    def create_success_message_monitor_entry(self, sheet_name, selected_company, has_attachment, each_expense_item_line):
        # Obtain datetime
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_time = datetime.now(malaysia_tz)

        message_monitor = self.env['message.monitor.expense'].create({
            'name': current_time,
            'type': 'hr.expense',
            'company_id': selected_company.id,
            'sheet_name': sheet_name,
            'object_id': each_expense_item_line.id,
            'has_attachment': has_attachment,
        })