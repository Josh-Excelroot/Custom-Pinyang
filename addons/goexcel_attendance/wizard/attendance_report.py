# 1. Standard library imports
import base64
import csv
from io import StringIO
# 2. Known third party imports (One per line sorted and split in python stdlib)
# 3. Odoo imports (odoo)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# 4. Imports from Odoo modules (rarely, and only if necessary)
# 5. Local imports in the relative form
# 6. Unknown third party imports (One per line sorted and split in python stdlib)

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report'

    attendance_sheet = fields.Many2many(comodel_name='hr.attendance.sheet', required=True)

    def create_report(self):
        # Create a CSV buffer to write data into
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        # Define the header row for the CSV file

        # Write the header row to the CSV file

        # Iterate through attendance records and write data
        for sheet in self.attendance_sheet:
            for attendance_line in sheet.attendance_sheet_ids:
                sheet_title = f'{sheet.employee_id.name} Attendance Sheet From {sheet.date_from} To {sheet.date_to}'
                csv_writer.writerow([sheet_title])
                header = ['Date', 'Check-In', 'Check-Out', 'Overtime', 'Difference Time', 'Status']
                csv_writer.writerow(header)
                date = attendance_line.date
                check_in = attendance_line.asignin
                check_out = attendance_line.asignout
                overtime = attendance_line.overtime
                diff_time = attendance_line.difftime
                total_attendance = attendance_line.total_attendance
                status = attendance_line.status

                # Write data for each attendance line
                csv_writer.writerow([date, check_in, check_out, overtime, diff_time, total_attendance, status])
                csv_writer.writerow()

        # Move the cursor to the beginning of the buffer
        csv_buffer.seek(0)

        # Create a binary file and store the CSV data in it
        report_data = csv_buffer.read().encode()
        csv_buffer.close()
        print('report_data')
        print(report_data)

        # Create a record for the CSV file in Odoo
        report = self.env['ir.attachment'].create({
            'name': 'attendance_report.csv',
            'type': 'binary',
            'datas': base64.b64encode(report_data),
            'datas_fname': 'attendance_report.csv',
        })

        # Return an action to open or download the CSV file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{report.id}?download=true',
            'target': 'self',
        }