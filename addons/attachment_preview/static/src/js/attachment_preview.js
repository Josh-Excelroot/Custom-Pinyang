/* Copyright 2014 Therp BV (<http://therp.nl>)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define('attachment_preview', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    var Chatter = require('mail.Chatter');
    var basic_fields = require('web.basic_fields');
    var FormRenderer = require('web.FormRenderer');
    var FormController = require('web.FormController');
    var Widget = require('web.Widget');

    var AttachmentBox = require('mail.AttachmentBox');


//        $(document).on("click", ".preview_report_view", function(ev){
//        ev.preventDefault();
//        var $target = $(this);
//        var product = $(ev.currentTarget);
//        console.log('payslip click');
//
//        });
//
        var formController = FormController.include({

               getUrl: function (attachments) {
        var attachment_extension=attachments[0].mimetype;
        var attachment_title = attachments[0].name;
        var attachment_url = attachments[0].url
//        if (!attachment_url) {
         attachment_url =  '/web/content/' + attachments[0].id;
//        }


        var url = (window.location.origin || '') +
        '/attachment_preview/static/lib/ViewerJS/index.html' +
        '?type=' + encodeURIComponent(attachment_extension) +
        '&title=' + encodeURIComponent(attachment_title) +
        '#' +
        attachment_url.replace(window.location.origin, '');
            return url;
        },
             _attachmentPreviewWidgetHidden: function () {
             this.$el.find('.o_form_view').removeClass('attachment_preview');
//            this.__parentedParent.__parentedParent.$el.removeClass('attachment_preview');
        },
            showPreview: function (atachments) {
            console.log("Testing")
        var url = this.getUrl(atachments);
        var attachmentPreviewWidget = new AttachmentPreviewWidget(this);
            attachmentPreviewWidget.on('hidden', this, this._attachmentPreviewWidgetHidden);
            attachmentPreviewWidget.insertAfter(this.$el.find('.o_form_view'));
               this.$el.find('.o_form_view').addClass('attachment_preview');

            attachmentPreviewWidget.setAttachments(
              atachments,url
            );
           attachmentPreviewWidget.show();

//        this.trigger_up('onAttachmentPreview', {url: url,attachment:atachments});

    },

//     _fetchAttachments: function (ev) {
     _fetchAttachmentsPayslip: function (ev) {
        var self = this;
        console.log(ev.data.record.res_id);
        var domain = [
            ['res_id', '=', ev.data.record.res_id],
            ['res_model', '=', 'hr.payslip'],
        ];
        return this._rpc({
            model: 'ir.attachment',
            method: 'payslip_attachments',
            domain: domain,
                 args: [[
                	['res_id', '=', ev.data.record.res_id],
                ]],
            fields: ['id', 'name', 'datas_fname','url','mimetype'],
        }).then(function (result) {
//            self._areAttachmentsLoaded = true;
//            self.attachments = result;
            if (result.length >= 1){
                        self.showPreview(result);

            }
        });

    },

        _onButtonClicked: function (event) {
//            if(event.data.attrs.id === "preview_report_view"){
//            console.log('Test xxxx');
//                      this._fetchAttachmentsPayslip(event);
////                      this._fetchAttachments(event);
//            }
            this._super(event);
            },
        });

     AttachmentBox.include({

        /**
         * @constructor
         */
        init: function (parent, record, attachments) {
            this._super.apply(this, arguments);
            console.log('inhereted');
             this.fileuploadId = _.uniqueId('oe_fileupload');
        $(window).on(this.fileuploadId, this._onUploaded.bind(this));
        this.currentResID = record.res_id;
        this.currentResModel = record.model;
        this.attachmentIDs = attachments;
        this.imageList = {};
        this.otherList = {};

        _.each(attachments, function (attachment) {
            // required for compatibility with the chatter templates.
            if (!attachment.url){
            attachment.url = '/web/content/' + attachment.id;
            }
             attachment.url = '/web/content/' + attachment.id;
//            attachment.url = attachment.url_drive
//            attachment.mimetype= 'application/pdf'
            attachment.filename = attachment.datas_fname || _t('unnamed');
        });
        var sortedAttachments = _.partition(attachments, function (att) {
            return att.mimetype && att.mimetype.split('/')[0] === 'image';
        });
        this.imageList = sortedAttachments[0];
        this.otherList = sortedAttachments[1];
        },
        });



    var AttachmentPreviewMixin = {
        canPreview: function (extension) {
            return $.inArray(
                extension,
                ['odt', 'odp', 'ods', 'fodt', 'pdf', 'ott', 'fodp', 'otp',
                 'fods', 'ots',
                ]) > -1;
        },

        getUrl: function (attachment_id, attachment_url, attachment_extension, attachment_title) {
            var url = (window.location.origin || '') +
                '/attachment_preview/static/lib/ViewerJS/index.html' +
                '?type=' + encodeURIComponent(attachment_extension) +
                '&title=' + encodeURIComponent(attachment_title) +
                '#' +
                attachment_url.replace(window.location.origin, '');
            return url;
        },

        showPreview: function (attachment_id, attachment_url, attachment_extension, attachment_title, split_screen) {
            var url = this.getUrl(attachment_id, attachment_url, attachment_extension, attachment_title);
            if (split_screen) {
                this.trigger_up('onAttachmentPreview', {url: url});
            } else {
                window.open(url);
            }
        },
    };

    Chatter.include(AttachmentPreviewMixin);
    Chatter.include({
        events: _.extend({}, Chatter.prototype.events, {
            'click .o_attachment_preview': '_onPreviewAttachment',
        }),

        previewableAttachments: null,

        _openAttachmentBox: function () {
            var res = this._super.apply(this, arguments);

            this.getPreviewableAttachments().done(function (atts) {
                this.previewableAttachments = atts;
                this.updatePreviewButtons(atts);
                this.getParent().attachmentPreviewWidget.setAttachments(atts);
            }.bind(this));

            return res;
        },

        update: function () {
            var res = this._super.apply(this, arguments);
            var self = this;
            if (this.getParent().$el.hasClass('attachment_preview')) {
                this._fetchAttachments().done(function () {
                    self._openAttachmentBox();
                    self.getPreviewableAttachments().done(function (atts) {
                        self.updatePreviewButtons(self.previewableAttachments);
                        self.previewableAttachments = atts;
                        self.getParent().attachmentPreviewWidget.setAttachments(atts);
                    });
                });
            }
            return res;
        },
            _fetchAttachments: function () {
        var self = this;
        var domain = [
            ['res_id', '=', this.record.res_id],
            ['res_model', '=', this.record.model],
        ];
        return this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: domain,
            fields: ['id', 'name', 'datas_fname', 'mimetype','url'],
        }).then(function (result) {
            self._areAttachmentsLoaded = true;
            self.attachments = result;
        });

    },

        _onPreviewAttachment: function (event) {
            event.preventDefault();
            var self = this,
                $target = $(event.currentTarget),
                split_screen = $target.attr('data-target') !== 'new',
                attachment_id = parseInt($target.attr('data-id'), 10),
                attachment_url = $target.attr('data-url'),
                attachment_extension = $target.attr('data-extension'),
                attachment_title = $target.attr('data-original-title');

            if (attachment_extension) {
                this.showPreview(attachment_id, attachment_url, attachment_extension, attachment_title, split_screen);
            } else {
                this._rpc({
                    model: 'ir.attachment',
                    method: 'get_attachment_extension',
                    args: [attachment_id],
                }).then(function (extension) {
                    self.showPreview(attachment_id, attachment_url, extension, null, split_screen);
                });
            }
        },

        getPreviewableAttachments: function () {
            var self = this;
            var deferred = $.Deferred();

            var $items = this.$el.find('.o_attachment_preview');
            var attachments = _.object($items.map(function () {
                return parseInt($(this).attr('data-id'), 10);
            }), $items.map(function () {
                return {
                    url: $(this).attr('data-gd-url'),
                    extension: $(this).attr('data-extension'),
                    title: $(this).attr('data-original-title'),
                };
            }));

            this._rpc({
                model: 'ir.attachment',
                method: 'get_attachment_extension',
                args: [
                    _.map(_.keys(attachments), function (id) {
                        return parseInt(id, 10);
                    }),
                ],
            }).then(function (extensions) {
                var reviewableAttachments = _.map(_.keys(_.pick(extensions, function (extension, id) {
                    return self.canPreview(extension);
                })), function (id) {
                    return {
                        id: id,
                        url: attachments[id].url,
                        extension: extensions[id],
                        title: attachments[id].title,
                        previewUrl: self.getUrl(
                            id,
                            attachments[id].url,
                            extensions[id],
                            id + ' - ' + attachments[id].title
                        ),
                    };
                });
                deferred.resolve(reviewableAttachments);
            }, function () {
                deferred.reject();
            });
            return deferred.promise();
        },

        updatePreviewButtons: function (previewableAttachments) {
            this.$el.find('.o_attachment_preview').each(function () {
                var $this = $(this);
                var id = $this.attr('data-id');
                var att = _.findWhere(previewableAttachments, {id: id});
                if (att) {
                    $this.attr('data-extension', att.extension);
                } else {
                    $this.remove();
                }
            });
        },
    });

    basic_fields.FieldBinaryFile.include(AttachmentPreviewMixin);
    basic_fields.FieldBinaryFile.include({
        events: _.extend({}, basic_fields.FieldBinaryFile.prototype.events, {
            'click .fa-search': '_onPreview',
        }),

        _renderReadonly: function () {
            var self = this;
            this._super.apply(this, arguments);

            if (this.recordData.id) {
                this._getBinaryExtension().done(function (extension) {
                    if (self.canPreview(extension)) {
                        self._renderPreviewButton(extension);
                    }
                });
            }
        },

        _renderPreviewButton: function (extension) {
            this.$previewBtn = $("<a/>");
            this.$previewBtn.addClass('fa fa-search mr-2');
            this.$previewBtn.attr('href', 'javascript:void(0)');
            this.$previewBtn.attr('title', _.str.sprintf(_t('Preview %s'), this.field.string));
            this.$previewBtn.attr('data-extension', extension);
            this.$el.find('.fa-download').before(this.$previewBtn);
        },

        _getBinaryExtension: function () {
            return this._rpc({
                model: 'ir.attachment',
                method: 'get_binary_extension',
                args: [
                    this.model,
                    this.recordData.id,
                    this.name,
                    this.attrs.filename,
                ],
            });
        },

        _onPreview: function (event) {
            this.showPreview(
                null,
                _.str.sprintf(
                    '/web/content?model=%s&field=%s&id=%d',
                    this.model,
                    this.name,
                    this.recordData.id
                ),
                $(event.currentTarget).attr('data-extension'),
                _.str.sprintf(_t('Preview %s'), this.field.string),
                false
            );
            event.stopPropagation();
        },
    });

    var AttachmentPreviewWidget = Widget.extend({
        template: 'attachment_preview.AttachmentPreviewWidget',
        activeIndex: 0,
        attachments: null,
        local_url:null,

        events: {
            'click .attachment_preview_close': '_onCloseClick',
            'click .attachment_preview_previous': '_onPreviousClick',
            'click .attachment_preview_next': '_onNextClick',
            'click .attachment_preview_popout': '_onPopoutClick',
        },

        start: function () {
            var res = this._super.apply(this, arguments);
            this.$overlay = this.$el.find('.attachment_preview_overlay');
            this.$iframe = this.$el.find('.attachment_preview_iframe');
            this.$current = this.$el.find('.attachment_preview_current');
            return res;
        },

        _onCloseClick: function () {
            this.hide();
        },

        _onPreviousClick: function () {
            this.previous();
        },

        _onNextClick: function () {
            this.next();
        },

        _onPopoutClick: function () {
            if (!this.attachments[this.activeIndex]) {
                return;
            }

            window.open(this.attachments[this.activeIndex].previewUrl);
        },

        next: function () {
            var index = this.activeIndex + 1;
            if (index >= this.attachments.length) {
                index = 0;
            }
            this.activeIndex = index;
            this.updatePaginator();
            this.loadPreview();
        },

        previous: function () {
            var index = this.activeIndex - 1;
            if (index < 0) {
                index = this.attachments.length - 1;
            }
            this.activeIndex = index;
            this.updatePaginator();
            this.loadPreview();
        },

        show: function () {
            this.$el.removeClass('d-none');
            this.trigger('shown');
        },

//        hide: function () {
//            this.$el.addClass('d-none');
//            this.trigger('hidden');
//        },

        hide: function () {
            if(this.$el){
                this.$el.addClass('d-none');
                this.trigger('hidden');}
        },

        updatePaginator: function () {
            if (this.attachments){
            var value = _.str.sprintf('%s / %s', this.activeIndex + 1, this.attachments.length);
            this.$current.html(value);
            }

        },

        loadPreview: function () {
            if (this.attachments.length === 0) {
                this.$iframe.attr('src', 'about:blank');
                return;
            }

            var att = this.attachments[this.activeIndex];
            if (!att.previewUrl && this.local_url.length>=1){
                     if (this.local_url.search('drive.google')!==-1){
                        var prevUrl =  this.local_url.split('#')[1]
                        var leftpart = prevUrl.split('?')[0]
                        var rightpart = prevUrl.split('?')[1].split('&')[1]
                        prevUrl = leftpart + '?'+  rightpart

                                                this.$iframe.attr('src', prevUrl);


            }
            else{
             var prevUrl1 =  this.local_url.split('?')[0]
              var prevUrl2 =  this.local_url.split('?')[1]
               var prevUrl_extra =  prevUrl2.split('?')[0]

                this.$iframe.attr('src', this.local_url);

            }
            }
            else{
                     if (att.previewUrl.search('drive.google')!==-1){
                        var prevUrl =  att.previewUrl.split('#')[1]
                        var leftpart = prevUrl.split('?')[0]
                        var rightpart = prevUrl.split('?')[1].split('&')[1]
                        prevUrl = leftpart + '?'+  rightpart

                                                this.$iframe.attr('src', att.previewUrl);


            }
            else{
             var prevUrl1 =  att.previewUrl.split('?')[0]
              var prevUrl2 =  att.previewUrl.split('?')[1]
               var prevUrl_extra =  prevUrl2.split('?')[0]

                this.$iframe.attr('src', att.previewUrl);

            }

            }

        },

        setAttachments: function (attachments,local_url=false) {
            this.attachments = attachments;
            this.activeIndex = 0;
            this.local_url = local_url
             if (this.$el){
            this.updatePaginator();
            this.loadPreview();
            }

        },
    });

    FormRenderer.include({
        custom_events: _.extend({}, FormRenderer.prototype.custom_events, {
            onAttachmentPreview: '_onAttachmentPreview',
        }),

        attachmentPreviewWidget: null,

        init: function () {
            var res = this._super.apply(this, arguments);
            this.attachmentPreviewWidget = new AttachmentPreviewWidget(this);
            this.attachmentPreviewWidget.on('hidden', this, this._attachmentPreviewWidgetHidden);
            this.attachments = arguments.attachments;
            this.local_url=false
            return res;
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self.attachmentPreviewWidget.insertAfter(self.$el);
            });
        },
