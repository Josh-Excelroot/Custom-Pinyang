# See LICENSE file for full copyright and licensing details

import base64
import tempfile
from datetime import datetime
from xlrd import open_workbook

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError


def _offset_format_timestamp(src_tstamp_str, src_format, dst_format, ignore_unparsable_time=True, context=None):
    """
    Convert a source timestamp string into a destination timestamp string, attempting to apply the
    correct offset if both the server and local timezone are recognized, or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they are both in the same TZ).

    @param src_tstamp_str: the str value containing the timestamp.
    @param src_format: the format to use when parsing the local timestamp.
    @param dst_format: the format to use when formatting the resulting timestamp.
    @param server_to_client: specify timezone offset direction (server=src and client=dest if True, or client=src and server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str cannot be parsed
                                   using src_format or formatted using dst_format.

    @return: destination formatted timestamp, expressed in the destination timezone if possible
            and if tz_offset is true, or src_tstamp_str if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False

    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object (so no time.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str,src_format)
            if context.get('tz',False):
                try:
                    import pytz
                    src_tz = pytz.timezone('UTC')
                    dst_tz = pytz.timezone(context['tz'])
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception as e:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception as e:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res

class UploadXlsWiz(models.TransientModel):

    _name  = "upload.xls.wiz"

    _description = 'Upload xls file for allowances or deductions input fields.'

    in_file= fields.Binary('Input File', required=True, filters='*.xls')
    datas_fname = fields.Char('Filename')
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    clear_all_prev_value= fields.Boolean('OVERRITE ALL VALUES', default=True)

    @api.constrains('date_from','date_end')
    def check_date(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be anterior to End date")

    @api.multi
    def upload_file(self):
        """
        This method will upload the xsl file.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: ID or list of IDs
        @param context:global dictionary
        """
        context = dict(self._context)
        if context is None:
            context = {}
        temp_path = tempfile.gettempdir()
        user_object = self.env['res.users']
        employee_object = self.env['hr.employee']
        filename_str = str(self.datas_fname)
        split_file = filename_str.split('.')
        if not filename_str[-4:] == ".xls":
            raise ValidationError(_('Select .xls file only'))
        csv_data = base64.decodestring(self.in_file)
        fp=open(temp_path+'/xsl_file.xls', 'wb+')
        fp.write(csv_data)
        fp.close()
        wb = open_workbook(temp_path+'/xsl_file.xls')
        hr_rule_input_brw = self.env['hr.rule.input'].search([])
        hr_rule_input_list = []
        for input in hr_rule_input_brw:
            hr_rule_input_list.append(input.code)

        xls_dict = {}
        xls_new_dict = {}
        for sheet in wb.sheets():
            for rownum in range(sheet.nrows):
                if rownum == 0:
                    i=1
                    first_headers = []
                    header_list = sheet.row_values(rownum)
                    new_header_list = sheet.row_values(rownum)
                    for header in new_header_list:
                        if header not in hr_rule_input_list and header not in ['name', 'NAME', 'REMARKS', 'EMPLOYEELOGIN']:
                            raise UserError(_('Check Salary input code. %s Salary Input code not exists.' % header))
                    for header in header_list:
                        xls_dict.update({i: ustr(header)})
                        i=i+1
                        if header in first_headers:
                            raise UserError(_('Duplicate salary input code %s found.' % header))
                        elif header not in ['name', 'NAME']:
                            first_headers.append(header)
                    remark_index = header_list.index('REMARKS')
                else:
                    i=1
                    headers = sheet.row_values(rownum)
                    for record in headers:
                        xls_new_dict.update({i: ustr(record)})
                        i = i+1
                    emp_login = ''
                    if type(sheet.row_values(rownum)[header_list.index('EMPLOYEELOGIN')]) == type(0.0):
                        emp_login = ustr(int(sheet.row_values(rownum)[header_list.index('EMPLOYEELOGIN')]))
                    else:
                        emp_login = ustr(sheet.row_values(rownum)[header_list.index('EMPLOYEELOGIN')])
                    user_ids = user_object.search([('login', '=', emp_login)])
                    if not user_ids:
                        user_ids = user_object.search([('login', '=', emp_login), ('active', '=', False)])
                        if user_ids:
                            raise UserError(_('Employee login %s is inactive for row number %s. ' % (emp_login, rownum+1) ))
                        raise UserError(_('Employee login %s not found for row number %s. ' % (emp_login, rownum+1) ))
                    emp_ids = employee_object.search([('user_id', 'in', user_ids.ids)])
                    if not emp_ids:
                        emp_ids = employee_object.search([('user_id', 'in', user_ids.ids), ('active', '=', False)])
                        if emp_ids:
                            raise UserError(_('Employee is inactive for login %s for row number %s.' % (emp_login, rownum+1) ))
                        raise UserError(_('No employee found for %s login name for row number %s.' % (emp_login, rownum+1) ))
                    if emp_ids:
                        contract_ids = self.env['hr.contract'].search([('employee_id', 'in', emp_ids.ids), ('date_start','<=', self.date_start), '|', ('date_end', '>=', self.date_end),('date_end','=',False)])
                        if not contract_ids:
                            raise UserError(_('Contract not found for Employee login %s in row number %s.' % (emp_login, rownum+1) ))
                        pay_slip_ids = self.env['hr.payslip'].search([('state','=','draft'),('employee_id', 'in', emp_ids.ids), ('date_from', '>=', self.date_start), ('date_to', '<=', self.date_end)])
                        if not pay_slip_ids:
                            raise UserError(_('There is no payslip  available or there is no payslip in darft state for Employee login %s in row number %s.' % (emp_login, rownum+1) ))
                        for pay_slip in pay_slip_ids:
                            if not pay_slip.contract_id:
                                raise UserError(_('Employee contract not found or not assign in payslip for %s for row number %s.' % (pay_slip.employee_id.name, rownum+1) ))
                            note = pay_slip.note or ''
                            user_data = self.env['res.users'].browse(self._uid)
                            context.update({'tz': user_data.tz})
                            user_current_date =  _offset_format_timestamp(datetime.today(), '%Y-%m-%d %H:%M:%S', '%d-%B-%Y %H:%M:%S', context=context)
                            note += '\nUploaded by ' + ustr(user_data.name or '') + ' on ' + ustr(user_current_date.strftime('%d-%b-%Y %H:%M:%S')) + ' \n ------------------------------------------------------ \n'
                            for xls in xls_dict:
                                for input_data in pay_slip.input_line_ids:
                                    xls_dict[xls]
                                    if input_data.code == xls_dict[xls]:
                                        salary_amt = xls_new_dict.get(xls).strip()
                                        if salary_amt:
                                            salary_amt = float(salary_amt)
                                        else :
                                            salary_amt = 0.00
                                        if self.clear_all_prev_value:
                                            input_line_amount = salary_amt or 0.00
                                        else:
                                            input_line_amount = salary_amt + input_data.amount or 0.0
                                        input_data.write({'amount': input_line_amount})
                                        note += ustr(xls_dict[xls]) + " "*5 + ustr(salary_amt) + " "*5 + sheet.row_values(rownum)[remark_index] + '\n'
                            if note:
                                pay_slip.write({'note':note})
                                pay_slip.compute_sheet()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: