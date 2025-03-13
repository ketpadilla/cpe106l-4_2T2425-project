/**
 * Handles the submission of the custom food form.
 * This script prevents the default form submission, sends an AJAX request to the server
 * to add a custom food item, and displays a success or error message based on the response.
 */
$(document).ready(function() {
    // Attach a submit event handler to the custom food form
    $("#customFoodForm").on("submit", function(event) {
        // Prevent the default form submission behavior
        event.preventDefault();

        // Get the values from the form inputs
        let foodName = $("#foodName").val();
        let calories = $("#calories").val();
        let servingSize = $("#servingSize").val();
        let brandOwner = $("#brandOwner").val();
        let customFoodCategory = $("#customFoodCategory").val();
        let ingredients = $("#ingredients").val();

        // Send an AJAX POST request to the server
        $.ajax({
            url: "/api/add-custom-food", // The URL to send the request to
            type: "POST", // The HTTP method to use
            contentType: "application/json", // The content type of the request
            data: JSON.stringify({ // The data to send, converted to JSON format
                foodName: foodName,
                calories: calories,
                servingSize: servingSize,
                brandOwner: brandOwner,
                customFoodCategory: customFoodCategory,
                ingredients: ingredients
            }),
            success: function(response) {
                // On success, display a success message and reset the form
                $('#customFoodMessage')
                    .removeClass('alert-danger')
                    .addClass('alert-success')
                    .text(response.message)
                    .show();
                $('#customFoodForm')[0].reset(); // Reset the form
            },
            error: function(error) {
                // On error, display an error message
                let errorMessage = error.responseJSON ? error.responseJSON.error : 'Failed to add food item. Try again.';
                $('#customFoodMessage')
                    .removeClass('alert-success')
                    .addClass('alert-danger')
                    .text(errorMessage)
                    .show();
            }
        });
    });
});
