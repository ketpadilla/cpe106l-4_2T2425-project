$(document).ready(function() {
  let $passwordInput = $("#password");
  let $messageBox = $("#message");
  let $letter = $("#letter");
  let $capital = $("#capital");
  let $number = $("#number");
  let $special = $("#special");
  let $length = $("#length");

  // Show message box when password field is focused
  $passwordInput.focus(function() {
    $messageBox.show();
  });

  // Hide message box when password field loses focus
  $passwordInput.blur(function() {
    $messageBox.hide();
  });

  // Validate password on keyup
  $passwordInput.on("keyup", function() {
    let value = $(this).val();

    validateField(value, /[a-z]/, $letter);
    validateField(value, /[A-Z]/, $capital);
    validateField(value, /[0-9]/, $number);
    validateField(value, /[@$!%*?&]/, $special);
    validateField(value.length >= 8, true, $length);
  });

  /**
   * Validates if a condition is met and updates the UI accordingly
   * @param {string} value - The input value
   * @param {RegExp|boolean} pattern - The pattern to match or boolean condition
   * @param {jQuery} element - The target element to update
   */
  function validateField(value, pattern, element) {
    if (typeof pattern === "boolean" ? pattern : value.match(pattern)) {
      element.removeClass("invalid").addClass("valid");
    } else {
      element.removeClass("valid").addClass("invalid");
    }
  }
});
