odoo.define('restrict_product_partner.partner_form', function (require) {
    "use strict";

// Ahmad Zaman - 21/9/24 - Custom Warning on Saving Duplicate Contact
    var FormController = require('web.FormController');
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');

    FormController.include({
        _onSave: function () {
            var self = this;

            if (this.modelName === 'res.partner') {
                return rpc.query({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['restrict_product_partner.warning'],
                }).then(function (warning_enabled) {

                    if (warning_enabled === 'True') {
                        var partner_name = this.renderer.state.data.name;
                        var partner_company_id;
                            if (this.renderer.state.data.company_id.data.id) {
                                partner_company_id = this.renderer.state.data.company_id.data.id;
                            } else {
                                partner_company_id = false;
                            }

                        return rpc.query({
                            model: 'res.partner',
                            method: 'search_read',
                            args: [[
                                ['name', '=', partner_name],
                                ['company_id', '=', partner_company_id],
                                ['company_type', '=', 'company']
                            ]],
                            fields: ['id'],
                            limit: 1
                        }).then(function (partners) {

                            if (partners.length > 0) {
                                var dialog = new Dialog(self, {
                                    title: 'Duplicate Partner',
                                    size: 'medium',
                                    $content: $('<p> A contact with the same name already exists. Do you want to proceed?</p>'),
                                    buttons: [
                                        {
                                            text: 'Proceed',
                                            classes: 'btn-primary',
                                            close: true,
                                            click: function () {
                                                self.saveRecord();
                                            }
                                        },
                                        {
                                            text: 'Cancel',
                                            close: true,
                                        }
                                    ]
                                });
                                dialog.open();
                                return $.Deferred().reject();
                            } else {
                                return self.saveRecord();
                            }
                        });
                    } else {
                        return self.saveRecord();
                    }
                });
            }
            return this._super.apply(this, arguments);
        }
    });
});

