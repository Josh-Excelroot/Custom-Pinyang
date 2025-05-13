/**********************************************************************************
* 
*    Copyright (C) 2017 MuK IT GmbH
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('attachment_preview.many2one_pdf', function(require) {
"use strict";

var core = require('web.core');
var registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var field_widgets = require('web.relational_fields');

var _t = core._t;
var QWeb = core.qweb;

var FieldpdfMany2One = field_widgets.FieldMany2One.extend({
    template: 'FieldpdfMany2One',
//        events: _.extend({}, AbstractField.prototype.events, {
//        'click .pdf_form_document_preview': '_onClickPreviewPdf',
//        }),

          init: function () {
        var res = this._super.apply(this, arguments);
        this.attachments = []
        this._areAttachmentsLoaded=false
         return res;
    },
           _attachmentPreviewWidgetHidden: function () {
            this.$el.removeClass('attachment_preview');
        },

       getUrl: function () {
        var attachment_extension=this.attachments[0].mimetype;
        var attachment_title = this.attachments[0].name;
        var attachment_url = this.attachments[0].url
//        if (!attachment_url) {
         attachment_url =  '/web/content/' + this.attachments[0].id;
//        }


        var url = (window.location.origin || '') +
        '/attachment_preview/static/lib/ViewerJS/index.html' +
        '?type=' + encodeURIComponent(attachment_extension) +
        '&title=' + encodeURIComponent(attachment_title) +
        '#' +
        attachment_url.replace(window.location.origin, '');
            return url;
        },

     _fetchAttachments: function () {
        var self = this;
        var domain = [
            ['res_id', '=', this.recordData.invoice_id.res_id],
            ['res_model', '=', this.recordData.invoice_id.model],
        ];
        return this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: domain,
            fields: ['id', 'name', 'datas_fname','url','mimetype'],
        }).then(function (result) {
            self._areAttachmentsLoaded = true;
            self.attachments = result;
            if (result.length >= 1){
                        self.showPreview();

            }
        });

    },

    showPreview: function () {
        var url = this.getUrl();

        this.trigger_up('onAttachmentPreview', {url: url,attachment:this.attachments});

    },

    _onClickPreviewPdf: function (ev) {
                        ev.preventDefault();
                ev.stopPropagation();
                this._fetchAttachments();





    },
    _renderReadonly: function () {
    	var self = this;
        this._super.apply(this, arguments);
        var value = _.escape((this.m2o_value || "").trim()).split("\n").join("<br/>");
        if (this.nodeOptions.show_pdf) {
            this.$el.append(QWeb.render('pdf_button_showx'));
     		this.$el.find('.pdfview_many2one_new').click(function (e) {
     		self._onClickPreviewPdf(e);
            });

    }

}
});

registry.add('pdf_many2one', FieldpdfMany2One);

return FieldpdfMany2One;

});
