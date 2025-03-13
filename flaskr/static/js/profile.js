/**
 * Enables editing mode for user profile fields.
 * Hides the static text values and shows input fields for editing.
 * Also adjusts visibility of action buttons.
 */
function enableEditing() {
  // Toggle visibility for text and input fields of basic user details
  ["name", "email", "dob", "weight", "height"].forEach(field => {
    document.getElementById(field + "Text").classList.add("d-none");  // Hide static text
    document.getElementById(field + "Input").classList.remove("d-none");  // Show input field
  });

  // Toggle visibility for gender selection
  document.getElementById("sexText").classList.add("d-none");
  document.getElementById("sexSelect").classList.remove("d-none");

  // Toggle visibility for activity level selection
  document.getElementById("activityLevelText").classList.add("d-none");
  document.getElementById("activityLevelSelect").classList.remove("d-none");

  // Hide "Edit" button and show "Save" and "Cancel" buttons
  document.getElementById("editButton").classList.add("d-none");
  document.getElementById("saveButton").classList.remove("d-none");
  document.getElementById("cancelButton").classList.remove("d-none");
}

/**
 * Disables editing mode and restores static text values.
 * Hides input fields and restores the original display.
 * Also resets visibility of action buttons.
 */
function disableEditing() {
  // Toggle visibility for text and input fields of basic user details
  ["name", "email", "dob", "weight", "height"].forEach(field => {
    document.getElementById(field + "Text").classList.remove("d-none");  // Show static text
    document.getElementById(field + "Input").classList.add("d-none");  // Hide input field
  });

  // Toggle visibility for gender selection
  document.getElementById("sexText").classList.remove("d-none");
  document.getElementById("sexSelect").classList.add("d-none");

  // Toggle visibility for activity level selection
  document.getElementById("activityLevelText").classList.remove("d-none");
  document.getElementById("activityLevelSelect").classList.add("d-none");

  // Show "Edit" button and hide "Save" and "Cancel" buttons
  document.getElementById("editButton").classList.remove("d-none");
  document.getElementById("saveButton").classList.add("d-none");
  document.getElementById("cancelButton").classList.add("d-none");
}
