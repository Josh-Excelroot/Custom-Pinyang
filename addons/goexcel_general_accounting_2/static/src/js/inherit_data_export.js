odoo.define('goexcel_general_accounting_2.inherit_data_export', function (require) {
"use strict";


var core = require('web.core');
var crash_manager = require('web.crash_manager');
var data = require('web.data');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var DataExport = require('web.DataExport');

var QWeb = core.qweb;
var _t = core._t;

DataExport.include({

 add_field: function( field_id, string , field_type) {

        var $field_list = this.$('.o_fields_list');
        var field_type_new = this.records[field_id].field_type  ;

        if (field_type_new == 'many2one')
        {
          console.log("custom module ***")  ;

              if($field_list.find("option[value='" + field_id+'/name' + "']").length === 0) {
                $field_list.append(new Option(string, field_id+'/name'));
            }

               if($field_list.find("option[value='" + field_id + "']").length > 0) {
                $field_list.find("option[value='" + field_id + "']").remove()
            }

        }
        else
        {
            field_id = this.records[field_id].value || field_id;
            if($field_list.find("option[value='" + field_id + "']").length === 0) {
                $field_list.append(new Option(string, field_id));
            }

        }
    },

 });

return DataExport ;




});