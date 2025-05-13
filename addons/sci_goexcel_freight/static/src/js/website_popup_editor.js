odoo.define('sci_goexcel_freight.si_website_popup_add', function (require) {
  'use strict';

  //var Model = require('web.Model');
  //var base = require('web_editor.base');
  //var options = require('web_editor.snippets.options');
  //var session = require('web.session');
  //var website = require('website.website');
  var core = require('web.core');
  var website = require('website.website');

  $(document).ready(function () {
    $('#popup_add_line_button').change(function () {
      var rpc = require('web.rpc');
      rpc
        .query({
          model: 'freight.ports',
          method: 'get_port_of_loading',
          args: [],
        })
        .then((data) => {
          data.map((portOfLoading) => {
            portName = `${portOfLoading.name}, ${portOfLoading.country_id.name}`;
            $('#port-of-loading').append(
              `<option value="${portOfLoading.name}">${portName}</option>`
            );
          });
        });
    });

    $('#popup_add_line_button').click(function () {
      $('#oe_generic_popup_modal').modal('show');
      //alert(core._t('Hello world'));
    });

    $('.popup_edit_line_button').click(function () {
      var rpc = require('web.rpc');
      const lineId = $(this).children('.hidden-line').val();
      const siCargoType = $(this).children('.hidden-si-cargo-type').val();
      console.log(siCargoType);
      rpc
        .query({
          model: 'freight.website.si',
          method: 'get_data',
          args: ['data', [lineId, siCargoType]],
        })
        .then((data) => {
          $('input[name=container_product_name]').val(
            data.container_product_name
          );
          console.log($('input[name=container_product_name]').val());
          $('input[name=fcl_container_qty]').val(data.fcl_container_qty);
          $('input[name=seal_no]').val(data.seal_no);
          $('input[name=packages_no]').val(data.packages_no);
          $('input[name=exp_gross_weight]').val(data.exp_gross_weight);
          $('input[name=exp_vol]').val(data.exp_vol);
          $('textarea[name=remark]').val(data.remark);
          $('input[name=line_id]').val(data.id);
        });
      $('#oe_edit_line_popup_modal').modal('show');
      //alert(core._t('Hello world'));
    });
  });

  /* $("#popup_button").on('click', function () {
        //$('#oe_generic_popup_modal').modal('show');
        alert(core._t('Hello world'));
    });*/
});
