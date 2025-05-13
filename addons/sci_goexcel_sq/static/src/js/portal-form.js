odoo.define('sci_goexcel_sq.portal-form', function (require) {
  'use strict';

  //   console.log(rpc);
  $(document).ready(() => {
    var rpc = require('web.rpc');
    let i = 1;
    let row;
    $('.add').on('click', (e) => {
      e.preventDefault();
      row = i;
      i = i + 1;
      rpc
        .query({
          model: 'website',
          method: 'get_container_type_portal',
          args: ['id', i],
        })
        .then((data) => {
          $(`
        <tr class="item-${i}">
                                                    <td>
                                                        <h2>Container ${i}</h2>
                                                    </td>
                                                    <td></td>
                                                </tr>
        <tr class="item-${i}">
        <td width="24%">
            <label class="control-label" for="commodity">
                <strong>Container Type</strong>
            </label>
        </td>
        <td width="77%">
            <t t-set="container_types" t-value="website.get_container_type()" />
            <select name="container_type_${i}" class="form-control" id="container-type-${i}" style="width: auto !important" required="True">
                <option value="" selected="True">Select Container Type</option>
                
            </select>
        </td>
    </tr>

    <tr class="item-${i}">
        <td>
            <label class="control-label">
                <strong>Container Quantity</strong>
            </label>
        </td>
        <td>
            <input class="form-control" style="width: auto !important" name="container_quantity_${i}" required="True" t-attf-value="#{container_quantity or ''}" type="number" placeholder="Container Quantity"/>
        </td>
    </tr>

    <tr class="end-row-${i} item-${i}">
        <td>
            <label class="control-label">
                <strong>Weight &#40;kg - cargo only&#41;</strong>
            </label>
        </td>
        <td>
            <input class="form-control" style="width: auto !important" name="weight_${i}" required="True" t-attf-value="#{weight or ''}" type="number" step="any" placeholder="Weight (kg - cargo only)"/>
        </td>
    </tr>`).insertAfter(`.end-row-${row}`);
          data.map((item) => {
            $(`#container-type-${i}`).append(
              `<option value="${item.value}">${item.name}</option>`
            );
          });
        });

      $('#hidden').attr('value', i);
    });
    $('.remove').on('click', (e) => {
      e.preventDefault();
      if (i > 1) {
        document.querySelectorAll(`.item-${i}`).forEach((e) => e.remove());
        i = i - 1;
        $('#hidden').attr('value', i);
      }
    });
  });
});
