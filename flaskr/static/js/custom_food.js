$(document).ready(function() {
    $("#customFoodForm").on("submit", function(event) {
        event.preventDefault();

        let foodName = $("#foodName").val();
        let calories = $("#calories").val();
        let servingSize = $("#servingSize").val();
        let brandOwner = $("#brandOwner").val();
        let customFoodCategory = $("#customFoodCategory").val();
        let ingredients = $("#ingredients").val();

        $.ajax({
            url: "/api/add-custom-food",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                foodName: foodName,
                calories: calories,
                servingSize: servingSize,
                brandOwner: brandOwner,
                customFoodCategory: customFoodCategory,
                ingredients: ingredients
            }),
            success: function(response){
                $('#customFoodMessage').removeClass('alert-danger').addClass('alert-success').text(response.message).show();
                $('#customFoodForm')[0].reset();
            },
            error: function(error){
                let errorMessage = error.responseJSON ? error.responseJSON.error : 'Failed to add food item. Try again.';
                $('#customFoodMessage').removeClass('alert-success').addClass('alert-danger').text(errorMessage).show();
            }
        });
    });
});