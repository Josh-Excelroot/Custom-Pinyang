from odoo import api, fields, models
import datetime
import calendar
from dateutil.relativedelta import *
import logging
_logger = logging.getLogger(__name__)


class RescheduleSailing(models.TransientModel):
    _name = "reschedule.sailing"

    booking_date = fields.Date(string='ETA/ETD Date')
    carrier_booking_no = fields.Char(string='Carrier Booking No', track_visibility='onchange')
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', track_visibility='onchange')
    voyage_no = fields.Char(string='Voyage No', track_visibility='onchange')
    booking_no = fields.Char(string='Job No', track_visibility='onchange')
    res_booking_date = fields.Date(string='New ETA/ETD Date')
    res_carrier_booking_no = fields.Char(string='New Carrier Booking No', track_visibility='onchange')
    res_vessel_name = fields.Many2one('freight.vessels', string='New Vessel Name', track_visibility='onchange')
    res_voyage_no = fields.Char(string='New Voyage No', track_visibility='onchange')
    res_feeder_vessel_name = fields.Char(string='New Feeder Vessel', track_visibility='onchange')
    res_feeder_voyage_no = fields.Char(string='New Feeder Voy. No', track_visibility='onchange')
    res_vessel_id = fields.Char(string='Vessel ID', track_visibility='onchange')
    res_pol_eta = fields.Date(string='Loading ETA')
    res_pod_eta = fields.Date(string='Discharge ETA')
    res_place_of_delivery_eta = fields.Date(string='Place of Delivery ETA')
    res_shipment_close_date_time = fields.Datetime(string='Closing Date Time')

    job_line_ids = fields.One2many('schedule.booking.line', 'reschedule_job_line_id',string="Jobs")

    contact_person = fields.Many2one('res.partner', string='Contact Person')

    @api.multi
    def update_job(self):

        for operation in self:
            #print('>>>>>>> update_job 1 >>>>>>>>>>>')
            if operation.booking_date or operation.voyage_no:
                # domain = [('shipment_booking_status', '!=', '09')]
                # if operation.booking_date:
                #     domain.append(('booking_date_time', '=', operation.booking_date))
                # # if self.vessel_name:
                # #     domain.append(('vessel_name', '=', self.vessel_name.id))
                # if operation.voyage_no:
                #     domain.append(('voyage_no', '=', operation.voyage_no))
                # if operation.port_of_loading:
                #     domain.append(('port_of_loading', '=', operation.port_of_loading.id))
                # booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
                #print('>>>>>>> update_job 1 >>>>>>>>>>>')
                for job in operation.job_line_ids:
                    #print('>>>>>>> update_job 2 >>>>>>>>>>>', job)
                    if job.add:
                        lines = []
                        #line = self.env['schedule.booking.line'].search([('id', '=', job.id)], limit=1)
                        #print('line booking_no=', line.booking_no)
                        #print('c. booking no=', job.carrier_booking_no)
                        # print('job booking no=', job.booking_no, ', carrier no=', job.carrier_booking_no, ' , eta=',
                        #       job.booking_date)
                        booking_job = self.env['freight.booking'].search([('booking_no', '=', job.booking_no)], limit=1)
                        #print('booking_job booking no=', booking_job.carrier_booking_no)
                        if operation.res_booking_date:
                            booking_job.booking_date_time = operation.res_booking_date
                            if booking_job.booking_id:
                                booking_job.booking_id.booking_date = operation.res_booking_date
                        if operation.res_vessel_name:
                            booking_job.vessel_name = operation.res_vessel_name.id
                            if booking_job.booking_id:
                                booking_job.booking_id.vessel_name = operation.res_vessel_name.id
                        if operation.res_voyage_no:
                            booking_job.voyage_no = operation.res_voyage_no
                            if booking_job.booking_id:
                                booking_job.booking_id.voyage_no = operation.res_voyage_no
                        if operation.res_vessel_id:
                            booking_job.vessel_id = operation.res_vessel_id
                            if booking_job.booking_id:
                                booking_job.booking_id.vessel_id = operation.res_vessel_id
                        if operation.res_feeder_vessel_name:
                            booking_job.feeder_vessel_name = operation.res_feeder_vessel_name
                        if operation.res_feeder_voyage_no:
                            booking_job.feeder_voyage_no = operation.res_feeder_voyage_no
                        if operation.res_pol_eta:
                            booking_job.port_of_loading_eta_2 = operation.res_pol_eta
                        if operation.res_pod_eta:
                            booking_job.port_of_discharge_eta = operation.res_pod_eta
                            if booking_job.booking_id:
                                booking_job.booking_id.port_of_discharge_eta = operation.res_pod_eta
                        if operation.res_place_of_delivery_eta:
                            booking_job.place_of_delivery_eta = operation.res_place_of_delivery_eta
                        if operation.res_shipment_close_date_time:
                            booking_job.shipment_close_date_time = operation.res_shipment_close_date_time
                            booking_job.intended_cy_cut_off = operation.res_shipment_close_date_time

                    #booking_job.booking_log_lines_ids = lines


    @api.multi
    def update_send_email(self):
        self.ensure_one()
        self.update_job()
        for line in self.job_line_ids:
            if line.contact_person:
                self.contact_person = line.contact_person.id
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('goexcel_sailing_reschedule', 'email_template_resailing_reschedule')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'reschedule.sailing',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            #'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

        # if self.port_of_loading:
        #     if self.availability == 'available':
        #         bookings = self.env['freight.multimodal.transport'].search([
        #             ('booking_date', '>=', self.eta_date_from),
        #             ('booking_date', '<=', self.eta_date_to),
        #             ('port_of_loading', '=', self.port_of_loading.id),
        #             ('direction', '=', self.shipment_type),
        #             ('balance_container', '!=', 0),
        #         ])
        #
        # datas = {
        #     'form': bookings.ids,
        # }
        #
        # ir_model_data = self.env['ir.model.data']
        # try:
        #     template_id = \
        #         ir_model_data.get_object_reference('custom_bhl', 'email_template_RescheduleSailing')[1]
        # except ValueError:
        #     template_id = False
        # try:
        #     compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        # except ValueError:
        #     compose_form_id = False
        #
        # partner_ids = self.env['res.partner'].browse(self._context.get('active_ids'))
        # ctx = {
        #     'default_model': 'reschedule.sailing',
        #     'default_res_id': self.ids[0],
        #     'data': datas,
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'mark_so_as_sent': True,
        #     'custom_layout': "mail.mail_notification_light",
        #     'force_email': True,
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }



    # @api.multi
    # def action_search_related_job(self):
    #     for job in self:
    #         domain = [('shipment_booking_status', '!=', '09')]
    #         if job.booking_date:
    #             domain.append(('booking_date_time', '==', job.booking_date))
    #         if job.vessel_name:
    #             domain.append(('vessel_name', '=', job.vessel_name.id))
    #         if job.voyage_no:
    #             domain.append(('voyage_no', '=', job.voyage_no))
    #         # if job.vessel_name:
    #         #     domain.append(('vessel_name', '==', job.vessel_name))
    #         booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
    #         if booking_jobs:
    #             booking_list = []
    #             lines = []
    #             for booking_job in booking_jobs:
    #                 #print('>>>>>>>> Before Insert= ', booking_job.booking_no)
    #                 #booking_list = {
    #                 booking_list.append({
    #                     'reschedule_job_line_id': booking_job.id,
    #                     'carrier_booking_no': booking_job.carrier_booking_no,
    #                     'booking_date': booking_job.booking_date_time,
    #                     'booking_no': booking_job.booking_no,
    #                     'port_of_discharge': booking_job.port_of_discharge.id,
    #                     'port_of_loading': booking_job.port_of_loading.id,
    #                     'vessel_name': booking_job.vessel_name.id,
    #                     'voyage_no': booking_job.voyage_no,
    #                     'customer': booking_job.customer_name.id,
    #                     'shipper': booking_job.shipper.id,
    #                     'consignee': booking_job.consignee.id,
    #                     'booking_status': booking_job.shipment_booking_status,
    #                 })
    #             print('>>>>>>>> Before Insert')
    #             job['job_line_ids'] = booking_list
    #             job = self._convert_to_write(job)
    #             #job.job_line_ids = [(0, 0, booking_list)]
    #             print('>>>>>>>> After Insert')
    #             # lines.append(booking_list)
    #             # job.job_line_ids = lines
    #                 #print('>>>>> action_search_related_job=', booking_job.booking_date_time)
    #             #     booking_list.append([0, 0, {
    #             #         'reschedule_job_line_id': booking_job.id,
    #             #         'carrier_booking_no': booking_job.carrier_booking_no,
    #             #         'booking_date': booking_job.booking_date_time,
    #             #         'booking_no': booking_job.booking_no,
    #             #         'port_of_discharge': booking_job.port_of_discharge.id,
    #             #         'port_of_loading': booking_job.port_of_loading.id,
    #             #         'vessel_name': booking_job.vessel_name.id,
    #             #         'voyage_no': booking_job.voyage_no,
    #             #         'customer': booking_job.customer_name.id,
    #             #         'shipper': booking_job.shipper.id,
    #             #         'consignee': booking_job.consignee.id,
    #             #         'booking_status': booking_job.shipment_booking_status,
    #             #     }])
    #             # lines.append(booking_list)
    #             # job.job_line_ids = lines
    #             return {
    #                 "type": "set_scrollTop",
    #             }
    #             # return {
    #             #     'view_mode': 'form',
    #             #     'view_id': False,
    #             #     'res_model': self._name,
    #             #     'domain': [],
    #             #     'context': dict(self._context, active_ids=self.ids),
    #             #     'type': 'ir.actions.act_window',
    #             #     'target': 'new',
    #             #     'res_id': self.id,
    #             # }
    #
    #             #result['job_line_ids'] = booking_list
    #                 #result = self._convert_to_write(result)

    # @api.multi
    # def action_search_related_job2(self):
    #     for job in self:
    #         domain = [('shipment_booking_status', '!=', '09')]
    #         if job.booking_date:
    #             domain.append(('booking_date_time', '==', job.booking_date))
    #         if job.vessel_name:
    #             domain.append(('vessel_name', '=', job.vessel_name.id))
    #         if job.voyage_no:
    #             domain.append(('voyage_no', '=', job.voyage_no))
    #         # if job.vessel_name:
    #         #     domain.append(('vessel_name', '==', job.vessel_name))
    #         booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
    #         if booking_jobs:
    #             job.job_line_ids = False
    #             #booking_list = []
    #             lines = []
    #             for booking_job in booking_jobs:
    #                 print('>>>>>>>>action_search_related_job2 Before Insert= ', booking_job.booking_no)
    #                 booking_list = {
    #                     'reschedule_job_line_id': job.id,
    #                     'carrier_booking_no': booking_job.carrier_booking_no,
    #                     'booking_date': booking_job.booking_date_time,
    #                     'booking_no': booking_job.booking_no,
    #                     'port_of_discharge': booking_job.port_of_discharge.id,
    #                     'port_of_loading': booking_job.port_of_loading.id,
    #                     'vessel_name': booking_job.vessel_name.id,
    #                     'voyage_no': booking_job.voyage_no,
    #                     'customer': booking_job.customer_name.id,
    #                     'shipper': booking_job.shipper.id,
    #                     'consignee': booking_job.consignee.id,
    #                     'booking_status': booking_job.shipment_booking_status,
    #                 }
    #                 print('>>>>>>>>action_search_related_job2 Before Insert')
    #                 lines.append((0, 0, booking_list))
    #             #job['job_line_ids'] = booking_list
    #             #job = self._convert_to_write(job)
    #             #job.job_line_ids = [(0, 0, booking_list)]
    #             print('>>>>>>>>action_search_related_job2 After Insert')
    #             # lines.append(booking_list)
    #             job.write({'job_line_ids': lines,})
    #             return {
    #                 "type": "set_scrollTop",
    #             }


    # @api.onchange('vessel_name')
    # def onchange_vessel_name(self):
    #     if self.vessel_name:
    #         domain = [('shipment_booking_status', '!=', '09')]
    #         if self.booking_date:
    #             domain.append(('booking_date_time', '==', self.booking_date))
    #         if self.vessel_name:
    #             domain.append(('vessel_name', '=', self.vessel_name.id))
    #         if self.voyage_no:
    #             domain.append(('voyage_no', '=', self.voyage_no))
    #         # if job.vessel_name:
    #         #     domain.append(('vessel_name', '==', job.vessel_name))
    #         booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
    #         if booking_jobs:
    #             self.job_line_ids = False
    #             #booking_list = []
    #             lines = []
    #             for booking_job in booking_jobs:
    #                 print('>>>>>>>>action_search_related_job2 Before Insert= ', booking_job.booking_no)
    #                 booking_list = {
    #                     'reschedule_job_line_id': self.id,
    #                     'carrier_booking_no': booking_job.carrier_booking_no,
    #                     'booking_date': booking_job.booking_date_time,
    #                     'booking_no': booking_job.booking_no,
    #                     'port_of_discharge': booking_job.port_of_discharge.id,
    #                     'port_of_loading': booking_job.port_of_loading.id,
    #                     'vessel_name': booking_job.vessel_name.id,
    #                     'voyage_no': booking_job.voyage_no,
    #                     'customer': booking_job.customer_name.id,
    #                     'shipper': booking_job.shipper.id,
    #                     'consignee': booking_job.consignee.id,
    #                     'booking_status': booking_job.shipment_booking_status,
    #                 }
    #                 print('>>>>>>>>action_search_related_job2 Before Insert')
    #                 lines.append((0, 0, booking_list))
    #             #job['job_line_ids'] = booking_list
    #             #job = self._convert_to_write(job)
    #             #job.job_line_ids = [(0, 0, booking_list)]
    #             print('>>>>>>>>action_search_related_job2 After Insert')
    #             # lines.append(booking_list)
    #             #self.write({'job_line_ids': lines,})
    #             self.job_line_ids = lines
    #             # return {
    #             #     "type": "set_scrollTop",
    #             # }


    @api.onchange('booking_date', 'voyage_no', 'port_of_loading')
    def onchange_booking_date(self):
        if self.booking_date or self.voyage_no:
            self.job_line_ids = False
            domain = [('shipment_booking_status', '!=', '09')]
            if self.booking_date:
                domain.append(('booking_date_time', '=', self.booking_date))
            # if self.vessel_name:
            #     domain.append(('vessel_name', '=', self.vessel_name.id))
            if self.voyage_no:
                domain.append(('voyage_no', '=', self.voyage_no))
            if self.port_of_loading:
                 domain.append(('port_of_loading', '=', self.port_of_loading.id))
            booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
            if booking_jobs:
                #self.job_line_ids = False
                #booking_list = []
                lines = []
                for booking_job in booking_jobs:
                    #print('>>>>>>>>action_search_related_job2 Before Insert= ', booking_job.booking_no)
                    booking_list = {
                        'reschedule_job_line_id': self.id,
                        'carrier_booking_no': booking_job.carrier_booking_no,
                        'booking_date': booking_job.booking_date_time,
                        'booking_no': booking_job.booking_no,
                        'port_of_discharge': booking_job.port_of_discharge.id,
                        'port_of_loading': booking_job.port_of_loading.id,
                        'vessel_name': booking_job.vessel_name.id,
                        'voyage_no': booking_job.voyage_no,
                        'customer': booking_job.customer_name.id,
                        'shipper': booking_job.shipper.id,
                        'consignee': booking_job.consignee.id,
                        'booking_status': booking_job.shipment_booking_status,
                        'contact_person': booking_job.contact_name.id,
                        'add': True,
                    }
                    #print('>>>>>>>>action_search_related_job2 Before Insert')
                    lines.append((0, 0, booking_list))
                #job['job_line_ids'] = booking_list
                #job = self._convert_to_write(job)
                #job.job_line_ids = [(0, 0, booking_list)]
               #print('>>>>>>>>action_search_related_job2 After Insert')
                # lines.append(booking_list)
                #self.write({'job_line_ids': lines,})
                self.job_line_ids = lines
                # return {
                #     "type": "set_scrollTop",
                # }
    # @api.multi
    # def action_search_related_job3(self):
    #     for job in self:
    #         domain = [('shipment_booking_status', '!=', '09')]
    #         if job.booking_date:
    #             domain.append(('booking_date_time', '=', job.booking_date))
    #         if job.vessel_name:
    #             domain.append(('vessel_name', '=', job.vessel_name.id))
    #         if job.voyage_no:
    #             domain.append(('voyage_no', '=', job.voyage_no))
    #         # if job.vessel_name:
    #         #     domain.append(('vessel_name', '==', job.vessel_name))
    #         booking_jobs = self.env['freight.booking'].search(domain, order="booking_no asc")
    #         if booking_jobs:
    #             job.job_line_ids = False
    #             #booking_list = []
    #             lines = []
    #             for booking_job in booking_jobs:
    #                 print('>>>>>>>>action_search_related_job2 Before Insert= ', booking_job.booking_no)
    #                 booking_list = {
    #                     'reschedule_job_line_id': job.id,
    #                     'carrier_booking_no': booking_job.carrier_booking_no,
    #                     'booking_date': booking_job.booking_date_time,
    #                     'booking_no': booking_job.booking_no,
    #                     'port_of_discharge': booking_job.port_of_discharge.id,
    #                     'port_of_loading': booking_job.port_of_loading.id,
    #                     'vessel_name': booking_job.vessel_name.id,
    #                     'voyage_no': booking_job.voyage_no,
    #                     'customer': booking_job.customer_name.id,
    #                     'shipper': booking_job.shipper.id,
    #                     'consignee': booking_job.consignee.id,
    #                     'booking_status': booking_job.shipment_booking_status,
    #                 }
    #                 print('>>>>>>>>action_search_related_job2 Before Insert')
    #                 lines.append((0, 0, booking_list))
    #             #job['job_line_ids'] = booking_list
    #             #job = self._convert_to_write(job)
    #             #job.job_line_ids = [(0, 0, booking_list)]
    #             job.job_line_ids = lines
    #             print('>>>>>>>>action_search_related_job2 After Insert')
    #             # lines.append(booking_list)
    #             #job.write({'job_line_ids': lines,})
    #         return {
    #             "type": "set_scrollTop",
    #         }


class ScheduleBookingLine(models.TransientModel):
    """Split Booking Model."""
    _name = 'schedule.booking.line'

    reschedule_job_line_id = fields.Many2one('reschedule.sailing', 'Reschedule Sailing', required=True, ondelete='cascade',
                                             index=True,copy=False)
    #cost_profit_line = fields.Many2one('freight.cost_profit', string='Booking Reference', required=True, ondelete='cascade',
    #                                   index=True,copy=False)
    booking_no = fields.Char(string='Booking No')
    carrier_booking_no = fields.Char(string='Carrier Booking No')
    booking_date = fields.Date(string='ETA/ETD Date')
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge')
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading')
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name')
    voyage_no = fields.Char(string='Voyage No')
    customer = fields.Many2one('res.partner', string='Customer')
    shipper = fields.Many2one('res.partner', string='Shipper')
    consignee = fields.Many2one('res.partner', string='Consignee')
    booking_status = fields.Char(string='Job Status')
    add = fields.Boolean(string="Add", default=True)
    contact_person = fields.Many2one('res.partner', string='Contact Person')