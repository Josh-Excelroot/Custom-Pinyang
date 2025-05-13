odoo.define('odoo_recently_viewed_records.get_view_url', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var QWeb = core.qweb;

    FormRenderer.include({
//            kashif 25may23 : calling the function after renderview base js loads

    autofocus: function () {
        if (this.mode === 'readonly') {
            var firstPrimaryFormButton =  this.$el.find('button.btn-primary:enabled:visible:first()');
//            customm
var self=this;
                                  var url = self.$el.context.baseURI;
            var components = URI.parse(url);
            var query = URI.parseQuery(components['fragment']);
            var vals = {
                'name': self.state.data.display_name,
                'url': self.$el.context.baseURI,
                'action': parseInt(query['action']) || false,
                'record_id': self.state.data.id,
                'model': self.state.model,
            }
            ajax.jsonRpc("/recently/view/records", 'call', vals)
            .then(function(data) {
                if (data['status']) {
                    self._updateRecordPreview(data.records_list);
                }
            });

//custom
            if (firstPrimaryFormButton.length > 0) {
                return firstPrimaryFormButton.focus();
            } else {
                return;
            }
        }
        var focusWidget = this.defaultFocusField;
        if (!focusWidget || !focusWidget.isFocusable()) {
            var widgets = this.allFieldWidgets[this.state.id];
            for (var i = 0; i < (widgets ? widgets.length : 0); i++) {
                var widget = widgets[i];
                if (widget.isFocusable()) {
                    focusWidget = widget;
                    break;
                }
            }
        }
        if (focusWidget) {
            return focusWidget.activate({noselect: true, noAutomaticCreate: true});
        }
    },

//        autofocus: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                                   var url = self.$el.context.baseURI;
//            var components = URI.parse(url);
//            var query = URI.parseQuery(components['fragment']);
//            var vals = {
//                'name': self.state.data.display_name,
//                'url': self.$el.context.baseURI,
//                'action': parseInt(query['action']) || false,
//                'record_id': self.state.data.id,
//                'model': self.state.model,
//            }
//            ajax.jsonRpc("/recently/view/records", 'call', vals)
//            .then(function(data) {
//                if (data['status']) {
//                    self._updateRecordPreview(data.records_list);
//                }
//            });
//            });
//
//        },

//    _renderView: function () {
//     var self = this;
//        return this._super.apply(this, arguments).then(function () {
//                    var url = self.$el.context.baseURI;
//            var components = URI.parse(url);
//            var query = URI.parseQuery(components['fragment']);
//            var vals = {
//                'name': self.state.data.display_name,
//                'url': self.$el.context.baseURI,
//                'action': parseInt(query['action']) || false,
//                'record_id': self.state.data.id,
//                'model': self.state.model,
//            }
//            ajax.jsonRpc("/recently/view/records", 'call', vals)
//            .then(function(data) {
//                if (data['status']) {
//                    self._updateRecordPreview(data.records_list);
//                }
//            });
//        });
//        },


//        _updateView: function(e) {
//            var self = this;
//            this._super.apply(this, arguments);
//            var url = this.$el.context.baseURI;
//            var components = URI.parse(url);
//            var query = URI.parseQuery(components['fragment']);
//            var vals = {
//                'name': this.state.data.display_name,
//                'url': this.$el.context.baseURI,
//                'action': parseInt(query['action']) || false,
//                'record_id': this.state.data.id,
//                'model': this.state.model,
//            }
//             console.log('ok0');
//            ajax.jsonRpc("/recently/view/records", 'call', vals)
//            .then(function(data) {
//                if (data['status']) {
//                    self._updateRecordPreview(data.records_list);
//                }
//            });
//        },
        _updateRecordPreview: function(records) {
            var self = this;
            $('.o_mail_systray_dropdown_items').html(
                QWeb.render('odoo_recently_viewed_records.RecentRecordPreview', {
                    records : records
                })
            );
        },
    });
});
