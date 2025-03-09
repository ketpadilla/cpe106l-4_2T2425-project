let calorieChart;

document.addEventListener("DOMContentLoaded", function () {
  fetch("/api/user-calories")
    .then((response) => response.json())
    .then((data) => {
      if (!data.error) {
        document.getElementById("consumedCalories").textContent = data.total_calories;
        document.getElementById("recommendedCalories").textContent = data.recommended_calories;
      }

      if (data.error) {
        console.error("Error fetching data:", data.error);
        return;
      }

      let recommendedCalories = data.recommended_calories;
      let consumedCalories = data.total_calories;
      let remainingCalories = Math.max(recommendedCalories - consumedCalories, 0);
      let exceededCalories = Math.max(consumedCalories - recommendedCalories, 0);

      document.getElementById("consumedCalories").textContent = consumedCalories;

      if (data.consumed.length === 0) {
        let noFoodModal = new bootstrap.Modal(document.getElementById("noFoodModal"));
        noFoodModal.show();

        document.querySelector("#noFoodModal .btn-secondary").addEventListener("click", function () {
          noFoodModal.hide();
        });        
      }      

      let chartElement = document.getElementById("calorieChart");

      if (chartElement) {
        calorieChart = new Chart(chartElement.getContext("2d"), {
          type: "doughnut",
          data: {
            labels: ["Consumed", "Remaining", "Exceeded"],
            datasets: [
              {
                data: [consumedCalories, remainingCalories, exceededCalories],
                backgroundColor: ["#007bff", "rgba(0, 123, 255, 0.3)", "#dc3545"],
              },
            ],
          },
          options: {
            responsive: true,
            legend: { display: false },
          },
        });
      }

      fetch("/api/get-daily-intake")
        .then((response) => response.json())
        .then((data) => {
          let foodList = document.getElementById("food-list-today");
          foodList.innerHTML = "";

          if (data.foods.length === 0) {
            foodList.innerHTML = "<p class='text-muted'>No food entries for today.</p>";
            return;
          }

          let expectedMealCalories = recommendedCalories / 3;

          data.foods.forEach((food) => {
            let servings = food.servings || 1;
            let baseCalories = food.calories;
            let totalCalories = baseCalories * servings;

            let calorieClass = "text-success";
            if (totalCalories > expectedMealCalories * 1.2) {
              calorieClass = "text-danger";
            } else if (totalCalories > expectedMealCalories * 1.1) {
              calorieClass = "text-warning";
            }

            let foodItem = document.createElement("div");
            foodItem.className = "d-flex justify-content-between align-items-center border-bottom py-3";

            foodItem.innerHTML = `
              <div class="flex-grow-1">
                <p class="m-0 fw-bold">${food.name}</p>
                <span class="text-muted">Calories per Serving: <span class="text-info">${baseCalories} kcal</span></span><br>
                <span class="text-muted">Total Calories: <span class="${calorieClass}" id="total-calories-${food.fdcId}">${totalCalories} kcal</span></span><br>
                <span class="text-muted">Serving Size: <span class="text-warning">${food.serving_size}</span></span>
                ${food.brand ? `<br><small class="text-muted">Brand: ${food.brand}</small>` : ""}
              </div>
              <div class="d-flex flex-column align-items-stretch ml-3" style="width: 100px;">
                <input type="number" value="${servings}" min="1" class="form-control text-center servings-input" 
                  data-fdcid="${food.fdcId}" data-base-calories="${baseCalories}">
                <button class="btn btn-danger btn-sm mt-2" onclick="removeFood('${food.fdcId}', this)">Remove</button>
              </div>
            `;

            foodList.appendChild(foodItem);
          });

          document.querySelectorAll(".servings-input").forEach((input) => {
            input.addEventListener("input", function () {
              let fdcId = this.getAttribute("data-fdcid");
              let baseCalories = parseFloat(this.getAttribute("data-base-calories"));
              let newServings = Math.max(1, parseInt(this.value) || 1);
              updateServings(fdcId, newServings, baseCalories);
            });
          });
        })
        .catch((error) => console.error("Error fetching daily intake:", error));
    })
    .catch((error) => console.error("Error loading calorie data:", error));
});

function updateServings(fdcId, newServings, baseCalories) {
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

      let totalCaloriesElementForFood = document.getElementById(`total-calories-${fdcId}`);
      let totalCaloriesForFood = newServings * baseCalories;
      if (totalCaloriesElementForFood) {
        totalCaloriesElementForFood.textContent = `${totalCaloriesForFood} kcal`;

        let recommendedCalories = data.recommended_calories;
        let expectedMealCalories = recommendedCalories / 3;
        let calorieClass = "text-success";
        if (totalCaloriesForFood > expectedMealCalories * 1.2) {
          calorieClass = "text-danger";
        } else if (totalCaloriesForFood > expectedMealCalories * 1.1) {
          calorieClass = "text-warning";
        }
        totalCaloriesElementForFood.className = calorieClass;
      }

      updateConsumedCaloriesDisplay(data.new_total_calories, data.recommended_calories);
    })
    .catch((error) => console.error("Error updating servings:", error));
}

function updateConsumedCaloriesDisplay(newConsumedCalories, recommendedCalories) {
  let consumedCaloriesElement = document.getElementById("consumedCalories");
  
  if (consumedCaloriesElement) {
    consumedCaloriesElement.textContent = newConsumedCalories;

    // Remove previous classes
    consumedCaloriesElement.classList.remove("text-success", "text-warning", "text-danger");

    // Determine new class based on calorie intake
    let percentage = (newConsumedCalories / recommendedCalories) * 100;
    if (percentage <= 100) {
      consumedCaloriesElement.classList.add("text-success");
    } else if (percentage > 100 && percentage <= 120) {
      consumedCaloriesElement.classList.add("text-warning");
    } else {
      consumedCaloriesElement.classList.add("text-danger");
    }
  }

  let remainingCalories = Math.max(recommendedCalories - newConsumedCalories, 0);
  let exceededCalories = Math.max(newConsumedCalories - recommendedCalories, 0);

  if (calorieChart) {
    calorieChart.data.datasets[0].data = [newConsumedCalories, remainingCalories, exceededCalories];
    calorieChart.update();
  }
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

      // Remove the item from UI
      let foodItem = button.closest(".d-flex.justify-content-between");
      if (foodItem) {
        foodItem.remove();
      }

      // Check if food list is now empty and show a message
      let foodList = document.getElementById("food-list-today");
      if (!foodList.querySelector(".d-flex.justify-content-between")) {
        foodList.innerHTML = "<p class='text-muted'>No food entries for today.</p>";
      }

      // Fetch updated calorie data from /api/user-calories
      fetch("/api/user-calories")
        .then((response) => response.json())
        .then((caloriesData) => {
          if (caloriesData.error) {
            console.error("Error fetching updated calorie data:", caloriesData.error);
            return;
          }

          // Update the calorie display and chart with the latest values
          updateConsumedCaloriesDisplay(
            caloriesData.total_calories,
            caloriesData.recommended_calories
          );
        })
        .catch((error) => console.error("Error fetching user calories:", error));
    })
    .catch((error) => console.error("Error removing food:", error));
}
