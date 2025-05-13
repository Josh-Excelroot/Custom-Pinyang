odoo.define('dynamic_date_filter.search_date_filters', function(require) {
  "use strict";

  var core = require('web.core');
  var filters = require('web.search_filters');

  var _t = core._t;
  filters.ExtendedSearchProposition.include({
    select_field: function(field) {
      this._super.apply(this, arguments);
      this.is_date = field.type == 'date' || field.type == 'datetime';
      this.$value = this.$el.find('.searchview_extended_prop_value, .o_searchview_extended_prop_value');
      if (this.is_date) {
        this.add_date_range_types_operator();
      }
    },

    add_date_range_types_operator: function() {
      var self = this;
//      $('<option>', { value: 'today' })
//        .text(_('Today'))
//        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
//      $('<option>', { value: 'yesterday' })
//        .text(_('Yesterday'))
//        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
//      $('<option>', { value: 'tomorrow' })
//        .text(_('Tomorrow'))
//        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'current_week' })
        .text(_('Current Week'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'next_week' })
        .text(_('Next Week'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'last_week' })
        .text(_('Last Week'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'current_month' })
        .text(_('Current Month'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'next_month' })
        .text(_('Next Month'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
//      $('<option>', { value: 'last_month' })
//        .text(_('Last Month'))
//        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
//      $('<option>', { value: 'current_year' })
//        .text(_('Current Year'))
//        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'next_year' })
        .text(_('Next Year'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'last_year' })
        .text(_('Last Year'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'current_quarter' })
        .text(_('Current Quarter'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'next_quarter' })
        .text(_('Next Quarter'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'last_quarter' })
        .text(_('Last Quarter'))
        .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'last_current_next_quarter' })
                .text(_('Last + Curr. + Next Qtr'))
                .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      $('<option>', { value: 'last_current_next_year' })
                      .text(_('Last + Curr. + Next Year'))
                      .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      // $('<option>', { value: 'last_7days' })
      //   .text(_('Last 7 Days'))
      //   .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
      // $('<option>', { value: 'last_30days' })
      //   .text(_('Last 30 Days'))
      //   .appendTo(self.$el.find('.searchview_extended_prop_op, .o_searchview_extended_prop_op'));
    },

    operator_changed: function(e) {
      var val = $(e.target).val();
//      if (val == 'today') {
//        this.today = true;
//        this.$value.hide();
//        return;
//      } else if (val == 'tomorrow') {
//        this.tomorrow = true;
//        this.$value.hide();
//        return;
//      } else if (val == 'yesterday') {
//        this.yesterday = true;
//        this.$value.hide();
//        return;
//      } else
      if (val == 'current_week') {
        this.current_week = true;
        this.$value.hide();
        return;
      } else if (val == 'next_week') {
        this.next_week = true;
        this.$value.hide();
        return;
      } else if (val == 'last_week') {
        this.last_week = true;
        this.$value.hide();
        return;
      } else if (val == 'current_month') {
        this.current_month = true;
        this.$value.hide();
        return;
      } else if (val == 'next_month') {
        this.next_month = true;
        this.$value.hide();
        return;
      } else if (val == 'last_month') {
        this.last_month = true;
        this.$value.hide();
        return;
      } else if (val == 'current_year') {
        this.current_year = true;
        this.$value.hide();
        return;
      } else if (val == 'next_year') {
        this.next_year = true;
        this.$value.hide();
        return;
      } else if (val == 'last_year') {
        this.last_year = true;
        this.$value.hide();
        return;
      } else if (val == 'current_quarter') {
        this.current_quarter = true;
        this.$value.hide();
        return;
      } else if (val == 'next_quarter') {
        this.next_quarter = true;
        this.$value.hide();
        return;
      } else if (val == 'last_quarter') {
        this.last_quarter = true;
        this.$value.hide();
        return;
      } else if (val == 'last_current_next_quarter') {
        this.last_current_next_quarter = true;
        this.$value.hide();
        return;
     }else if (val == 'last_current_next_year') {
        this.last_current_next_year = true;
        this.$value.hide();
        return;
     }

      // else if (val == 'last_7days') {
      //   this.last_7days = true;
      //   this.$value.hide();
      //   return;
      // } else if (val == 'last_30days') {
      //   this.last_30days = true;
      //   this.$value.hide();
      //   return;
      // }

      this._super.apply(this, arguments);
    },


    get_filter: function() {
      var res = this._super.apply(this, arguments);
//      if (this.today) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().startOf('day')],
//          [this.attrs.selected.name, '<=', moment().endOf('day')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Today";
//      }
//
//      if (this.yesterday) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().add(-1, 'day').startOf('day')],
//          [this.attrs.selected.name, '<=', moment().add(-1, 'day').endOf('day')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Yesterday";
//      }
//      if (this.tomorrow) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().add(1, 'day').startOf('day')],
//          [this.attrs.selected.name, '<=', moment().add(1, 'day').endOf('day')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Tomorrow";
//      }
      if (this.current_week) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().startOf('isoWeek')],
          [this.attrs.selected.name, '<=', moment().endOf('isoWeek')]
        ];
        res.attrs.string = this.attrs.selected.string + " Current Week";
      }
      if (this.next_week) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().add(1, 'weeks').startOf('isoWeek')],
          [this.attrs.selected.name, '<=', moment().add(1, 'weeks').endOf('isoWeek')]
        ];
        res.attrs.string = this.attrs.selected.string + " Next Week";
      }
      if (this.last_week) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().subtract(1, 'weeks').startOf('isoWeek')],
          [this.attrs.selected.name, '<=', moment().subtract(1, 'weeks').endOf('isoWeek')]
        ];
        res.attrs.string = this.attrs.selected.string + " Last Week";
      }

