# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
import time
import tempfile
import binascii
import xlrd
import io
import itertools
import codecs
from io import StringIO, BytesIO
# import pandas as pd
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _

_logger = logging.getLogger(__name__)


class AccountingWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    # def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
    #     # Redirect output to a queue
    #     self.queue = StringIO()
    #     # created a writer with Excel formating settings
    #     self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
    #     self.stream = f
    #     self.encoder = codecs.getincrementalencoder(encoding)()
    #
    # def writerow(self, row):
    #     # we ensure that we do not try to encode none or bool
    #     row = (x or '' for x in row)
    #     self.writer.writerow(row)
    #     # Fetch UTF-8 output from the queue ...
    #     data = self.queue.getvalue()
    #     # ... and reencode it into the target encoding as BytesIO
    #     data = self.encoder.encode(data)
    #     # write to the target stream
    #     self.stream.write(data)
    #     # seek() or truncate() have side effect if not used combinated
    #     self.queue.truncate(0)
    #     self.queue.seek(0)
    #     # https://stackoverflow.com/questions/4330812/how-do-i-clear-a-stringio-object
    #     # It fails when you use `self.queue = StringIO()` only add one line
    #
    # def writerows(self, rows):
    #     for row in rows:
    #         self.writerow(row)
    #     # https://docs.python.org/3/library/io.html#io.IOBase.close
    #     self.queue.close()


