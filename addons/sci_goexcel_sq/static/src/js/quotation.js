odoo.define('sci_goexcel_sq.quotation', function (require) {
  'use strict';

  //   console.log(rpc);
  $(document).ready(() => {
    var rpc = require('web.rpc');
    console.log('New Running');
    const id = $('.hidden_field').attr('id');
    $('#confirm_button').on('click', () => {
      rpc
        .query({
          model: 'sale.order',
          method: 'action_confirm',
          args: ['id', id],
        })
        .then(() => {
          $('#confirm_button').remove();

          $('#messages').removeClass('hidden').addClass('alert alert-success ');
          $('#messages_content').html(
            'Your sales quotation has been confirmed.'
          );

          setTimeout(() => {
            $('#messages').alert('close');
          }, 5000);
        })
        .fail((err) => {
          $('#messages').removeClass('hidden').addClass('alert alert-danger ');
          $('#messages_content').html(
            "Sorry! your sales quotation hasn't been confirmed."
          );
        });



    });
  });
});
