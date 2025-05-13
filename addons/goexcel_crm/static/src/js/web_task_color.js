odoo.define('goexcel_crm.web_task_color', function (require) {
    'use strict';

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        _render: function(){
            this._super.apply(this, arguments);
            if (this.modelName === 'crm.lead' && this.recordData.stage_color) {
                var $record = this.$el.css("background-color", this.recordData.stage_color || 'white');
            }
            else {
                this._super.apply(this, arguments);
            }
        }
    });

});