odoo.define('goexcel_visit.FormController', function (require) {
    'use strict';

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var view_registry = require('web.view_registry');
    var rpc = require('web.rpc');
    var core = require('web.core');

    var VisitFormController = FormController.include({
        runQuery: function (event, model, method, args){
            event.stopPropagation();
            rpc.query({
                model: model,
                method: method,
                args: args,
            }).then(function (){
                core.bus.trigger('reload_page');
            });
        },

        _onButtonClicked: function (event) {
            const self = this;
            var attrs = event.data.attrs;
            var record = event.data.record;
            var id = event.data.attrs.id;

            if ("save_partner_location get_partner_location get_location get_location_check_in get_location_check_out save_customer_location".includes(id)
                && navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function (position) {
                    var gps_location = position.coords.latitude + ',' + position.coords.longitude;
                    var record_id = record.res_id;

                    if (id === 'save_partner_location') {
                        event.stopPropagation();
                        self.runQuery(event,'res.partner', 'save_partner_location',[gps_location, record_id]);
                    }

                    else if (id === 'get_partner_location' || id === 'get_location') {
                        event.stopPropagation();
                        // var destination = record.data.destination;
                        // if (record.data.partner_latitude && record.data.partner_longitude){
                        //     destination = record.data.partner_latitude+','+record.data.partner_longitude;
                        // }
                        // var url = 'https://www.google.com/maps/dir/' + gps_location + '/' + destination;
                        // window.open(url);
                    }

                    else if (id === 'get_location_check_in') {
                        self.runQuery(event, 'visit', 'update_check_in_location', [gps_location, record_id]);
                    }

                    else if (id === 'get_location_check_out') {
                        self.runQuery(event, 'visit', 'update_check_out_location', [gps_location, record_id]);
                    }

                    else if (id === 'save_customer_location') {
                        self.runQuery(event, 'visit', 'save_customer_location', [gps_location, record_id]);
                    }
                });
            }
            this._super(event);
        },
    });
});