class SIUploadWizard(models.TransientModel):
    _name = "si.upload.wizard"

    file_to_upload = fields.Binary('File')
    #data = fields.Binary('Excel', readonly=True)
    import_filename = fields.Char("Import File Name")

    @api.multi
    def import_si(self):
        #https://xlrd.readthedocs.io/
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file_to_upload))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except FileNotFoundError:
            raise UserError('No such file or directory found. \n%s.' % self.file)
        except xlrd.biffh.XLRDError:
            raise UserError('Only excel files are supported.')
        original_bol = False
        freight_prepaid = False
        seawaybill = False
        freight_collect = False
        telex_release = False
        si_id = self.env.context.get('id')
        si = self.env['freight.website.si'].browse(si_id)
        shipper_addr = ''
        if sheet.cell_value(1, 1) and len(sheet.cell_value(1, 1))>0:
            shipper_addr += sheet.cell_value(1, 1) + "\n"
        if sheet.cell_value(2, 1) and len(sheet.cell_value(2, 1))>0:
            shipper_addr += sheet.cell_value(2, 1) + "\n"
        if sheet.cell_value(3, 1) and len(sheet.cell_value(3, 1))>0:
            shipper_addr += sheet.cell_value(3, 1) + "\n"
        if sheet.cell_value(4, 1) and len(sheet.cell_value(4, 1))>0:
            shipper_addr += sheet.cell_value(4, 1) + "\n"
        if sheet.cell_value(5, 1) and len(sheet.cell_value(5, 1))>0:
            shipper_addr += sheet.cell_value(5, 1) + "\n"
        if sheet.cell_value(6, 1) and len(sheet.cell_value(6, 1))>0:
            shipper_addr += sheet.cell_value(6, 1) + "\n"
        if len(shipper_addr)>1:
            si.shipper = shipper_addr
        consignee_addr = ''
        if sheet.cell_value(7, 1) and len(sheet.cell_value(7, 1))>0:
            consignee_addr += sheet.cell_value(7, 1) + "\n"
        if sheet.cell_value(8, 1) and len(sheet.cell_value(8, 1))>0:
            consignee_addr += sheet.cell_value(8, 1) + "\n"
        if sheet.cell_value(9, 1) and len(sheet.cell_value(9, 1))>0:
            consignee_addr += sheet.cell_value(9, 1) + "\n"
        if sheet.cell_value(10, 1) and len(sheet.cell_value(10, 1))>0:
            consignee_addr += sheet.cell_value(10, 1) + "\n"
        if sheet.cell_value(11, 1) and len(sheet.cell_value(11, 1))>0:
            consignee_addr += sheet.cell_value(11, 1) + "\n"
        if sheet.cell_value(12, 1) and len(sheet.cell_value(12, 1))>0:
            consignee_addr += sheet.cell_value(12, 1) + "\n"
        if len(consignee_addr)>1:
            si.consignee = consignee_addr
        notify_party_addr = ''
        if sheet.cell_value(7, 1) and len(sheet.cell_value(7, 1))>0:
            notify_party_addr += sheet.cell_value(7, 1) + "\n"
        if sheet.cell_value(8, 1) and len(sheet.cell_value(8, 1))>0:
            notify_party_addr += sheet.cell_value(8, 1) + "\n"
        if sheet.cell_value(9, 1) and len(sheet.cell_value(9, 1))>0:
            notify_party_addr += sheet.cell_value(9, 1) + "\n"
        if sheet.cell_value(10, 1) and len(sheet.cell_value(10, 1))>0:
            notify_party_addr += sheet.cell_value(10, 1) + "\n"
        if sheet.cell_value(11, 1) and len(sheet.cell_value(11, 1))>0:
            notify_party_addr += sheet.cell_value(11, 1) + "\n"
        if sheet.cell_value(12, 1) and len(sheet.cell_value(12, 1))>0:
            notify_party_addr += sheet.cell_value(12, 1) + "\n"
        if len(notify_party_addr)>1:
            si.notify_party = notify_party_addr
        # print(sheet.cell_value(row, col))
        if sheet.cell_value(3, 3) and len(sheet.cell_value(3, 3))>0:
            original_bol = True
        if sheet.cell_value(3, 4) and len(sheet.cell_value(3, 4))>0:
            freight_prepaid = True
        if sheet.cell_value(3, 5) and len(sheet.cell_value(3, 5))>0:
            telex_release = True
        if sheet.cell_value(6, 3) and len(sheet.cell_value(6, 3))>0:
            seawaybill = True
        if sheet.cell_value(6, 4) and len(sheet.cell_value(6, 4))>0:
            freight_collect = True
        if sheet.cell_value(20, 2) and len(sheet.cell_value(20, 2))>0:
            si.place_of_receipt = sheet.cell_value(20, 2)
        if sheet.cell_value(19, 6) and len(sheet.cell_value(19, 6))>0:
            si.place_of_delivery = sheet.cell_value(19, 6)
        if sheet.cell_value(21, 6) and len(sheet.cell_value(21, 6))>0:
            si.place_of_delivery = sheet.cell_value(21, 6)
        if original_bol:
            si.bill_of_lading_type = 'original'
        elif seawaybill:
            si.bill_of_lading_type = 'seaway'
        elif telex_release:
            si.bill_of_lading_type = 'telex'
        if freight_prepaid:
            si.freight_type = 'prepaid'
        elif freight_collect:
            si.freight_type = 'collect'

        count_of_data_rows = self.get_data_rows(22, sheet, 'marking')

        data_marking = []
        row = 23
        for i in range(count_of_data_rows):
            values = {"marking": sheet.cell_value(row, 0),
                      "description": sheet.cell_value(row, 2)}
            data_marking.append(values)
            row = row + 1

        no_of_packages_uom = False
        row = 34
        data_containers = []
        count_of_data_rows = self.get_data_rows(33, sheet, 'containers')
        for i in range(count_of_data_rows):
            values = {
                "container_no": sheet.cell_value(row, 0),
                "seal_no": sheet.cell_value(row, 2),
                "no_of_packages": sheet.cell_value(row, 3),
                "no_of_packages_uom": sheet.cell_value(row, 4),
                "gross_weight": sheet.cell_value(row, 5),
                "volume": sheet.cell_value(row, 7),
            }
            data_containers.append(values)
            row = row + 1

        if len(data_containers) > len(data_marking):
            # for container_line in data_containers:
            for x, container_line in enumerate(data_containers):
                if si.cargo_type == 'fcl':
                    si_line_obj = self.env['freight.website.si.fcl']
                    si_line = si_line_obj.create({
                        'container_product_name': data_marking[x].get('description') if x < len(data_marking) else False,
                        'fcl_line': si.id or '',
                        'container_no': container_line.get('container_no') or '',
                        'seal_no': container_line.get('seal_no') or '',
                        'packages_no': container_line.get('no_of_packages') or 0.0,
                        'packages_no_uom': no_of_packages_uom.id if no_of_packages_uom else False,
                        'exp_gross_weight': container_line.get('gross_weight') or 0.0,
                        'exp_vol': container_line.get('volume') or 0.0,
                        'remark': data_marking[x].get('marking') if x < len(data_marking) else False,
                    })
                    si.write({'fcl_line_ids': si_line or False})
                else:
                    si_line_obj = self.env['freight.website.si.lcl']
                    si_line = si_line_obj.create({
                        'container_product_name': data_marking[x].get('description') if x < len(data_marking) else False,
                        'lcl_line': si.id or '',
                        'container_no': container_line.get('container_no') or '',
                        'seal_no': container_line.get('seal_no') or '',
                        'packages_no': container_line.get('no_of_packages') or 0.0,
                        'packages_no_uom': no_of_packages_uom.id if no_of_packages_uom else False,
                        'exp_gross_weight': container_line.get('gross_weight') or 0.0,
                        'exp_vol': container_line.get('volume') or 0.0,
                        'remark': data_marking[x].get('marking') if x < len(data_marking) else False,
                    })
                    si.write({'lcl_line_ids': si_line or False})


    def get_data_rows(self, header_row, sheet, section_flag):
        # header_row = header
        col1_index = 0
        # col2_index = 2
        count_of_data_rows = 0
        # num_col2_data = 0
        for row in range(header_row + 1, sheet.nrows):
            col1_value = sheet.cell_value(row, col1_index)
            # col2_value = sheet.cell_value(row, col2_index)
            if col1_value == 'Container No.' or col1_value == 'NOTE :':
                break
            if section_flag=='marking':
                if col1_value != '' or sheet.cell_value(row, 2) != '':
                    count_of_data_rows += 1
            elif section_flag == 'containers':
                if col1_value != '' or sheet.cell_value(row, 2) != '' or sheet.cell_value(row, 3) != '' or \
                        sheet.cell_value(row, 5) != '' or sheet.cell_value(row, 7) != '':
                    count_of_data_rows += 1
            # if col2_value != '':
            #     num_col2_data += 1
        print(f"Number of data in column 0: {count_of_data_rows}")
        return count_of_data_rows



