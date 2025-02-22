$("form[name=signup_form]").submit(function(e) {
    var $form = $(this);
    var data = $form.serialize();

    $.ajax({
        url: "/sign-up/",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            console.log(resp);
        },
        error: function(resp) {
            console.log("Error:", resp);
        }
    });

    e.preventDefault();
});
