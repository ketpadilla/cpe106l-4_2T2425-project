function calculateCalorieIntake() {
    const dobElem = document.getElementById('dobText');
    let age = 30; 
    if (dobElem) {
        const dobStr = dobElem.innerText;
        const dobDate = new Date(dobStr);
        if (!isNaN(dobDate)) {
            const diffMs = Date.now() - dobDate.getTime();
            const diffDate = new Date(diffMs); 
            age = Math.abs(diffDate.getUTCFullYear() - 1970);
        }
    }

    document.getElementById('ageDisplay').innerText = `Age: ${age}`;

    const sexElem = document.getElementById('sexText');
    let sex = 'male'; // default to male if not found
    if (sexElem) {
        sex = sexElem.innerText.toLowerCase();
    }

    const weightInput = document.getElementById('weightInput');
    const weightText = document.getElementById('weightText');
    let weight = weightInput && weightInput.value ? parseFloat(weightInput.value) : parseFloat(weightText.innerText);

    const heightInput = document.getElementById('heightInput');
    const heightText = document.getElementById('heightText');
    let height = heightInput && heightInput.value ? parseFloat(heightInput.value) : parseFloat(heightText.innerText);

    let bmi = weight / Math.pow(height / 100, 2);

    const activitySelect = document.getElementById('activityLevelSelect');
    let activityFactor = 1.2; // default to sedentary
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

    // Calculate BMR using Harris-Benedict equation.
    // Male: BMR = 10*weight + 6.25*height - 5*age + 5, Female: BMR = 10*weight + 6.25*height - 5*age - 161
    let bmr;
    if (sex === "female") {
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161;
    } else {
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
    }


    let maintenance = bmr * activityFactor;
    const goalWeightInput = document.getElementById('goalWeightInput');
    const goalWeight = parseFloat(goalWeightInput.value);
    const calorieDeficitPerDay = 500; // 0.5 kg per week
    const calorieSurplusPerDay = 500; // 0.5 kg per week
    const caloriesPerKg = 7700; // Approximate calories in 1 kg of body weight

    if (isNaN(goalWeight)) {
        document.getElementById('calorieResult').innerText = 'Please enter a valid goal weight.';
        return;
    }

    let weightDifference = goalWeight - weight;
    let totalCaloriesToChange = Math.abs(weightDifference) * caloriesPerKg;
    let daysToReachGoal = Math.ceil(totalCaloriesToChange / calorieDeficitPerDay);
    let dailyCalorieIntake;

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

    document.getElementById('recommendedCalorieIntakeText').innerText = dailyCalorieIntake.toFixed(2);

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