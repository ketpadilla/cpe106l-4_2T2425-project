$("form[name=login_form]").submit(function(e) {
  e.preventDefault();

  var $form = $(this);
  var data = $form.serialize();

  $.ajax({
    url: "/sign-in/",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      window.location.href = "/user/" + resp.name + "/";
    },
    error: function(resp) {
      $(".error-message").text(resp.responseJSON.error).show();
    }
  });
});
