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
                alert('Food item added successefully')
                $('#regFoodModal').modal('hide');
                $('#customFoodForm')[0].reset();    
            },
            error: function(error){
                alert('Failed to add food item. Try again.')
            }
        });
    });
});