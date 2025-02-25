function calculateCalorieIntake() {
    // Get age from the date of birth element.
    const dobElem = document.getElementById('dobText');
    let age = 30; // default age if parsing fails
    if (dobElem) {
        const dobStr = dobElem.innerText;
        const dobDate = new Date(dobStr);
        if (!isNaN(dobDate)) {
            const diffMs = Date.now() - dobDate.getTime();
            const diffDate = new Date(diffMs); 
            age = Math.abs(diffDate.getUTCFullYear() - 1970);
        }
    }

    // Get sex from the corresponding element (expects "Male" or "Female").
    const sexElem = document.getElementById('sexText');
    let sex = 'male'; // default to male if not found
    if (sexElem) {
        sex = sexElem.innerText.toLowerCase();
    }

    // Get weight (kg) from input or text.
    const weightInput = document.getElementById('weightInput');
    const weightText = document.getElementById('weightText');
    let weight = weightInput && weightInput.value ? parseFloat(weightInput.value) : parseFloat(weightText.innerText);

    // Get height (cm) from input or text.
    const heightInput = document.getElementById('heightInput');
    const heightText = document.getElementById('heightText');
    let height = heightInput && heightInput.value ? parseFloat(heightInput.value) : parseFloat(heightText.innerText);

    // Calculate BMI.
    let bmi = weight / Math.pow(height / 100, 2);

    // Get activity factor from the activity level text.
    const activityElem = document.getElementById('activityLevelText');
    let activityFactor = 1.2; // default activity factor
    if (activityElem) {
        const activityStr = activityElem.innerText.toLowerCase();
        if (activityStr.includes("sedentary")) {
            activityFactor = 1.2;
        } else if (activityStr.includes("lightly")) {
            activityFactor = 1.375;
        } else if (activityStr.includes("moderately")) {
            activityFactor = 1.55;
        } else if (activityStr.includes("very active")) {
            activityFactor = 1.725;
        } else if (activityStr.includes("extremely active")) {
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

    // Calculate maintenance calories.
    let maintenance = bmr * activityFactor;
    let recommended;
    let category = "";
    
    // Adjust based on BMI.
    if (bmi > 25) {
        // Overweight: subtract a deficit of 500 calories.
        recommended = maintenance - 500;
        category = "Overweight (deficit of 500 calories applied)";
    } else if (bmi < 18.5) {
        // Underweight: add a surplus of 500 calories.
        recommended = maintenance + 500;
        category = "Underweight (surplus of 500 calories applied)";
    } else {
        // Normal weight: maintenance.
        recommended = maintenance;
        category = "Normal weight (maintenance calories)";
    }

    // Display the result.
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.innerText =
        "Category: " + category + "\n" +
        "Recommended Daily Calorie Intake: " + recommended.toFixed(2) + " calories.";
}
