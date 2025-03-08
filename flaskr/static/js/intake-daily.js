// Global variables for charts
let consumedChart, remainingChart;

document.addEventListener("DOMContentLoaded", function () {
  fetch("/api/user-calories")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error fetching data:", data.error);
        return;
      }

      let recommendedCalories = data.recommended_calories;
      let consumedCalories = data.total_calories;
      let remainingCalories = Math.max(recommendedCalories - consumedCalories, 0);

      if (data.consumed.length === 0) {
        alert("No food items recorded today. Please add an item to track your calories.");
      }

      // Initialize Charts
      let consumedChartElement = document.getElementById("consumedChart");
      let remainingChartElement = document.getElementById("remainingChart");

      if (consumedChartElement) {
        consumedChart = new Chart(consumedChartElement.getContext("2d"), {
          type: "doughnut",
          data: {
            datasets: [
              {
                data: [consumedCalories, remainingCalories],
                backgroundColor: ["#007bff", "rgba(0, 123, 255, 0.3)"],
              },
            ],
          },
          options: { responsive: true },
        });
      }

      if (remainingChartElement) {
        remainingChart = new Chart(remainingChartElement.getContext("2d"), {
          type: "doughnut",
          data: {
            datasets: [
              {
                data: [remainingCalories, consumedCalories],
                backgroundColor: ["gray", "rgba(128, 128, 128, 0.3)"],
              },
            ],
          },
          options: { responsive: true },
        });
      }

      // Fetch daily intake
      fetch("/api/get-daily-intake")
        .then((response) => response.json())
        .then((data) => {
          let foodList = document.getElementById("food-list-today");
          foodList.innerHTML = ""; // Clear previous entries

          if (data.foods.length === 0) {
            foodList.innerHTML = "<p class='text-muted'>No food entries for today.</p>";
            return;
          }

          let expectedMealCalories = recommendedCalories / 3; // Assume 3 meals a day

          data.foods.forEach((food) => {
            let servings = food.servings || 1; // Use servings directly from the food object
            let totalCalories = food.calories * servings;

            // Determine total calorie color based on expected per-meal intake
            let calorieClass = "text-success"; // Default: Green (within range)
            if (totalCalories > expectedMealCalories * 1.2) {
              calorieClass = "text-danger"; // Red: More than 20% over expected per meal
            } else if (totalCalories > expectedMealCalories * 1.1) {
              calorieClass = "text-warning"; // Orange: 10-20% over expected per meal
            }

            let foodItem = document.createElement("div");
            foodItem.className = "d-flex justify-content-between align-items-center border-bottom py-3";

            foodItem.innerHTML = `
              <div class="flex-grow-1">
                <p class="m-0 fw-bold">${food.name}</p>
                <span class="text-muted">Calories per Serving: <span class="text-info">${food.calories} kcal</span></span><br>
                <span class="text-muted">Total Calories: <span class="${calorieClass}" id="total-calories-${food.fdcId}">${totalCalories} kcal</span></span><br>
                <span class="text-muted">Serving Size: <span class="text-warning">${food.serving_size}</span></span>
                ${food.brand ? `<br><small class="text-muted">Brand: ${food.brand}</small>` : ""}
              </div>
              <div class="d-flex flex-column align-items-stretch ml-3" style="width: 100px;">
                <input type="number" value="${servings}" min="1" class="form-control text-center servings-input" data-fdcid="${food.fdcId}" data-calories="${food.calories}">
                <button class="btn btn-danger btn-sm mt-2" onclick="removeFood('${food.fdcId}', this)">Remove</button>
              </div>
            `;

            foodList.appendChild(foodItem);
          });

          // Add event listener for updating servings
          document.querySelectorAll(".servings-input").forEach((input) => {
            input.addEventListener("input", function () {
              let fdcId = this.getAttribute("data-fdcid");
              let calories = parseFloat(this.getAttribute("data-calories"));
              let newServings = Math.max(1, parseInt(this.value) || 1); // Ensure valid input
              updateServings(fdcId, newServings, calories);
            });
          });
        })
        .catch((error) => console.error("Error fetching daily intake:", error));
    })
    .catch((error) => console.error("Error loading calorie data:", error));
});

function updateServings(fdcId, newServings, calories) {
  fetch("/api/update-daily-intake/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fdcId: fdcId, servings: newServings }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error updating servings:", data.error);
        return;
      }

      // Update the total calories display
      let totalCaloriesElement = document.getElementById("total-calories");
      if (totalCaloriesElement) {
        totalCaloriesElement.textContent = data.new_total_calories;
      }

      // Update the chart data
      let recommendedCalories = data.recommended_calories;
      let consumedCalories = data.new_total_calories;
      let remainingCalories = Math.max(recommendedCalories - consumedCalories, 0);

      if (consumedChart) {
        consumedChart.data.datasets[0].data = [consumedCalories, remainingCalories];
        consumedChart.update();
      }

      if (remainingChart) {
        remainingChart.data.datasets[0].data = [remainingCalories, consumedCalories];
        remainingChart.update();
      }

      // Update the servings for the specific food item
      let totalCaloriesForFood = newServings * calories;
      let totalCaloriesElementForFood = document.getElementById(`total-calories-${fdcId}`);
      if (totalCaloriesElementForFood) {
        totalCaloriesElementForFood.textContent = `${totalCaloriesForFood} kcal`;

        // Update the calorie color based on the new total
        let expectedMealCalories = recommendedCalories / 3;
        let calorieClass = "text-success"; // Default: Green (within range)
        if (totalCaloriesForFood > expectedMealCalories * 1.2) {
          calorieClass = "text-danger"; // Red: More than 20% over expected per meal
        } else if (totalCaloriesForFood > expectedMealCalories * 1.1) {
          calorieClass = "text-warning"; // Orange: 10-20% over expected per meal
        }
        totalCaloriesElementForFood.className = calorieClass;
      }
    })
    .catch((error) => console.error("Error updating servings:", error));
}

function removeFood(fdcId, button) {
  fetch("/api/remove-daily-intake", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fdcId: fdcId }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error removing food:", data.error);
        return;
      }
      button.closest(".d-flex").remove(); // Removes the entire entry
    })
    .catch((error) => console.error("Error removing food:", error));
}