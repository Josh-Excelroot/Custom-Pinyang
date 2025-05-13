odoo.define('one2many_field_search.one2many_field_search', function (require) {
    // The goal of this file is to contain JS hacks related to allowing
    // section and note on sale order and invoice.

    // [UPDATED] now also allows configuring products on sale order.

    "use strict";

    var pyUtils = require('web.py_utils');
    var core = require('web.core');
    var _t = core._t;
    var FieldChar = require('web.basic_fields').FieldChar;
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var fieldRegistry = require('web.field_registry');
    var FieldText = require('web.basic_fields').FieldText;
    var ListRenderer = require('web.ListRenderer');

    var SectionAndNoteListRenderer = ListRenderer.extend({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, ListRenderer.prototype.events),
        /**
         * We want section and note to take the whole line (except handle and trash)
         * to look better and to hide the unnecessary fields.
         *
         * @override
         */
        _renderBodyCell: function (record, node, index, options) {
            var $cell = this._super.apply(this, arguments);

            var isSection = record.data.display_type === 'line_section';
            var isNote = record.data.display_type === 'line_note';

            if (isSection || isNote) {
                if (node.attrs.widget === "handle") {
                    return $cell;
                } else if (node.attrs.name === "name") {
                    var nbrColumns = this._getNumberOfCols();
                    if (this.handleField) {
                        nbrColumns--;
                    }
                    if (this.addTrashIcon) {
                        nbrColumns--;
                    }
                    $cell.attr('colspan', nbrColumns);
                } else {
                    return $cell.addClass('o_hidden');
                }
            }

            return $cell;
        },

        /**
         * We add the o_is_{display_type} class to allow custom behaviour both in JS and CSS.
         *
         * @override
         */
        _renderRow: function (record, index) {
            var $row = this._super.apply(this, arguments);

            if (record.data.display_type) {
                $row.addClass('o_is_' + record.data.display_type);
            }

            return $row;
        },

        /**
         * We want to add .o_section_and_note_list_view on the table to have stronger CSS.
         *
         * @override
         * @private
         table-responsive
         */
//        _renderView: function () {
//            var def = this._super();
//            var self=this;
//            this.$el.find('> table').addClass('o_section_and_note_list_view');
//            if (self.arch.tag == 'tree' && self.$el.hasClass('o_list_view')) {
//                var search = '<input type="text" class="oe_search_input mt-2 ml-5 pl-5" placeholder="Search...">';
//                var row_count = '<span class="oe_row_count">Total Row: '+ self.state.data.length+'</span>';
//                self.$el.find('table').addClass('oe_table_search');
//                var $search = $(search).css('border', '1px solid #ccc')
//                .css('width', '50%')
//                .css('border-radius', '10px')
//                // .css('margin-top', '-32px')
//                .css('height', '30px')
//                var $row_count = $(row_count).css('float', 'right')
//                .css('margin-right', '30rem')
//                .css('margin-top', '4px')
//                .css('color', '#666666');
//                self.$el.prepend($search);
//                self.$el.prepend($row_count);
//            }
//            return def;
//        },

                _renderView: function () {
            var def = this._super();
            var self=this;
            this.$el.find('> table').addClass('o_section_and_note_list_view');
            if (self.arch.tag == 'tree' && self.$el.hasClass('table-responsive')) {
                var search = '<input type="text" class="oe_search_input mt-2 ml-5 pl-5" placeholder="Search...">';
                var row_count = '<span class="oe_row_count">Total Row: '+ self.state.data.length+'</span>';
                self.$el.find('table').addClass('oe_table_search');
                var $search = $(search).css('border', '1px solid #ccc')
                .css('width', '50%')
                .css('border-radius', '10px')
                // .css('margin-top', '-32px')
                .css('height', '30px')
                var $row_count = $(row_count).css('float', 'right')
                .css('margin-right', '30rem')
                .css('margin-top', '4px')
                .css('color', '#666666');
                var total_columns = self.$el.find('thead tr th').length;
                var table = '<tr><th colspan="' + total_columns + '"></th></tr>';
                var $table = $(table);
                $table.find('th').append($row_count, $search);
                self.$el.find('thead').prepend($table);
            }
            return def;
        },

        /**
         * Add support for product configurator
         *
         * @override
         * @private
         */
        _onAddRecord: function (ev) {
            // we don't want the browser to navigate to a the # url
            ev.preventDefault();

            // we don't want the click to cause other effects, such as unselecting
            // the row that we are creating, because it counts as a click on a tr
            ev.stopPropagation();

            // but we do want to unselect current row
            var self = this;
            this.unselectRow().then(function () {
                var context = ev.currentTarget.dataset.context;

                var pricelistId = self._getPricelistId();
                if (context && pyUtils.py_eval(context).open_product_configurator){
                    self._rpc({
                        model: 'ir.model.data',
                        method: 'xmlid_to_res_id',
                        kwargs: {xmlid: 'sale.sale_product_configurator_view_form'},
                    }).then(function (res_id) {
                        self.do_action({
                            name: _t('Configure a product'),
                            type: 'ir.actions.act_window',
                            res_model: 'sale.product.configurator',
                            views: [[res_id, 'form']],
                            target: 'new',
                            context: {
                                'default_pricelist_id': pricelistId
                            }
                        }, {
                            on_close: function (products) {
                                if (products && products !== 'special'){
                                    self.trigger_up('add_record', {
                                        context: self._productsToRecords(products),
                                        forceEditable: "bottom" ,
                                        allowWarning: true,
                                        onSuccess: function (){
                                            self.unselectRow();
                                        }
                                    });
                                }
                            }
                        });
                    });
                } else {
                    self.trigger_up('add_record', {context: context && [context]}); // TODO write a test, the deferred was not considered
                }
            });
        },

        /**
         * Will try to get the pricelist_id value from the parent sale_order form
         *
         * @private
         * @returns {integer} pricelist_id's id
         */
        _getPricelistId: function () {
            var saleOrderForm = this.getParent() && this.getParent().getParent();
            var stateData = saleOrderForm && saleOrderForm.state && saleOrderForm.state.data;
            var pricelist_id = stateData.pricelist_id && stateData.pricelist_id.data && stateData.pricelist_id.data.id;

            return pricelist_id;
        },

        /**
         * Will map the products to appropriate record objects that are
         * ready for the default_get
         *
         * @private
         * @param {Array} products The products to transform into records
         */
        _productsToRecords: function (products) {
            var records = [];
            _.each(products, function (product){
                var record = {
                    default_product_id: product.product_id,
                    default_product_uom_qty: product.quantity
                };

                if (product.no_variant_attribute_values) {
                    var default_product_no_variant_attribute_values = [];
                    _.each(product.no_variant_attribute_values, function (attribute_value) {
                            default_product_no_variant_attribute_values.push(
                                [4, parseInt(attribute_value.value)]
                            );
                    });
                    record['default_product_no_variant_attribute_value_ids']
                        = default_product_no_variant_attribute_values;
                }

                if (product.product_custom_attribute_values) {
                    var default_custom_attribute_values = [];
                    _.each(product.product_custom_attribute_values, function (attribute_value) {
                        default_custom_attribute_values.push(
                                [0, 0, {
                                    attribute_value_id: attribute_value.attribute_value_id,
                                    custom_value: attribute_value.custom_value
                                }]
                            );
                    });
                    record['default_product_custom_attribute_value_ids']
                        = default_custom_attribute_values;
                }

                records.push(record);
            });

            return records;
        },

        /**
         * @private
         * @param {keyEvent} event
         */
        _onKeyUp: function (event) {
            var value = $(event.currentTarget).val().toLowerCase();
            var count_row = 0;
            var $el = $(this.$el)
            $(event.currentTarget).parent().parent().parent().parent().find('.o_data_row').filter(function () {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
                count_row = $(this).text().toLowerCase().indexOf(value) > -1 ? count_row+1 : count_row
            });
            $el.find('.oe_row_count').text('')
            $el.find('.oe_row_count').text('Total Row: ' + count_row)
        },
    });

    // We create a custom widget because this is the cleanest way to do it:
    // to be sure this custom code will only impact selected fields having the widget
    // and not applied to any other existing ListRenderer.
    var SectionAndNoteFieldOne2Many = FieldOne2Many.extend({

        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function () {
            if (this.view.arch.tag === 'tree') {
                return SectionAndNoteListRenderer;
            }
            return this._super.apply(this, arguments);
        },
    });

    // This is a merge between a FieldText and a FieldChar.
    // We want a FieldChar for section,
    // and a FieldText for the rest (product and note).
    var SectionAndNoteFieldText = function (parent, name, record, options) {
        var isSection = record.data.display_type === 'line_section';
        var Constructor = isSection ? FieldChar : FieldText;
        return new Constructor(parent, name, record, options);
    };

    fieldRegistry.add('section_and_note_one2many_field_search', SectionAndNoteFieldOne2Many);

    return {
        SectionAndNoteListRenderer: SectionAndNoteListRenderer,
        SectionAndNoteFieldOne2Many: SectionAndNoteFieldOne2Many,
    }
});