//       getUrl: function (attach) {
//       var attachment_extension = false;
//       var attachment_title =false;
//       var attachment_url=false;
//               var attachment = this.attachments;
//               if (attachment.length > 0){
//
//
//        var attachment_extension=this.attachments[0].mimetype;
//        var attachment_title = this.attachments[0].name;
//        var attachment_url = this.attachments[0].url
////        if (!attachment_url) {
//         attachment_url =  '/web/content/' + this.attachments[0].id;
////        }
//
//
//        var url = (window.location.origin || '') +
//        '/attachment_preview/static/lib/ViewerJS/index.html' +
//        '?type=' + encodeURIComponent(attachment_extension) +
//        '&title=' + encodeURIComponent(attachment_title) +
//        '#' +
//        attachment_url.replace(window.location.origin, '');
//            return url;
//            }
//            else{
//            return attach
//            }
//            return false
//        },
//
//     _fetchAttachments:async function () {
//        var self = this;
//        var domain = [
//            ['res_id', '=', this.state.res_id],
//            ['res_model', '=', this.state.model],
//        ];
//        if(this.state.model === 'hr.payslip' && this.state.res_id){
//
//                return this._rpc({
//            model: 'ir.attachment',
//            method: 'payslip_attachments',
//            domain: domain,
//            args:domain,
//            fields: ['id', 'name', 'datas_fname','url','mimetype'],
//        }).then(function (result) {
//            self.attachments = result;
//        });
//        }
//        else if(this.state.model === 'account.invoice' && this.state.res_id){
//                        return this._rpc({
//            model: 'ir.attachment',
//            method: 'invoice_attachments',
//            domain: domain,
//            args:domain,
//            fields: ['id', 'name', 'datas_fname','url','mimetype'],
//        }).then(function (result) {
//            self.attachments = result;
//        });
//
//        }
//        else{
//        return this._rpc({
//            model: 'ir.attachment',
//            method: 'search_read',
//            domain: domain,
//            fields: ['id', 'name', 'datas_fname','url','mimetype'],
//        }).then(function (result) {
////            self._areAttachmentsLoaded = true;
//            self.attachments = result;
////            if (result.length >= 1){
////                        self.showPreview();
////
////            }
//        });
//        }
//
//    },
//                 _renderView: function () {
//          var self = this;
//           var def = this._super();
//         var attach=  this._fetchAttachments();
//         this.attachmentPreviewWidget.destroy();
//          this.attachmentPreviewWidget = new AttachmentPreviewWidget(this);
//           this.attachmentPreviewWidget.on('hidden', this, this._attachmentPreviewWidgetHidden);
//
//
////                   this.trigger_up('onAttachmentPreview', {url: url,attachment:this.attachments});
//return Promise.resolve(attach).then(function (obj) {
//
// self.url = self.getUrl(attach)
//if(self.url){
//self.attachmentPreviewWidget.insertAfter(self.$el);
//self.local_url=self.url;
//self.showAttachmentPreviewWidget();
//
//}
//console.log("RWENDER VIEW");
//           return def;
//           });
//         },

        _attachmentPreviewWidgetHidden: function () {
            this.$el.removeClass('attachment_preview');
        },

        showAttachmentPreviewWidget: function () {
//        Kashif - 18/9/24 - Fixed empty popup on invoice creation
        if (this.attachments.length > 0){
            this.$el.addClass('attachment_preview');

            this.attachmentPreviewWidget.setAttachments(
              this.attachments  ||  this.chatter.previewableAttachments,this.local_url
            );
            this.attachmentPreviewWidget.show();
            }
        },

        on_detach_callback: function () {
            this.attachmentPreviewWidget.hide();
            return this._super.apply(this, arguments);
        },

        _onAttachmentPreview: function (event) {
        if (event.data.attachment){
              if (event.data.attachment.length >=1){
             this.attachments = event.data.attachment;

           }

        }

            if (event.data.url.length >=1){
               this.local_url = event.data.url

            }
            this.showAttachmentPreviewWidget();
        },
    });


    return {
        AttachmentPreviewMixin: AttachmentPreviewMixin,
        AttachmentPreviewWidget: AttachmentPreviewWidget,

    };
});