//     ***** start 04-09-2024 - Yulia Lim - Fixed current month timezone bug
//if (this.current_month) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().startOf('month')],
//          [this.attrs.selected.name, '<=', moment().endOf('month')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Current Month";
//      }
      if (this.current_month) {
        const currentMonthUTCOffset = moment().utcOffset(-300).format('MMMM');
        res.attrs.domain = [
            [this.attrs.selected.name, '>=', moment().utcOffset(-300).startOf('month')],
            [this.attrs.selected.name, '<=', moment().utcOffset(-300).endOf('month')]
        ];
        res.attrs.string = this.attrs.selected.string + " Current Month";
      }
      if (this.next_month) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().add(1, 'months').startOf('month')],
          [this.attrs.selected.name, '<=', moment().add(1, 'months').endOf('month')]
        ];
        res.attrs.string = this.attrs.selected.string + " Next Month";
      }
//      if (this.last_month) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().subtract(1, 'months').startOf('month')],
//          [this.attrs.selected.name, '<=', moment().subtract(1, 'months').endOf('month')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Last Month";
//      }

//      if (this.current_year) {
//        res.attrs.domain = [
//          [this.attrs.selected.name, '>=', moment().startOf('year')],
//          [this.attrs.selected.name, '<=', moment().endOf('year')]
//        ];
//        res.attrs.string = this.attrs.selected.string + " Current Year";
//      }
      if (this.next_year) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().add(1, 'years').startOf('year')],
          [this.attrs.selected.name, '<=', moment().add(1, 'years').endOf('year')]
        ];
        res.attrs.string = this.attrs.selected.string + " Next Year";
      }
      if (this.last_year) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().subtract(1, 'years').startOf('year')],
          [this.attrs.selected.name, '<=', moment().subtract(1, 'years').endOf('year')]
        ];
        res.attrs.string = this.attrs.selected.string + " Last Year";
      }

//
      if (this.current_quarter) {
        res.attrs.domain = [
        [this.attrs.selected.name, '>=', moment().startOf('quarter').format('YYYY-MM-DD')],
          [this.attrs.selected.name, '<=', moment().endOf('quarter').format('YYYY-MM-DD')]
        ];
        res.attrs.string = this.attrs.selected.string + " Current Quarter";
      }
      if (this.next_quarter) {
//        res.attrs.domain = [
//            [this.attrs.selected.name, '>=', moment().startOf('quarter')],
//            [this.attrs.selected.name, '<=', moment().endOf('quarter')]
//        ];
        res.attrs.domain = [
           [this.attrs.selected.name, '>=', moment().add(1, 'quarters').startOf('quarter').format('YYYY-MM-DD')],
         [this.attrs.selected.name, '<=', moment().add(1, 'quarters').endOf('quarter').format('YYYY-MM-DD')]
        ];
        res.attrs.string = this.attrs.selected.string + " Next Quarter";
      }
      if (this.last_quarter) {
        res.attrs.domain = [
          [this.attrs.selected.name, '>=', moment().subtract(1, 'quarters').startOf('quarter').format('YYYY-MM-DD')],
        [this.attrs.selected.name, '<=', moment().subtract(1, 'quarters').endOf('quarter').format('YYYY-MM-DD')]
        ];
        res.attrs.string = this.attrs.selected.string + " Last Quarter";
      }
      if (this.last_current_next_quarter) {
          const startOfQuarter = moment().subtract(1, 'quarters').startOf('quarter').format('YYYY-MM-DD');
             const endOfQuarter = moment().add(1, 'quarters').endOf('quarter').format('YYYY-MM-DD');

            res.attrs.domain = [
                [this.attrs.selected.name, '>=', startOfQuarter],
                [this.attrs.selected.name, '<=', endOfQuarter]
            ];
          res.attrs.string = this.attrs.selected.string + " Last + Curr.+ Next Qtr";
      }
      if (this.last_current_next_year) {
              const now = moment();
            const startOfCurrentQuarter = now.startOf('quarter');
            const endOfCurrentQuarter = now.endOf('quarter');

            const startOfLastQuarter = now.subtract(1, 'quarters').startOf('quarter').format('YYYY-MM-DD');
            const endOfLastQuarter = now.subtract(1, 'quarters').endOf('quarter').format('YYYY-MM-DD');

            const startOfNextQuarter = now.add(1, 'quarters').startOf('quarter').format('YYYY-MM-DD');
            const endOfNextQuarter = now.add(1, 'quarters').endOf('quarter').format('YYYY-MM-DD');

            res.attrs.domain = [
                [this.attrs.selected.name, '>=', startOfLastQuarter],
                [this.attrs.selected.name, '<=', endOfNextQuarter]
            ];
            res.attrs.string = this.attrs.selected.string + " Last + Curr.+ Next Year";
      }
      // if (this.last_7days) {
      //   res.attrs.domain = [
      //     [this.attrs.selected.name, '>=', moment().endOf('day')],
      //     [this.attrs.selected.name, '<=', moment().subtract(7, 'days').startOf('day')]
      //   ];
      //   res.attrs.string = this.attrs.selected.string + " Last 7 Days";
      // }
      // if (this.last_30days) {
      //   res.attrs.domain = [
      //     [this.attrs.selected.name, '>=', moment().endOf('day')],
      //     [this.attrs.selected.name, '<=', moment().subtract(30, 'days').startOf('day')]
      //   ];
      //   res.attrs.string = this.attrs.selected.string + " Last 30 Days";
      // }


      return res;
    },

  });
});