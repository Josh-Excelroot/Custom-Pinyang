odoo.define('goexcel_user_manual.action_button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var web_client = require('web.web_client');
    var _t = core._t;


    ListController.include({
        renderButtons: function($node) {

        this._super.apply(this, arguments);
            if (this.$buttons) {
              this.$buttons.find('.oe_action_button').click(this.proxy('action_def')) ;
            }
        },
        action_def: function () {
            var self =this
            var user = session.uid;
            rpc.query({
                model: 'freight.booking.popup',
                method: 'open_url_popoup',
                args: [[user],{'id':user,'view_id':self.ksViewID,'model':self.modelName}],
                }).then(function(result) {
                    return web_client.do_action(result);
                });
            },
    })





});
