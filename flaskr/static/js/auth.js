/**
 * Handles the submission of the login form.
 * This script prevents the default form submission, sends an AJAX request to the server,
 * and handles the response by either redirecting the user or displaying an error message.
 */
$("form[name=login_form]").submit(function(e) {
  // Prevent the default form submission behavior
  e.preventDefault();

  // Get the form element and serialize its data
  var $form = $(this);
  var data = $form.serialize();

  // Send an AJAX POST request to the server
  $.ajax({
    url: "/sign-in/", // The URL to send the request to
    type: "POST", // The HTTP method to use
    data: data, // The form data to send
    dataType: "json", // The expected data type of the response
    success: function(resp) {
      // On success, redirect the user to their profile page
      window.location.href = "/user/" + resp.name + "/";
    },
    error: function(resp) {
      // On error, display the error message to the user
      $(".error-message").text(resp.responseJSON.error).show();
    }
  });
});
