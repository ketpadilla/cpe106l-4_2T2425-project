/**
 * Calculates the recommended daily calorie intake based on user inputs.
 * This function uses the Harris-Benedict equation to calculate the Basal Metabolic Rate (BMR)
 * and adjusts it based on the user's activity level. It also calculates the daily calorie intake
 * required to reach a goal weight (weight loss, weight gain, or maintenance).
 * The result is displayed on the page and sent to the server for storage.
 */
function calculateCalorieIntake() {
    // Get the user's date of birth (DOB) and calculate their age
    const dobElem = document.getElementById('dobText');
    let age = 30; // Default age if DOB is not found or invalid
    if (dobElem) {
        const dobStr = dobElem.innerText;
        const dobDate = new Date(dobStr);
        if (!isNaN(dobDate)) {
            const diffMs = Date.now() - dobDate.getTime();
            const diffDate = new Date(diffMs);
            age = Math.abs(diffDate.getUTCFullYear() - 1970);
        }
    }

    // Display the calculated age
    document.getElementById('ageDisplay').innerText = `Age: ${age}`;

    // Get the user's sex (default to male if not found)
    const sexElem = document.getElementById('sexText');
    let sex = 'male'; // Default to male if not found
    if (sexElem) {
        sex = sexElem.innerText.toLowerCase();
    }

    // Get the user's weight from either the input field or the displayed text
    const weightInput = document.getElementById('weightInput');
    const weightText = document.getElementById('weightText');
    let weight = weightInput && weightInput.value ? parseFloat(weightInput.value) : parseFloat(weightText.innerText);

    // Get the user's height from either the input field or the displayed text
    const heightInput = document.getElementById('heightInput');
    const heightText = document.getElementById('heightText');
    let height = heightInput && heightInput.value ? parseFloat(heightInput.value) : parseFloat(heightText.innerText);

    // Calculate BMI (Body Mass Index)
    let bmi = weight / Math.pow(height / 100, 2);

    // Get the user's activity level and determine the activity factor
    const activitySelect = document.getElementById('activityLevelSelect');
    let activityFactor = 1.2; // Default to sedentary
    if (activitySelect) {
        const activityValue = activitySelect.value;
        if (activityValue === "sedentary") {
            activityFactor = 1.2;
        } else if (activityValue === "light_activity") {
            activityFactor = 1.375;
        } else if (activityValue === "moderate_activity") {
            activityFactor = 1.55;
        } else if (activityValue === "very_active") {
            activityFactor = 1.725;
        } else if (activityValue === "extremely_active") {
            activityFactor = 1.9;
        }
    }

    // Calculate Basal Metabolic Rate (BMR) using the Harris-Benedict equation
    let bmr;
    if (sex === "female") {
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161; // Formula for females
    } else {
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5; // Formula for males
    }

    // Calculate maintenance calories based on BMR and activity factor
    let maintenance = bmr * activityFactor;

    // Get the user's goal weight and validate it
    const goalWeightInput = document.getElementById('goalWeightInput');
    const goalWeight = parseFloat(goalWeightInput.value);
    const calorieDeficitPerDay = 500; // 500 calories deficit per day for weight loss (0.5 kg per week)
    const calorieSurplusPerDay = 500; // 500 calories surplus per day for weight gain (0.5 kg per week)
    const caloriesPerKg = 7700; // Approximate calories in 1 kg of body weight

    if (isNaN(goalWeight)) {
        document.getElementById('calorieResult').innerText = 'Please enter a valid goal weight.';
        return;
    }

    // Calculate the weight difference and total calories needed to reach the goal
    let weightDifference = goalWeight - weight;
    let totalCaloriesToChange = Math.abs(weightDifference) * caloriesPerKg;
    let daysToReachGoal = Math.ceil(totalCaloriesToChange / calorieDeficitPerDay);
    let dailyCalorieIntake;

    // Determine the daily calorie intake based on the goal weight
    if (goalWeight < weight) {
        // Weight loss scenario
        dailyCalorieIntake = maintenance - calorieDeficitPerDay;
        document.getElementById('calorieResult').innerHTML = `Daily Intake To Reach Goal by ${daysToReachGoal} days: ${dailyCalorieIntake.toFixed(2)} calories<br>Weight Loss Scenario`;
    } else if (goalWeight > weight) {
        // Weight gain scenario
        dailyCalorieIntake = maintenance + calorieSurplusPerDay;
        document.getElementById('calorieResult').innerHTML = `Daily Intake To Reach Goal by ${daysToReachGoal} days: ${dailyCalorieIntake.toFixed(2)} calories<br>Weight Gain Scenario`;
    } else {
        // Maintenance scenario
        dailyCalorieIntake = maintenance;
        document.getElementById('calorieResult').innerHTML = `Maintenance Daily Calorie Intake: ${dailyCalorieIntake.toFixed(2)} calories<br>Maintenance Scenario`;
    }

    // Display the recommended daily calorie intake
    document.getElementById('recommendedCalorieIntakeText').innerText = dailyCalorieIntake.toFixed(2);

    // Send the recommended calorie intake to the server for storage
    fetch('/update-calorie-intake/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ recommended_calorie_intake: dailyCalorieIntake.toFixed(2) }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            console.log("Calorie intake updated:", data.recommended_calorie_intake);
        } else {
            console.error("Failed to update calorie intake:", data.error);
        }
    })
    .catch(error => console.error("Error:", error));
}