# OLD CODE COMMENTED

        #
        # marking = ''
        # description = ''
        # container_no = ''
        # seal_no = ''
        # no_of_packages =0
        # no_of_packages_uom = False
        # gross_weight = 0
        # volume = 0
        # if sheet.cell_value(23, 0) and len(sheet.cell_value(23, 0))>0:
        #     marking = sheet.cell_value(23, 0)
        # if sheet.cell_value(23, 2) and len(sheet.cell_value(23, 2))>0:
        #     description = sheet.cell_value(23, 2)
        # if sheet.cell_value(34, 0) and len(sheet.cell_value(34, 0))>0:
        #     container_no = sheet.cell_value(34, 0)
        # if sheet.cell_value(34, 2) and len(sheet.cell_value(34, 2))>0:
        #     seal_no = sheet.cell_value(34, 2)
        # if sheet.cell_value(34, 3) and sheet.cell_value(34, 3)>0:
        #     no_of_packages = sheet.cell_value(34, 3)
        # if sheet.cell_value(34, 4) and len(sheet.cell_value(34, 4))>0:
        #     uom = sheet.cell_value(34, 4)
        #     no_of_packages_uom = self.env['uom.uom'].search([('name', '=ilike', uom),], limit=1)
        # if sheet.cell_value(34, 5) and sheet.cell_value(34, 5)>0:
        #     gross_weight = sheet.cell_value(34, 5)
        # if sheet.cell_value(34, 7) and sheet.cell_value(34, 7)>0:
        #     volume = sheet.cell_value(34, 7)
        # if si.cargo_type == 'fcl':
        #     si_line_obj = self.env['freight.website.si.fcl']
        #     si_line = si_line_obj.create({
        #         #'container_product_id': line.container_product_id.id or False,
        #         'container_product_name': description or False,
        #         #'container_commodity_id': line.container_commodity_id.id or False,
        #         'fcl_line': si.id or '',
        #         'container_no': container_no or '',
        #         'seal_no': seal_no or '',
        #         #'fcl_container_qty': line.fcl_container_qty,
        #         'packages_no': no_of_packages or 0.0,
        #         'packages_no_uom': no_of_packages_uom.id if no_of_packages_uom else False,
        #         'exp_gross_weight': gross_weight or 0.0,
        #         #'exp_net_weight': line.exp_net_weight or 0.0,
        #         'exp_vol': volume or 0.0,
        #         'remark': marking or '',
        #     })
        #     si.write({'fcl_line_ids': si_line or False})
        # else:
        #     si_line_obj = self.env['freight.website.si.lcl']
        #     si_line = si_line_obj.create({
        #         # 'container_id': line.container_product_id.id or False,
        #         'container_product_name': description or False,
        #         #'container_product_id': line.container_commodity_id.id or False,
        #         'lcl_line': si.id or '',
        #         'container_no': container_no or '',
        #         # 'container_product_name': line.freight_currency.id,
        #         'packages_no': no_of_packages or 0.0,
        #         'packages_no_uom': no_of_packages_uom.id or False,
        #         'exp_gross_weight': gross_weight or 0.0,
        #         #'exp_net_weight': line.exp_net_weight or 0.0,
        #         'exp_vol': volume or 0.0,
        #         'remark': marking or '',
        #     })
        #     si.write({'lcl_line_ids': si_line or False})
        #
        #
        #         # if col == 6 and row == 19:
        #         #     si.place_of_delivery = sheet.cell_value(row, col)
        #
        #
        #
        #
