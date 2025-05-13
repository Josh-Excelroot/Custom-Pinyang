odoo.define('sci_goexcel_sq.lcl-buttons', function (require) {
  'use strict';
    console.log("hello");
  $(document).ready(() => {
    console.log('New Running');
    $('input[type=radio][name=cargo_type]').change(function() {

    var con = "";
    var container_id = "";
    var weight_id = "";
    var type_id = "";
    var len_id = "";
    var height_id = "";
    var width_id = "";
    var weight_id1 = "";
    var quantity_id = "";


    con = $("#con");
    container_id = $("#container_id");
    weight_id =   $("#weight_id");
    type_id = $("#type_id");
    len_id = $("#len_id");
    height_id = $("#height_id");
    width_id =  $("#width_id");
    weight_id1 =$("#weight_id1") ;
    quantity_id = $("#quantity_id");



        if (this.value == 'fcl') {

        $("#weight_id").css("display", "block");
        $("#type_id").css("display", "block");
        $("#container_quantity").css("display", "block");
        $("#container_id").css("display", "block");
        $("#len_id").css("display", "none");
         $("#lcl_length").prop('required',false);
        $("#height_id").css("display", "none");
         $("#lcl_height").prop('required',false);
        $("#width_id").css("display", "none");
         $("#lcl_width").prop('required',false);
        $("#weight_id1").css("display", "none");
         $("#weight").prop('required',false);
         $("#container_quantity").prop('required',false);
         $("#quantity_id").css("display", "none");
          $("#lcl_Weight").prop('required',false);
          $("#lcl_quantity").prop('required',false);



//      $('label[for=container_quantity], input#container_quantity').parent().append();
//        $('label[for=weight], input#weight').parent().append();
//        $('label[for=commodity], select#commodity').parent().append();
//        $('label[for=lcl_height], input#lcl_height').parent().detach();
//        $('label[for=lcl_length], input#lcl_length').parent().detach();
//        $('label[for=lcl_width], input#lcl_width').parent().detach();
//        $('label[for=lcl_weight], input#lcl_weight').parent().detach();
//        $('label[for=lcl_quantity], input#lcl_quantity').parent().detach();






    }else
    {


        $("#con").css("display", "none");
        $("#weight_id").css("display", "none");
        $("#type_id").css("display", "none");
         $("#commodity").prop('required',false);
        $("#len_id").css("display", "block");
         $("#weight").prop('required',false);
        $("#height_id").css("display", "block");
         $("#container_quantity").prop('required',false);
        $("#width_id").css("display", "block");
//         $("#lcl_width").prop('required',false);
        $("#weight_id1").css("display", "block");
//         $("#container_quantity").prop('required',false);
         $("#quantity_id").css("display", "block");
          $("#container_id").css("display", "none");

// $('label[for=container_quantity], input#container_quantity').parent().detach();
//        $('label[for=weight], input#weight').parent().detach();
//        $('label[for=commodity], select#commodity').parent().detach();
//        $('label[for=lcl_height], input#lcl_height').parent().append();
//        $('label[for=lcl_length], input#lcl_length').parent().append();
//        $('label[for=lcl_width], input#lcl_width').parent().append();
//        $('label[for=lcl_weight], input#lcl_weight').parent().append();
//        $('label[for=lcl_quantity], input#lcl_quantity').parent().append();
//







//
//        $("#con").css("display", "none");
//        $("#container_id").css("display", "none");
//        $("#weight_id").css("display", "none");
//        $("#type_id").css("display", "none");
//        $("#len_id").css("display", "block");
//        $("#height_id").css("display", "block");;
//        $("#width_id").css("display", "block");
//        $("#weight_id1").css("display", "block");
//         $("#quantity_id").css("display", "block");

    }
       console.log("alert");



    });
  });

 });
