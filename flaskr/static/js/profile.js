function enableEditing() {
  ["name", "email", "dob", "weight", "height"].forEach(field => {
    document.getElementById(field + "Text").classList.add("d-none");
    document.getElementById(field + "Input").classList.remove("d-none");
  });

  document.getElementById("sexText").classList.add("d-none");
  document.getElementById("sexSelect").classList.remove("d-none");

  document.getElementById("activityLevelText").classList.add("d-none");
  document.getElementById("activityLevelSelect").classList.remove("d-none");

  document.getElementById("editButton").classList.add("d-none");
  document.getElementById("saveButton").classList.remove("d-none");
  document.getElementById("cancelButton").classList.remove("d-none");
}

function disableEditing() {
  ["name", "email", "dob", "weight", "height"].forEach(field => {
    document.getElementById(field + "Text").classList.remove("d-none");
    document.getElementById(field + "Input").classList.add("d-none");
  });

  document.getElementById("sexText").classList.remove("d-none");
  document.getElementById("sexSelect").classList.add("d-none");

  document.getElementById("activityLevelText").classList.remove("d-none");
  document.getElementById("activityLevelSelect").classList.add("d-none");

  document.getElementById("editButton").classList.remove("d-none");
  document.getElementById("saveButton").classList.add("d-none");
  document.getElementById("cancelButton").classList.add("d-none");
}