odoo.define('goexcel_user_manual.dialog_inherit', function (require) {
"use strict";

var core = require('web.core');
var dom = require('web.dom');
var Widget = require('web.Widget');
var rpc = require('web.rpc');
var rpc = require('web.rpc');
var web_client = require('web.web_client');
var QWeb = core.qweb;
var _t = core._t;
var Dialog = require('web.Dialog');

    Dialog.include({


          willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            // Render modal once xml dependencies are loaded
            self.$modal = $(QWeb.render('Dialog', {
                fullscreen: true,
                title: self.title,
                subtitle: self.subtitle,
                technical: self.technical,
            }));

            switch (self.size) {
                case 'large':
                    self.$modal.find('.modal-dialog').addClass('modal-lg');
                    break;
                case 'small':
                    self.$modal.find('.modal-dialog').addClass('modal-sm');
                    break;
            }
            self.$footer = self.$modal.find(".modal-footer");
            // Assuming self.$modal is already defined and refers to the modal element
            var view=false;
            var model=false;
            var can_show=false;
            console.log(this);
            if(self.getParent()){
                var action = _.filter(self.getParent().actions,function(elem){

                console.log('--------------------------------------');
                console.log(elem.target);
                console.log(elem.usage);
                return elem.target === "new" && elem.usage == false;
                });

                if(action.length > 0){
                console.log('Enterrrrrrrrrrrrrrrrrrrrrrrr');
                view=action[0].view_id[0];
                model=action[0].res_model;
                can_show=true;
                }
            }

        if(can_show){
              var btn = "<button type='button' class='btn btn-primary' t-att-data-view="+view+"  t-att-data-model="+model+">User Guide</button>"
                self.buttons.push(btn);

            }
               self.set_buttons(self.buttons);
                        self.$modal.on('hidden.bs.modal', _.bind(self.destroy, self));


//            self.$modal.on('hidden.bs.modal', _.bind(self.destroy, self));
        });
    },
    /**
     * @param {Object[]} buttons - @see init
     */
     set_buttons: function (buttons) {
        var self = this;
//        this.$footer.empty();
        var $header = self.$modal.find(".modal-header .modal-title");
        _.each(buttons, function (buttonData) {
            var $button = dom.renderButton({
                attrs: {
                    class: buttonData.classes || (buttons.length > 1 ? 'btn-secondary' : 'btn-primary'),
                    disabled: buttonData.disabled,
                },

                icon: buttonData.icon,
                text: buttonData.text || 'User Guide',
            });


            $button.on('click', function (e) {
                console.log("e",e);
                console.log("this",this);
                console.log("self",self);
                var def;
                if (this.outerText == 'User Guide'){
                var model = $(self.buttons[0]).getAttributes()['t-att-data-model'];
                var view = $(self.buttons[0]).getAttributes()['t-att-data-view'];


                rpc.query({
                model: 'freight.booking.popup',
                method: 'open_url_popoup',
                args: [[2],{'id':2,'view_id':view,'model':model}],
                }).then(function(result) {
                    return web_client.do_action(result);
                });
                }
                if (buttonData.click) {
                    def = buttonData.click.call(self, e);
                }
                if (buttonData.close) {

                    $.when(def).always(self.close.bind(self));
                }
            });

            if (self.technical && buttonData.text) {
                self.$footer.append($button);
            } else {
                $header.append($button);
            }
        });
    },

    });

    return Dialog;


});