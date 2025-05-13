from odoo import models


class ShippingInstructionBolXlsx(models.AbstractModel):
    _name = 'report.sci_goexcel_freight_2.report_si_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    # learn Xlsxwriter
    def generate_xlsx_report(self, workbook, data, lines):
        format1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': False, 'left': True, 'right': True})
        format2 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True,
                                       'left': True, 'right': True})
        header_format = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': True, 'top': True,
                                       'bottom': True, 'left': True, 'right': True})
        format_label = workbook.add_format({'font_size': 12, 'valign': 'top', 'bold': False,
                                           'left': True, 'right': True, 'text_wrap':True})
        format_label.set_font_color('red')
        format_label_2 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': False,
                                              'left': True, 'right': True})
        format_label_2.set_font_color('black')
        format_label_3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'left': True, 'right': True})
        format_label_3.set_font_color('black')
        format_label_4 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': False, 'left': True, 'right': True})
        format_label_4.set_font_color('black')
        format_label_5 = workbook.add_format({'font_size': 12, 'valign': 'top', 'bold': False, 'left': True, 'right': True, 'text_wrap':True})
        format_label_5.set_font_color('black')
        format_label_6 = workbook.add_format({'font_size': 12, 'valign': 'top', 'align': 'center', 'bold': False,
                                            'left': True, 'right': True, 'text_wrap':True})
        format_label_6.set_font_color('red')
        merge_format = workbook.add_format({'align': 'center'})
        merge_format_2 = workbook.add_format({'align': 'left'})
        worksheet_name = 'SI ' + lines.carrier_booking_no
        sheet = workbook.add_worksheet(worksheet_name)
        if lines.direction == 'export':
            #set column width (first column, last column, width)
            sheet.set_column(0, 0, 15)  #first column
            sheet.set_column(1, 1, 20)  #second column
            sheet.set_column(2, 2, 35)  #third column
            sheet.set_column(3, 8, 10)  #forth to 9th Column
            #Row 1
            #first row, first column, last row, last column, string to write, merge_format
            sheet.merge_range(0, 0, 0, 8, '', merge_format)
            #row,column
            sheet.write(0, 0, 'SHIPPING INSTRUCTION FOR DOCUMENTATION', header_format)
            #Row 2
            sheet.merge_range(1, 1, 1, 2, '', merge_format)
            sheet.merge_range(1, 3, 1, 4, '', merge_format)
            sheet.merge_range(1, 5, 1, 8, '', merge_format)
            sheet.merge_range(1, 0, 6, 0, '', merge_format)  #merge cell row 1-7
            sheet.write(1, 0, 'Shipper', format_label)
            #if lines.shipper_address_input:
                #print('>>>>>>Shipper=', lines.shipper_address_input)
            sheet.write(1, 1, "", format1)
            sheet.write(1, 3, 'Booking No.', format_label)
            if lines.carrier_booking_no:
                sheet.write(1, 5, lines.carrier_booking_no, format2)
            #Row 3
            sheet.merge_range(2, 1, 2, 2, '', merge_format)
            sheet.write(2, 1, "", format1)
            sheet.write(2, 3, 'Following please indicate "X" if required', format_label_4)
            #Row 4
            sheet.merge_range(3, 1, 3, 2, '', merge_format)
            sheet.write(3, 1, "", format1)
            sheet.write(3, 3, 'X', format_label_3)
            sheet.write(3, 4, 'Original Bill of Lading', format_label_2)
            sheet.write(3, 7, 'Sea Waybill', format_label_2)
            #Row 5
            sheet.merge_range(4, 1, 4, 2, '', merge_format)
            sheet.write(4, 1, "", format1)
            sheet.write(4, 3, '', format_label_2)
            sheet.write(4, 4, 'Freight Prepaid', format_label_2)
            sheet.write(4, 7, 'Freight Collect', format_label_2)
            #Row 6
            sheet.merge_range(5, 1, 5, 2, '', merge_format)
            sheet.write(5, 1, "", format1)
            sheet.write(5, 3, '', format_label_2)
            sheet.write(5, 4, 'Telex-Release', format_label_2)
            #Row 7
            sheet.merge_range(6, 1, 6, 2, '', merge_format)
            sheet.write(6, 1, "", format1)
            sheet.write(6, 3, 'Place of BL issue:', format_label_4)
            #Row 8
            sheet.merge_range(7, 1, 7, 2, '', merge_format)
            sheet.merge_range(8, 0, 12, 0, '', merge_format)  #merge cell 8 to 13
            sheet.write(7, 0, 'Consignee', format_label)
            sheet.write(7, 1, "", format1)
            #if lines.consignee_address_input:
            #    sheet.write(7, 1, lines.consignee_address_input, format1)
                #print('>>>>>>Consignee=', lines.consignee_address_input)
            sheet.write(7, 4, 'PKG', format_label_4)
            sheet.write(7, 6, 'PEN', format_label_4)
            sheet.write(7, 8, 'PGU', format_label_4)
            #Row 9
            sheet.merge_range(8, 1, 8, 2, '', merge_format)
            sheet.write(8, 1, "", format1)
            sheet.write(8, 3, 'Other (please indicate):', format_label_4)
            #Row 10
            sheet.merge_range(9, 1, 9, 2, '', merge_format)
            sheet.write(9, 1, "", format1)
            #sheet.merge_range(9, 3, 9, 6, '', merge_format)
            sheet.merge_range(9, 7, 10, 8, '', merge_format) #merge cell 8 to 13
            sheet.merge_range(9, 3, 10, 6, '', merge_format)  #merge row 9 to 10, merge column 3 to 6
            sheet.write(9, 3, 'If place of BL issue & payment is different, please indicate place of payment:', format_label_5)
            #Row 11
            sheet.merge_range(10, 1, 10, 2, '', merge_format)
            sheet.write(10, 1, "", format1)
            #Row 12
            sheet.merge_range(11, 1, 11, 2, '', merge_format)
            sheet.write(11, 1, "", format1)
            #sheet.merge_range(11, 3, 11, 6, '', merge_format)
            sheet.merge_range(11, 7, 12, 8, '', merge_format)
            sheet.merge_range(11, 3, 12, 6, '', merge_format)  #merge row 11 to 12, merge column 3 to 6
            sheet.write(11, 3, 'For USA AUTO-NVOCC please indicate SCAC Code:', format_label)
            #Row 13
            sheet.merge_range(12, 1, 12, 2, '', merge_format)
            sheet.write(12, 1, "", format1)
            #Row 14
            sheet.merge_range(13, 1, 13, 2, '', merge_format)
            sheet.write(13, 1, "", format1)
            sheet.merge_range(13, 7, 14, 8, '', merge_format)
            sheet.merge_range(13, 0, 18, 0, '', merge_format)  #merge cell 8 to 13
            sheet.merge_range(13, 3, 14, 6, '', merge_format)
            sheet.write(13, 0, 'Notify Party', format_label)
            #if lines.notify_party_address_input:
            #    sheet.write(13, 1, lines.notify_party_address_input, format1)
            sheet.write(13, 3, 'Commodity Code (H.S.Code) :', format_label)
            #Row 15
            sheet.merge_range(14, 1, 14, 2, '', merge_format)
            sheet.write(14, 1, "", format1)
            #Row 16
            sheet.merge_range(15, 1, 15, 2, '', merge_format)
            sheet.write(15, 1, "", format1)
            sheet.merge_range(15, 3, 15, 8, '', merge_format) #merge cell 8 to 13
            sheet.write(15, 3, 'Special/other request:', format_label_4)
            #Row 17
            sheet.merge_range(16, 1, 16, 2, '', merge_format)
            sheet.write(16, 1, "", format1)
            sheet.merge_range(16, 3, 16, 8, '', merge_format) #merge cell 8 to 13
            #Row 18
            sheet.merge_range(17, 1, 17, 2, '', merge_format)
            sheet.write(17, 1, "", format1)
            sheet.merge_range(17, 3, 17, 8, '', merge_format) #merge cell 8 to 13
            #Row 19
            sheet.merge_range(18, 1, 18, 2, '', merge_format)
            sheet.write(18, 1, "", format1)
            sheet.merge_range(18, 3, 18, 8, '', merge_format) #merge cell 8 to 13
            #Row 20
            sheet.merge_range(19, 0, 19, 1, '', merge_format)
            sheet.merge_range(19, 6, 19, 8, '', merge_format)
            sheet.merge_range(19, 3, 19, 5, '', merge_format)
            sheet.write(19, 0, 'Precarried vessel/voyage :', format_label)
            feeder_vessel_name = ''
            feeder_voyage_no = ''
            if lines.feeder_vessel_name:
                feeder_vessel_name = lines.feeder_vessel_name
            if lines.feeder_voyage_no:
                feeder_voyage_no = lines.feeder_voyage_no
            feeder_vessel_voyage = feeder_vessel_name + ' / ' + feeder_voyage_no
            if len(feeder_vessel_voyage) > 3:
                sheet.write(19, 2, feeder_vessel_voyage, format1)
            else:
                sheet.write(19, 2, '', format1)
            sheet.write(19, 3, 'Vessel/Voyage :', format_label)
            vessel_name = ''
            voyage_no = ''
            if lines.vessel_name:
                vessel_name = lines.vessel_name.name
            if lines.voyage_no:
                voyage_no = lines.voyage_no
            vessel_voyage = vessel_name + ' / ' + voyage_no
            if len(vessel_voyage) > 3:
                sheet.write(19, 6, vessel_voyage, format1)
            else:
                sheet.write(19, 6, '', format1)
            #Row 21
            sheet.merge_range(20, 0, 20, 1, '', merge_format)
            sheet.merge_range(20, 6, 20, 8, '', merge_format)
            sheet.merge_range(20, 3, 20, 5, '', merge_format)
            sheet.write(20, 0, 'Place of Receipt :', format_label)
            if lines.place_of_receipt:
                sheet.write(20, 2, lines.place_of_receipt, format1)
            sheet.write(20, 3, 'Port of Loading :', format_label)
            if lines.port_of_loading:
                sheet.write(20, 6, lines.port_of_loading.name, format1)
            #Row 22
            sheet.merge_range(21, 0, 21, 1, '', merge_format)
            sheet.merge_range(21, 6, 21, 8, '', merge_format)
            sheet.merge_range(21, 3, 21, 5, '', merge_format)
            sheet.write(21, 0, 'Port of Discharge :', format_label)
            if lines.port_of_discharge:
                sheet.write(21, 2, lines.port_of_discharge.name, format1)
            sheet.write(21, 3, 'Place of Delivery :', format_label)
            if lines.place_of_delivery:
                sheet.write(21, 6, lines.place_of_delivery, format1)
            else:
                sheet.write(21, 6, '', format1)
            #Row 23
            sheet.merge_range(22, 0, 22, 1, '', merge_format)
            sheet.merge_range(22, 2, 22, 8, '', merge_format)
            sheet.write(22, 0, 'Marking', format_label_6)
            sheet.write(22, 2, 'Description of Goods', format_label_6)
            #Row 24
            sheet.merge_range(23, 0, 23, 1, '', merge_format)
            sheet.merge_range(23, 2, 23, 8, '', merge_format)
            #Row 25
            sheet.merge_range(24, 0, 24, 1, '', merge_format)
            sheet.merge_range(24, 2, 24, 8, '', merge_format)
            #Row 26
            sheet.merge_range(25, 0, 25, 1, '', merge_format)
            sheet.merge_range(25, 2, 25, 8, '', merge_format)
            #Row 27
            sheet.merge_range(26, 0, 26, 1, '', merge_format)
            sheet.merge_range(26, 2, 26, 8, '', merge_format)
            #Row 28
            sheet.merge_range(27, 0, 27, 1, '', merge_format)
            sheet.merge_range(27, 2, 27, 8, '', merge_format)
            #Row 29
            sheet.merge_range(28, 0, 28, 1, '', merge_format)
            sheet.merge_range(28, 2, 28, 8, '', merge_format)
            #Row 30
            sheet.merge_range(29, 0, 29, 1, '', merge_format)
            sheet.merge_range(29, 2, 29, 8, '', merge_format)
            #Row 31
            sheet.merge_range(30, 0, 30, 1, '', merge_format)
            sheet.merge_range(30, 2, 30, 8, '', merge_format)
            #Row 32
            sheet.merge_range(31, 0, 31, 1, '', merge_format)
            sheet.merge_range(31, 2, 31, 8, '', merge_format)
            #Row 33
            sheet.merge_range(32, 0, 32, 1, '', merge_format)
            sheet.merge_range(32, 2, 32, 8, '', merge_format)
            #Row 34
            sheet.merge_range(33, 0, 33, 1, '', merge_format)
            sheet.merge_range(33, 2, 33, 2, '', merge_format)
            sheet.merge_range(33, 3, 33, 4, '', merge_format)
            sheet.merge_range(33, 5, 33, 6, '', merge_format)
            sheet.merge_range(33, 7, 33, 8, '', merge_format)
            sheet.write(33, 0, 'Container No.', format_label_6)
            sheet.write(33, 2, 'Seal No.', format_label_6)
            sheet.write(33, 3, 'No of Packages', format_label_6)
            sheet.write(33, 5, 'Gross Weight (KGS)', format_label_6)
            sheet.write(33, 7, 'Measurement (M3)', format_label_6)
            #Row 35
            sheet.merge_range(34, 0, 34, 1, '', merge_format)
            sheet.merge_range(34, 2, 34, 2, '', merge_format)
            sheet.merge_range(34, 5, 34, 6, '', merge_format)
            sheet.merge_range(34, 7, 34, 8, '', merge_format)
            #Row 36
            sheet.merge_range(35, 0, 35, 1, '', merge_format)
            sheet.merge_range(35, 2, 35, 2, '', merge_format)
            sheet.merge_range(35, 5, 35, 6, '', merge_format)
            sheet.merge_range(35, 7, 35, 8, '', merge_format)
            #Row 37
            sheet.merge_range(36, 0, 36, 1, '', merge_format)
            sheet.merge_range(36, 2, 36, 2, '', merge_format)
            sheet.merge_range(36, 5, 36, 6, '', merge_format)
            sheet.merge_range(36, 7, 36, 8, '', merge_format)
            #Row 38
            sheet.merge_range(37, 0, 37, 1, '', merge_format)
            sheet.merge_range(37, 2, 37, 2, '', merge_format)
            sheet.merge_range(37, 5, 37, 6, '', merge_format)
            sheet.merge_range(37, 7, 37, 8, '', merge_format)
            #Row 39
            sheet.merge_range(38, 0, 38, 1, '', merge_format)
            sheet.merge_range(38, 2, 38, 2, '', merge_format)
            sheet.merge_range(38, 5, 38, 6, '', merge_format)
            sheet.merge_range(38, 7, 38, 8, '', merge_format)
            #Row 40
            sheet.merge_range(39, 0, 39, 1, '', merge_format)
            sheet.merge_range(39, 2, 39, 2, '', merge_format)
            sheet.merge_range(39, 5, 39, 6, '', merge_format)
            sheet.merge_range(39, 7, 39, 8, '', merge_format)
            #Row 41
            sheet.merge_range(40, 0, 40, 1, '', merge_format)
            sheet.merge_range(40, 2, 40, 2, '', merge_format)
            sheet.merge_range(40, 5, 40, 6, '', merge_format)
            sheet.merge_range(40, 7, 40, 8, '', merge_format)
            #Row 42
            sheet.merge_range(41, 0, 41, 1, '', merge_format)
            sheet.merge_range(41, 2, 41, 2, '', merge_format)
            sheet.merge_range(41, 5, 41, 6, '', merge_format)
            sheet.merge_range(41, 7, 41, 8, '', merge_format)
            #Row 43
            sheet.merge_range(42, 0, 42, 1, '', merge_format)
            sheet.merge_range(42, 2, 42, 2, '', merge_format)
            sheet.merge_range(42, 5, 42, 6, '', merge_format)
            sheet.merge_range(42, 7, 42, 8, '', merge_format)
            #Row 44
            sheet.merge_range(43, 0, 43, 1, '', merge_format)
            sheet.merge_range(43, 2, 43, 2, '', merge_format)
            sheet.merge_range(43, 5, 43, 6, '', merge_format)
            sheet.merge_range(43, 7, 43, 8, '', merge_format)
            #Row 45
            sheet.merge_range(44, 0, 44, 8, 'NOTE :', merge_format_2)
            sheet.merge_range(45, 0, 45, 8, 'ALL DOCUMENT MUST BE CHECK AND CONFIRMED BY US BEFORE FINAL B/L IS ISSUED.', merge_format_2)
            sheet.merge_range(46, 0, 46, 8, 'WE NEED TO RECEIVE THE FULL PRE-ALERT 2DAYS (48 HOURS- SEAFREIGHT) FOR MANIFEST PURPOSE.', merge_format_2)
            sheet.merge_range(47, 0, 47, 8, 'ANY FAILURE IN COMPLYING TO THE LEAD TIMES FOR ADVANCE MANIFEST WILL INCUR CUSTOMS PENALTIES WHICH WE SHALL HOLD YOUR SIDE ACCOUNTABLE.', merge_format_2)
            sheet.merge_range(48, 0, 48, 8, 'THANKS AND BEST REGARDS.', merge_format_2)
            sheet.merge_range(49, 0, 49, 8, 'THE MANAGEMENT OF ' + lines.company_id.name, merge_format_2)


