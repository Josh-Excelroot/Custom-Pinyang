# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key_expense_ocr = fields.Char(string='Hugging Face AI API Key', config_parameter='hr_expense.api_key_expense_ocr', help='Hugging face API Key Location \nFirstly go to the Hugging Face website and log in (If you dont have an account, simply create one).\nSetting>Access Token>New Token')