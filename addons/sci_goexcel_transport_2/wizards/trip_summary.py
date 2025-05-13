from datetime import date, datetime

import pytz
from odoo import api, fields, models


class TransportSummaryWizard(models.TransientModel):
    _name = "trip.summary.wizard"

    @api.model
    def action_create(self, fields):
        pass

    @api.multi
    def write(self, vals):
        res = super(TransportSummaryWizard, self).write(vals)
        return res

    @api.model
    def _get_summary(self):
        j = 1
        check = 0
        summary = ''
        active_id = self._context.get('active_id')
        if active_id:
            transport = self.env['transport.rft'].browse(int(active_id))
            fleet = self.env['dispatch.trip'].search([('rft_reference', '=', transport.id), ])
            today = date.today()
            header_date = transport.required_date_time
            # print('>>>> _get_summary commodity 1=', transport.commodity1)
            if transport.rft_no:
                summary += transport.rft_no + "\n\n"
            if transport.commodity1:
                # print('>>>> _get_summary commodity 2=', transport.commodity1)
                summary += str(transport.commodity1) or " " + "\n"
            else:
                # print('>>>> _get_summary commodity 3=', transport.commodity1)
                summary += ''
            if header_date:
                summary += str(transport.required_date_time.strftime("%d-%m-%Y")) + "\n\n"

            if transport.driver_id.display_name:
                summary += 'Truck 1 :'
                summary += str(transport.driver_id.display_name) + "\n"

            if transport.vehicle.license_plate:
                summary += 'Vehicle No :'
                summary += str(transport.vehicle.license_plate) + "//"

            if check == 0:
                if transport.temperature_set_point:
                    summary += str(transport.temperature_set_point)
                    summary += '°C' + "\n"
                    check = 2
            if transport.driver_id.identification_no:
                summary += 'IC/Passport : '
                summary += str(transport.driver_id.identification_no)
                if transport.driver_id.passport_no:
                    summary += '//' + str(transport.driver_id.passport_no)+"\n"
                else:
                    summary += '//' + 'N/A' + "\n"
            if transport.driver_id.mobile:
                summary += 'HP No : '
                summary += str(transport.driver_id.mobile) + "\n" + "\n"
            # print("Customer ", browse_id.pickup_from.commercial_company_name)
            # summary += transport.pickup_from.commercial_company_name + "\n"
            # print("Address", browse_id.pickup_from_address_input)
            if transport.pickup_from_address_input:
                summary += str(transport.pickup_from_address_input) + "\n"
            if transport.required_date_time:
                print('/////////////////////////////////// REQ DATE TIME:', transport.required_date_time)
                # now_utc = transport.required_date_time(pytz.UTC)

                now = datetime.strftime(fields.Datetime.context_timestamp(self, transport.required_date_time),
                                        "%d-%m-%Y %H:%M:%S")
                summary += 'Loading - '
                summary += str(now) + "\n"

                # now_user = now_utc.astimezone(pytz.timezone(self.env.user.tz or 'UTC'))

                print('////////////////////// NOW : ', now)
                # print('////////////////////// NOW USER : ', now_user)
            #     summary += 'Loading - '
            #     summary += str(transport.required_date_time.strftime("%d-%m-%Y %H:%M:%S")) + "\n\n"
            # # if transport.temperature_set_point:
            #     summary += 'Temperature :'
            #     summary += str(transport.temperature_set_point) + "\n"

            if transport.container_line_ids:
                count = 1
                delivery_to = 1
                for i in transport.container_line_ids:

                    # Loading Details

                    if i.pickup_from_address.display_name:
                        summary += "\n"
                        summary += str(count) + ')' "Loading From :\n" + "\n"
                        count = count + 1
                        summary += str(i.pickup_from_address.display_name) + "\n"
                    if i.pickup_from_address.contact_address:
                        summary += str(i.pickup_from_address.street) + "\n" + "\n"
                    # if i.pickup_from_address.street :
                    #     summary += str(i.pickup_from_address.city)
                    # if i.pickup_from_address.country_id :
                    #     summary += str(i.pickup_from_address.country_id )
                    if i.loading_pic:
                        summary += 'PIC : '
                        summary += str(i.loading_pic) + "\n"

                    if i.accept_hour_line.display_name:
                        summary += 'Accept Hours :'
                        summary += str(i.accept_hour_line.display_name) + "\n"

                    if i.packages_no:
                        summary += 'Quantity :'
                        summary += str(i.packages_no) + "\n"
                    # if transport.temperature_set_point:
                    #     summary += 'Temperature :'
                    #     summary += str(transport.temperature_set_point) + "\n"
                    if transport.delivery_instruction:
                        summary += 'Delivery Instruction' + "\n"
                        summary += str(transport.delivery_instruction) + "\n" + "\n"
                    # Delivery Details

                    if i.delivery_to_address.display_name:
                        # summary += "\n"
                        if delivery_to == 1:
                            summary += str(delivery_to) + ')' + "Delivery To: \n"
                        else:
                            summary += "\n" + str(delivery_to) + ')' + "Delivery To: \n"
                        summary += "\n"
                        delivery_to = delivery_to + 1
                        summary += str(i.delivery_to_address.display_name) + "\n"
                    if i.delivery_to_address.street:
                        summary += str(i.delivery_to_address.street) + "\n"
                    if i.delivery_to_address.street2:
                        summary += str(i.delivery_to_address.street2) + "\n"
                    if i.delivery_to_address.city:
                        summary += str(i.delivery_to_address.city) + "\n"
                    summary += "\n"
                    if i.delivery_pic:
                        summary += 'PIC : '
                        summary += str(i.delivery_pic) + "\n"

                    # if i.accept_hour_line.display_name:
                    #     summary += 'Accept Hours :'
                    #     summary += str(i.accept_hour_line.display_name) + "\n"
                    #
                    # if i.packages_no:
                    #     summary += 'Quantity :'
                    #     summary += str(i.packages_no) + "\n"
                    # if transport.temperature_set_point:
                    #     summary += 'Temperature :'
                    #     summary += str(transport.temperature_set_point) + "\n"
            else:

                if transport.delivery_to.display_name:
                    # summary += "\n"
                    summary += str(transport.delivery_to.display_name)
                if transport.delivery_to_address_input:
                    summary += str(transport.delivery_to_address_input)
                if transport.delivery_to_contact_name.name:
                    summary += 'PIC : '
                    summary += str(transport.delivery_to_contact_name.name) + "\n"
                if transport.delivery_to_contact_name.phone:
                    summary += 'Phone : '
                    summary += str(transport.delivery_to_contact_name.phone) + "\n"
                if transport.accept_hour.display_name:
                    summary += 'Accept Hours :'
                    summary += str(transport.accept_hour.display_name) + "\n"
                # if transport.temperature_set_point:
                #     summary += 'Temperature :'
                #     summary += str(transport.temperature_set_point) + "\n"
            return summary

    summary = fields.Text(string=' Transport Summary', default=_get_summary)
