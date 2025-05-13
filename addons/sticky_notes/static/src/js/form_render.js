odoo.define('sticky_notes.sticky_note', function (require) {
"use strict";

    var core = require('web.core');
    var formRenderer = require('web.FormRenderer');
    var dialogs = require('web.view_dialogs');

    var qweb = core.qweb;
    var _t = core._t;

    formRenderer.include({
        events: _.extend({}, formRenderer.prototype.events, {
            "click .edit_sticky_note": "_onClickStickyNote",
        }),
        _updateView: function ($newContent) {
            //  the method to find existing alerts anad them to the form
            //  to-do: think better when to trigger change of notes. It seems irrational to do it each time a form is
            //  reloaded
            this._super.apply(this, arguments);
            this.$('.sticky_note_container').remove();
            var self = this;
            if (self.state && self.state.model && self.state.data && self.state.data.id) {
                self._rpc({
                    model: "sticky.note",
                    method: "return_notes",
                    args: [self.state.model, self.state.data.id],
                    context: {},
                }).then(function (notes) {
                    if (notes.length > 0) {
                        var $noteHTML = qweb.render('StickyNotes', {"notes": notes});
                        if (self.$('.o_form_statusbar').length) {
                            self.$('.o_form_statusbar').after($noteHTML);
                        } else if (self.$('.o_form_sheet_bg').length) {
                            self.$('.o_form_sheet_bg').prepend($noteHTML);
                        }
                        else {
                            self.$el.prepend($noteHTML);
                        }
                    };
                });
            };
        },
        _onClickStickyNote: function(event) {
            event.preventDefault();
            event.stopPropagation();
            var self = this;
            var resID = parseInt(event.currentTarget.id);
            self._rpc({
                model: "sticky.note",
                method: "return_form_view",
                args: [[resID]],
                context: {},
            }).then(function (res) {
                var dialog = new dialogs.FormViewDialog(self, {
                    res_model: "sticky.note",
                    title: _t("Sticky Note"),
                    res_id: resID,
                    context: res.context,
                    view_id: res.view_id,
                    readonly: false,
                    shouldSaveLocally: false,
                    buttons: [
                        {
                            text: (_t("Save")),
                            classes: "btn-primary",
                            click: function () {
                                dialog._save().then(
                                    self._onApplyNoteAction(dialog)
                                );
                            },
                        },
                        {
                            text: (_t("Remove")),
                            classes: "btn-primary",
                            click: function () {
                                dialog._save().then(
                                    self._onApplyNoteAction(dialog, "unlink")
                                );
                            },
                        },
                        {
                            text: (_t("Discard")),
                            classes: "btn-secondary o_form_button_cancel",
                            close: true,
                        },
                    ],
                }).open();
            });
        },
        _onApplyNoteAction: function(dialog, action) {
            var self = this;
            if (!action) {
                dialog.close();
                self.trigger_up('reload');
            }
            else if (action == 'unlink') {
                var record = dialog.form_view.model.get(dialog.form_view.handle);
                var resID = parseInt(record.data.id);
                self._rpc({
                    model: "sticky.note",
                    method: "unlink",
                    args: [[resID]],
                    context: {},
                }).then(function () {
                    dialog.close();
                    self.trigger_up('reload');
                });
            }
        },
    });

    return formRenderer;

});
