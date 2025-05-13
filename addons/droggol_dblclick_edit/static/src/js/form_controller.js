odoo.define('droggol_dblclick_edit.FormController', function (require) {
"use strict";
var FormController = require('web.FormController');
var FormRenderer = require('web.FormRenderer');

FormRenderer.include({
    events: _.extend({}, FormRenderer.prototype.events, {
        'dblclick': '_onFormviewDblClick',
    }),
    _onFormviewDblClick: function (ev) {
        var $target = $(ev.target);
        // avoid if chatter components or modal
        if ($target.parents('.modal').length || $target.parents('.o_chatter').length || $target.is('.o_chatter')) {
            return;
        }
        switch (this.mode) {
            case 'readonly':
                if (!$target.is('.o_form_label, .o_field_widget')) {
                    this.trigger_up('d_switch_mode');
                }
                break;
            case 'edit':
                if (!$target.is('.o_form_label, input, textarea') && !$target.parents('.o_field_widget').length) {
                    this.trigger_up('d_switch_mode');
                }
                break;
        }
    },
});

FormController.include({
    custom_events: _.extend({}, FormController.prototype.custom_events, {
        d_switch_mode: '_onTurnOnEditMode',
    }),
    _onTurnOnEditMode: function (ev) {
        if (this.is_action_enabled('edit')) {
            switch (this.mode) {
                case 'readonly':
                    this._onEdit();
                    break;
                case 'edit':
                    this._onSave(ev);
                    break;
            }
        }
    },
});
});
