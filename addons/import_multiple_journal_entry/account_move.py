# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import json
import io
import datetime
import tempfile
import binascii
import xlrd
import itertools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, api, _
import logging
from operator import itemgetter

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class gen_journal_entry(models.TransientModel):
    _name = "gen.journal.entry"

    file_to_upload = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')

    @api.multi
    def find_account_id(self, account_code):
        if account_code:
            account_ids = self.env['account.account'].search([('code', '=', account_code.split('.'))])
            if not account_ids:
                account_ids = self.env['account.account'].search([('name', 'ilike', account_code)])
            if account_ids:
                account_id = account_ids[0]
                return account_id
            else:
                return False

    @api.multi
    def check_desc(self, name):
        if name:
            return name
        else:
            return ''

    @api.multi
    def find_account_analytic_id(self, analytic_account_name):
        analytic_account_id = self.env['account.analytic.account'].search([('name', '=', analytic_account_name)])
        if analytic_account_id:
            analytic_account_id = analytic_account_id[0].id
            return analytic_account_id
        else:
            raise Warning(_('Wrong Analytic Account Name: {}'.format(analytic_account_name)))

    @api.multi
    def find_analytic_tag_id(self, analytic_tag_name):
        analytic_tag_ids = self.env['account.analytic.tag'].search([('name', '=', analytic_tag_name)])
        if analytic_tag_ids:
            analytic_tag_id = analytic_tag_ids[0]
            return analytic_tag_id
        else:
            raise Warning(_('Wrong Analytic Account Tag: {}'.format(analytic_tag_name)))

    @api.multi
    def find_partner_by_ref(self, partner_ref):
        partner_ids = self.env['res.partner'].search([('ref', '=', partner_ref)])
        if partner_ids:
            partner_id = partner_ids[0]
            return partner_id
        else:
            partner_id = None

    @api.multi
    def find_partner_by_name(self, partner_name):
        partner_ids = self.env['res.partner'].search([('name', '=', partner_name)])
        if partner_ids:
            partner_id = partner_ids[0]
            return partner_id
        else:
            partner_id = None

    @api.multi
    def check_currency(self, cur_name):
        currency_ids = self.env['res.currency'].search([('name', '=', cur_name)])
        if currency_ids:
            currency_id = currency_ids[0]
            return currency_id
        else:
            currency_id = None
            return currency_id

    @api.multi
    def create_import_move_lines(self, values):
        move_line_obj = self.env['account.move.line']
        move_obj = self.env['account.move']
        if values.get('partner_code'):
            partner_ref = values.get('partner_code')
            if self.find_partner_by_ref(partner_ref) != None:
                partner_id = self.find_partner_by_ref(partner_ref)
                values.update({'partner_id': partner_id.id})
        elif values.get('partner'):
            partner_name = values.get('partner')
            if self.find_partner_by_name(partner_name) != None:
                partner_id = self.find_partner_by_name(partner_name)
                values.update({'partner_id': partner_id.id})


        if values.get('currency'):
            cur_name = values.get('currency')
            if cur_name != '' and cur_name != None:
                currency_id = self.check_currency(cur_name)
                if currency_id != None:
                    values.update({'currency_id': currency_id.id})
                else:
                    raise Warning(_('"%s" Currency %s is not  in the system') % cur_name)

        if values.get('name'):
            desc_name = values.get('name')
            name = self.check_desc(desc_name)
            values.update({'name': name})

        if values.get('date_maturity'):
            date = values.get('date_maturity')
            values.update({'date_maturity': date})

        if values.get('account_code'):
            account_code = values.get('account_code')
            account_id = self.find_account_id(str(account_code))
            if account_id not in [False, None]:
                values.update({'account_id': account_id.id})
            else:
                # pass
                raise Warning(_('"%s" Wrong Account Code %s') % account_code)

        if values.get('debit') != '':
            values.update({'debit': float(str(values.get('debit')).replace(',', ''))})
            if float(str(values.get('debit')).replace(',', '')) < 0:
                values.update({'credit': abs(values.get('debit'))})
                values.update({'debit': 0.0})
        else:
            values.update({'debit': float('0.0')})

        if values.get('name') == '':
            values.update({'name': '/'})

        if values.get('credit') != '':
            values.update({'credit': float(str(values.get('credit')).replace(',', ''))})
            if float(str(values.get('credit')).replace(',', '')) < 0:
                values.update({'debit': abs(values.get('credit'))})
                values.update({'credit': 0.0})
        else:
            values.update({'credit': float('0.0')})
        # kashif 21 july23: if amount curr not provided then neglect it
        if 'amount_currency' in values.keys():
            if values.get('amount_currency') != '':
                values.update({'amount_currency': str(values.get('amount_currency')).replace(',', '')})
            else:
                values.update({'amount_currency': str(values.get('amount_currency')).replace('', 0)})
        # end
        if values.get('analytic_account_id') != '':
            account_anlytic_account = values.get('analytic_account_id')
            if account_anlytic_account != '' or account_anlytic_account == None:
                analytic_account_id = self.find_account_analytic_id(account_anlytic_account)
                values.update({'analytic_account_id': analytic_account_id})
            else:
                raise Warning(_('"%s" Wrong Account Code %s') % account_anlytic_account)

        if values.get('analytic_tag_ids') != '':
            analytic_tag_name = values.get('analytic_tag_ids')
            if analytic_tag_name != '':
                analytic_tag_id = self.find_analytic_tag_id(analytic_tag_name)
                values.update({'analytic_tag_ids': [(6, 0, [analytic_tag_id.id])]})
            else:
                raise Warning(_('"%s" Wrong Account Tag %s') % analytic_tag_name)

        return values

    @api.multi
    def import_move_lines(self):
        if self.import_option == 'csv':
            keys = ['date', 'ref', 'journal', 'name', 'partner', 'analytic_account_id', 'account_code', 'date_maturity',
                    'debit', 'credit', 'amount_currency', 'currency']
            try:
                csv_data = base64.b64decode(self.file_to_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise Warning(_("Invalid file!"))

            values = {}
            lines = []
            data = []
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))

                if values:
                    if i == 0:
                        continue
                    else:
                        # kashif 18july23: added code to get right date format
                        date = datetime.strptime(values.get('date'), "%d/%m/%Y")
                        values.update({'date': date.date()})
                        values.pop('date')
                        values.pop('date_maturity')
                        values.update({
                            'name': values.get('ref')
                        })
                        # end
                        data.append(values)

            data1 = {}
            # sorted_data =sorted(data,key=lambda x:x['ref'])
            list1 = []
            for key, group in itertools.groupby(data, key=lambda x: x['ref']):
                small_list = []
                for i in group:
                    small_list.append(i)
                    data1.update({key: small_list})

            lines = []

            for key in data1.keys():

                move = False
                values = data1.get(key)
                for val in values:
                    res = self.create_import_move_lines(val)
                    if 'account_id' in res:
                        move_obj = self.env['account.move']
                        if val.get('journal'):
                            journal_search = self.env['account.journal'].search([('name', '=', val.get('journal'))])
                            if journal_search:
                                # date = datetime.strptime(val.get('date'), "%Y-%m-%d")
                                move1 = move_obj.search([('date', '=', val.get('date')),
                                                         ('ref', '=', val.get('ref')),
                                                         ('journal_id', '=', journal_search.name)])
                                if move1:
                                    move = move1
                                else:
                                    move = move_obj.create(
                                        {'date': val.get('date') or False, 'ref': val.get('ref') or False,
                                         'journal_id': journal_search.id})
                            else:
                                raise Warning(_('Please Define Journal which are already in system.'))
                        lines.append((0, 0, res))
            if not move:
                move = move_obj.create({'date': '01-07-2023', 'ref': "Opening balance June 2023",
                                        'journal_id': self.env['account.journal'].search(
                                            [('type', '=', 'general'), ('code', '=', 'MISC')], limit=1).id})

            move.write({'line_ids': lines})
            move.write({'ref': 'Opening balance June 2023'})


        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_to_upload))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise Warning(_('Invalid Excel File!!'))
            product_obj = self.env['product.product']
            lines = []
            data = []
            move_obj = self.env['account.move']

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))

                    date = False
                    if line[0] != '':
                        if line[13] != '':
                            date = str(xlrd.xldate.xldate_as_datetime(int(float(line[13])), workbook.datemode))
                        else:
                            date = False
                        main_date = str(xlrd.xldate.xldate_as_datetime(int(float(line[0])), workbook.datemode))
                        # kashif 18july23: added sign for other currency credit amount

                        sign = -1 if float(line[12] and line[12] != '' or 0.0) > 0 and float(
                            line[11] and line[11] != '' or 0.0) > 0.00 else 1
                        # end

                        # values = {'date': main_date,
                        #           'name': line[1], #account.move.line name (label)
                        #           'ref': line[2], # account.move reference
                        #           'partner': line[3],
                        #           'partner_code' : line[4], #partner internal reference
                        #           'account_code': line[5],
                        #           'currency': line[6],
                        #           'analytic_tag': line[7],
                        #           'debit': line[8],
                        #           'credit': line[9],
                        #           'amount_currency': float(line[10] if line[10] != '' else 0.0) * sign,
                        #           'analytic_account' : line[11],
                        #           'date_maturity': date,
                        #           }
                        values = {
                            'date': main_date,
                            'ref': line[1],  # account.move reference
                            'journal': line[2],
                            'partner': line[3],
                            'partner_code': line[4],  # partner internal reference
                            'name': line[5],  # account.move.line name (label)
                            'account_code': line[6],
                            'analytic_account_id': line[7],
                            'analytic_tag_ids': line[8],
                            # 'amount_currency': float(line[9] if line[9] != '' else 0.0) * sign,
                            'amount_currency': float(line[9] if line[9] != '' else 0.0),
                            'currency': line[10],
                            'debit': line[11],
                            'credit': line[12],
                            'date_maturity': date,
                        }
                        data.append(values)

                    # else:
                    #     raise Warning(_('Define Date or Amount In Corresponding Columns !!!'))
            data1 = {}

            sorted_data = sorted(data, key=lambda x: x['ref'])
            list1 = []
            for key, group in itertools.groupby(sorted_data, key=lambda x: x['ref']):
                small_list = []
                for i in group:
                    small_list.append(i)
                    data1.update({key: small_list})

            for key in data1.keys():
                lines = []
                move = False
                values = data1.get(key)
                for val in values:
                    res = self.create_import_move_lines_ob(val)

                    move_obj = self.env['account.move']
                    if val.get('journal'):
                        journal_search = self.env['account.journal'].search([('name', '=', val.get('journal'))])
                        if journal_search:
                            # date =datetime. datetime.strptime(val.get('date'), "%Y-%m-%d")
                            move1 = move_obj.search([('date', '=', val.get('date')),
                                                     ('ref', '=', val.get('ref')),
                                                     ('journal_id', '=', journal_search.name)])
                            if move1:
                                move = move1
                            else:
                                move = move_obj.create(
                                    {'name': val.get('ref') or False,
                                     'date': val.get('date') or False,
                                     'ref': val.get('ref') or False,
                                     'journal_id': journal_search.id})
                        else:
                            raise Warning(_('Please Define Journal which are already in system.'))
                    lines.append((0, 0, res))
                if not move:
                    move = move_obj.create({'date': '01-07-2023', 'ref': "Opening Balance",
                                            'journal_id': self.env['account.journal'].search(
                                                [('type', 'in', ['cash', 'bank'])], limit=1).id})

                move.write({'line_ids': lines})

    # kashif 18july23: added separate method to counter Opening balance import
    # Ahmad Zaman - 8/8/23 : Fixed excel import issue
    @api.multi
    def create_import_move_lines_ob(self, values):
        move_line_obj = self.env['account.move.line']
        move_obj = self.env['account.move']
        if values.get('partner_code'):
            partner_ref = values.get('partner_code')
            if self.find_partner_by_ref(partner_ref) != None:
                partner_id = self.find_partner_by_ref(partner_ref)
                values.update({'partner_id': partner_id.id})
        elif values.get('partner'):
            partner_name = values.get('partner')
            if self.find_partner_by_name(partner_name) != None:
                partner_id = self.find_partner_by_name(partner_name)
                values.update({'partner_id': partner_id.id})

        if values.get('currency'):
            cur_name = values.get('currency')
            if cur_name != '' and cur_name != None:
                currency_id = self.check_currency(cur_name)
                # if currency_id.name == "USD" and values.get('amount_currency') in [0, None]:
                #     raise Warning(_("Currency amount not defined for line {} under journal {}").format(values.get('name'),values.get('ref')))
                if currency_id != None:
                    values.update({'currency_id': currency_id.id})
                else:
                    raise Warning(_('"%s" Currency %s is not in the system') % cur_name)

        if values.get('name'):
            desc_name = values.get('name')
            name = self.check_desc(desc_name)
            values.update({'name': name})

        if values.get('date_maturity'):
            date = values.get('date_maturity')
            values.update({'date_maturity': date})

        if values.get('account_code'):
            account_code = values.get('account_code')
            account_id = self.find_account_id(str(account_code))
            if account_id not in [False, None]:
                values.update({'account_id': account_id.id})
            else:
                # pass
                raise Warning(_('"%s" Wrong Account Code %s') % account_code)

        if values.get('debit') != '':
            values.update({'debit': float(values.get('debit'))})
            if float(values.get('debit')) < 0:
                values.update({'credit': abs(values.get('debit'))})
                values.update({'debit': 0.0})
        else:
            values.update({'debit': float('0.0')})

        if values.get('name') == '':
            values.update({'name': ''})

        if values.get('credit') != '':
            values.update({'credit': float(values.get('credit'))})
            # if float(values.get('credit')) < 0:
            #     values.update({'debit': abs(values.get('credit'))})
            #     values.update({'credit': 0.0})
        else:
            values.update({'credit': float('0.0')})

        if values.get('amount_currency') != '':
            values.update({'amount_currency': float(values.get('amount_currency'))})

        if values.get('analytic_account_id') != '':
            account_anlytic_account = values.get('analytic_account_id')
            if account_anlytic_account != '' or account_anlytic_account == None:
                # pass
                analytic_account_id = self.find_account_analytic_id(account_anlytic_account)
                values.update({'analytic_account_id': analytic_account_id})
            else:
                raise Warning(_('"%s" Wrong Account Code %s') % account_anlytic_account)

        if values.get('analytic_tag_ids') != '':
            analytic_tag_name = values.get('analytic_tag_ids')
            if analytic_tag_name != '':
                analytic_tag_id = self.find_analytic_tag_id(analytic_tag_name)
                values.update({'analytic_tag_ids': [(6, 0, [analytic_tag_id.id])]})
            else:
                raise Warning(_('"%s" Wrong Account Tag %s') % analytic_tag_name)

        return values
# end
