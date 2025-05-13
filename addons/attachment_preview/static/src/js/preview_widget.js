odoo.define('attachment_preview.AbstractMessageExtend', function (require) {
"use strict";

var AbstractMessage = require('mail.model.AbstractMessage');

/**
 * This is a message that is handled by im_livechat, without making use of the
 * mail.Manager. The purpose of this is to make im_livechat compatible with
 * mail.widget.Thread.
 *
 * @see mail.model.AbstractMessage for more information.
 */
 AbstractMessage.include({
    _processAttachmentURL: function () {
//        this._super.apply(this, arguments);
        _.each(this.getAttachments(), function (attachment) {
           if (attachment.url){
           attachment.url = attachment.url
           }
           else{

            attachment.url = '/web/content/' + attachment.id + '?download=true';
            }
        });

    },


});

//return AbstractMessageExtend;

});
