odoo.define('sticky_notes.Sidebar', function (require) {
"use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var dialogs = require('web.view_dialogs');

    var qweb = core.qweb;
    var _t = core._t;

    Sidebar.include({
        events: _.extend({}, Sidebar.prototype.events, {
            "click #sticky_note_sidebar": "_createNewNote",
        }),
        _redraw: function () {
            // Re-write to add sticky note button
            this._super.apply(this, arguments);
            var alReady = $('#sticky_note');
            if (alReady.length == 0) {
                var quickLink = qweb.render("StickyQuickLink", {widget: this});
                this.$el.append(quickLink);
            };
        },
        _createNewNote: function () {
            // The method to open empty note
            var self = this;
            var resModel = this.env.model;
            var resID = parseInt(this.env.activeIds[0]);
            self._rpc({
                model: "sticky.note",
                method: "return_form_view",
                args: [[], resModel, resID],
                context: this.options.env.context,
            }).then(function (res) {
                var onSaved = function(record) {
                    self.trigger_up('reload');
                };
                new dialogs.FormViewDialog(self, {
                    res_model: "sticky.note",
                    title: _t("Sticky Note"),
                    context: res.context,
                    view_id: res.view_id,
                    readonly: false,
                    shouldSaveLocally: false,
                    on_saved: onSaved,
                }).open();
            });
        },
    });

});