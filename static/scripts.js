// var order_amount = document.getElementById("oo").value
// var discount = document.getElementById("voucher").value;
// let btn = document.getElementById("voucher")


$(document).ready(function() {
    $("#payment_type_1").on("click", function(){
        $("#card_form").hide();
     });
     
    $("#payment_type_2").on("click", function(){
        $("#card_form").show(); 
    });

    $("#voucher").on("change", function(){
        var order_amount = document.getElementById("order_total").value
        var discount = document.getElementById("voucher").value;

        if (discount == "No Voucher") {
            document.getElementById("total_payment").value = order_amount;
        } else if (discount == "5% Off") {
            order_amount = order_amount * 0.95;
            order_amount = order_amount.toFixed(2)
            document.getElementById("total_payment").value = order_amount;
        } else if (discount == "10% Off") {
            order_amount = order_amount * 0.90;
            order_amount = order_amount.toFixed(2)
            document.getElementById("total_payment").value = order_amount;
        } else if (discount == "15% Off") {
            order_amount = order_amount * 0.85;
            order_amount = order_amount.toFixed(2)
            document.getElementById("total_payment").value = order_amount;
        } else if (discount == "20% Off") {
            order_amount = order_amount * 0.80;
            order_amount = order_amount.toFixed(2)
            document.getElementById("total_payment").value = order_amount;
        } else if (discount == "25% Off") {
            order_amount = order_amount * 0.75;
            order_amount = order_amount.toFixed(2)
            document.getElementById("total_payment").value = order_amount;
        }       
    })

})