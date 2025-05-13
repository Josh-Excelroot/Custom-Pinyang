from odoo import fields, models


class FreightBolInherit(models.TransientModel):
    _inherit = 'si.upload.wizard'

    data = fields.Binary()

    def export_manifest(self):
        data = {
            'active_record_id': self._context.get('active_id'),
        }
        # record = self.env["freight.website.si"].browse(self._context.get('active_id'))
        return self.env.ref('sci_goexcel_freight_2.action_si_report_excel').report_action(self, data)


class AssetXlsxReport(models.AbstractModel):
    _name = 'report.sci_goexcel_freight_2.report_si_data_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        domain = []
        record = self.env["freight.website.si"].browse(data.get('active_record_id'))
        sheet = workbook.add_worksheet('Excel Report')
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fffbed', 'border': True})
        title = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 20, 'bg_color': '#f2eee4', 'border': True})
        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        cell_format = workbook.add_format({'border': False})
        cell_format_heading = workbook.add_format({'border': False, 'color': 'red'})



        sheet.merge_range('A1:I1', 'SHIPPING INSTRUCTION FOR DOCUMENTATION', title)

        sheet.write('A2', 'Shipper', cell_format_heading)
        # sheet.merge_range('A3:A7', 'Shipper')
        sheet.merge_range('B2:C2', '%s' %(record.shipper), cell_format)
        sheet.merge_range('B3:C3', '', cell_format)
        sheet.merge_range('B4:C4', '', cell_format)
        sheet.merge_range('B5:C5', '', cell_format)
        sheet.merge_range('B6:C6', '', cell_format)
        sheet.merge_range('B7:C7', '', cell_format)
        sheet.merge_range('D2:E2', 'Booking No.', cell_format_heading)
        sheet.merge_range('F2:I2', '%s' %(record.carrier_booking_ref), cell_format)
        sheet.write('D3', 'Following please indicate "X" if required')
        sheet.write('E4', 'Original Bill of Lading')
        sheet.write('D7', 'Place of BL issue:')

        sheet.write('A8', 'Consignee', cell_format_heading)
        sheet.merge_range('A9:A13', '')
        sheet.merge_range('B8:C8', '%s' %(record.consignee), cell_format)
        sheet.merge_range('B9:C9', '', cell_format)
        sheet.merge_range('B10:C10', '', cell_format)
        sheet.merge_range('B11:C11', '', cell_format)
        sheet.merge_range('B12:C12', '', cell_format)
        sheet.merge_range('B13:C13', '', cell_format)
        sheet.write('E8', 'PKG')
        sheet.write('G8', 'PEN')
        sheet.write('I8', 'PGU')
        sheet.write('D9', 'Other (please indicate):')
        sheet.merge_range('D10:G11', 'If place of BL issue & payment is different, please indicate place of payment:', cell_format)
        sheet.merge_range('H10:I11', '', cell_format_heading)
        sheet.merge_range('D12:G13', 'For USA AUTO-NVOCC please indicate SCAC Code:', cell_format_heading)
        sheet.merge_range('H12:I13', '', cell_format_heading)
        sheet.merge_range('D14:G15', 'Commodity Code (H.S.Code) :', cell_format_heading)
        sheet.merge_range('H14:I15', '%s' %(record.commodity), cell_format_heading)
        sheet.merge_range('D16:I16', 'Special/other request:', cell_format)
        sheet.merge_range('D17:I17', '%s' %(record.note), cell_format)
        sheet.merge_range('D18:I18', '', cell_format)
        sheet.merge_range('D19:I19', '', cell_format)

        sheet.write('A14', 'Notify Party', cell_format_heading)
        sheet.merge_range('A15:A19', '%s' %(record.notify_party), cell_format_heading)
        sheet.merge_range('B14:C14', '', cell_format)
        sheet.merge_range('B15:C15', '', cell_format)
        sheet.merge_range('B16:C16', '', cell_format)
        sheet.merge_range('B17:C17', '', cell_format)
        sheet.merge_range('B18:C18', '', cell_format)
        sheet.merge_range('B19:C19', '', cell_format)

        sheet.merge_range('A20:B20', 'Precarried vessel/voyage:', cell_format_heading)
        sheet.write('C20','%s' %(record.voyage_no))
        sheet.merge_range('D20:F20', 'Vessel/Voyage:', cell_format_heading)
        sheet.merge_range('G20:I20', '%s' %(record.vessel), cell_format)
        sheet.merge_range('A21:B21', 'Place of Receipt:', cell_format_heading)
        sheet.write('C21', '%s' % (record.place_of_receipt))
        sheet.merge_range('D21:F21', 'Port of Loading :', cell_format_heading)
        sheet.merge_range('G21:I21', '%s' % (record.port_of_loading_input.name), cell_format)
        sheet.merge_range('A22:B22', 'Port of Discharge:', cell_format_heading)
        sheet.write('C22', '%s' % (record.port_of_discharge_input.name))
        sheet.merge_range('D22:F22', 'Place of Delivery:', cell_format_heading)
        sheet.merge_range('G22:I22', '%s' % (record.place_of_delivery), cell_format)

        sheet.merge_range('A23:B23', 'Marking', cell_format_heading)
        sheet.merge_range('C23:I23', 'Description of Goods', cell_format_heading)
        row = 24
        for i in range(24, 34):
            sheet.merge_range('A%s:B%s' % (i, i), '', cell_format_heading)
            sheet.merge_range('C%s:I%s' % (i, i), '', cell_format_heading)

        sheet.merge_range('A34:B34', 'Container No.', cell_format_heading)
        sheet.write('C34', 'Seal No.', cell_format_heading)
        sheet.write('D34', 'No of Packages', cell_format_heading)
        sheet.write('E34', 'Type of Packages', cell_format_heading)
        sheet.merge_range('F34:G34', 'Gross Weight (KGS)', cell_format_heading)
        sheet.merge_range('H34:I34', 'Measurement (M3)', cell_format_heading)
        row = 35
        for i in range(35,45):
            sheet.merge_range('A%s:B%s' %(i, i), '', cell_format)
            sheet.merge_range('F%s:G%s' %(i, i), '', cell_format)
            sheet.merge_range('H%s:I%s' %(i, i), '', cell_format)

        sheet.merge_range('A45:I45', 'NOTE:', cell_format)
        sheet.merge_range('A46:I46', 'ALL DOCUMENT MUST BE CHECK AND CONFIRMED BY US BEFORE FINAL B/L IS ISSUED.', cell_format)
        sheet.merge_range('A47:I47', 'WE NEED TO RECEIVE THE FULL PRE-ALERT 2DAYS (48 HOURS- SEAFREIGHT) FOR MANIFEST PURPOSE.', cell_format)
        sheet.merge_range('A48:I48', 'ANY FAILURE IN COMPLYING TO THE LEAD TIMES FOR ADVANCE MANIFEST WILL INCUR CUSTOMS PENALTIES WHICH WE SHALL HOLD YOUR SIDE ACCOUNTABLE.', cell_format)
        sheet.merge_range('A49:I49', 'THANKS AND BEST REGARDS.', cell_format)
        sheet.merge_range('A50:I50', 'THE MANAGEMENT OF EASTWAY EXPRESS LINE SDN BHD', cell_format)




        # courses = self.env['openacademy.course'].search(domain)
        row = 3
        col = 1

        # Header row
        # sheet.set_column(0, 9, 30)
        # sheet.write(row, col, 'Regin', header_row_style)
        # # sheet.write(row, col+1, 'Start date', header_row_style)
        # sheet.write(row, col + 1, 'Contact', header_row_style)
        # sheet.write(row, col + 2, 'Value', header_row_style)
        # row += 2