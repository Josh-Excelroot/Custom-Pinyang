odoo.define('goexcel_visit.button_partner_location', function (require) {
  'use strict';

  var FormController = require('web.FormController');
  var formController = FormController.include({
    _onButtonClicked: function (event) {
      if (event.data.attrs.id === 'save_partner_location') {
        event.stopPropagation();
        var attrs = event.data.attrs;
        var record = event.data.record;
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(function (position) {
            var rpc = require('web.rpc');
            var gps_location =
              position.coords.latitude + ',' + position.coords.longitude;
            var record_id = record.res_id;
            rpc
              .query({
                model: 'res.partner',
                method: 'save_partner_location',
                args: [gps_location, record_id],
              })
              .always(function () {
                //self.destroy();
              });
          });
        }
      }

      if (event.data.attrs.id === 'get_partner_location') {
        event.stopPropagation();
        var attrs = event.data.attrs;
        var record = event.data.record;
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(function (position) {
            var rpc = require('web.rpc');
            var gps_location =
              position.coords.latitude + ',' + position.coords.longitude;
            var record_id = record.res_id;
            var destination = record.data.destination;
            var url =
              'https://www.google.com/maps/dir/' +
              gps_location +
              '/' +
              destination;
            window.open(url);
          });
        }
      }
      this._super(event);
    },
  });
});
