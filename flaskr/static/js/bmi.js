let isMetric = true;

/**
 * Calculates the BMI (Body Mass Index) based on the user's weight and height.
 * Updates the BMI result and category on the page.
 */
function calculateBMI() {
  const weightInput = document.getElementById("weight");
  const heightInput = document.getElementById("height");
  const bmiResultElement = document.getElementById("bmiResult");
  const bmiCategoryElement = document.getElementById("bmiCategory");

  let weight = parseFloat(weightInput.value);
  let height = parseFloat(heightInput.value);

  // Reset category color and text
  bmiCategoryElement.style.color = "";
  bmiCategoryElement.innerHTML = "Category:";

  // Convert weight and height to metric units if necessary
  if (!isMetric) {
    weight /= 2.2046226218; // Convert pounds to kilograms
    height *= 0.0254; // Convert inches to meters
  } else {
    height /= 100; // Convert centimeters to meters
  }

  // Check if weight and height are valid
  if (weight > 0 && height > 0) {
    // Calculate BMI and round to 2 decimal places
    const bmi = (weight / (height * height)).toFixed(2);
    bmiResultElement.innerText = bmi;

    // Define BMI categories and their corresponding colors
    const bmiCategories = [
      { limit: 18.5, category: "Underweight", color: "blue" },
      { limit: 24.9, category: "Normal weight", color: "green" },
      { limit: 29.9, category: "Overweight", color: "orange" },
      { limit: Infinity, category: "Obese", color: "red" }
    ];

    // Find the appropriate category for the calculated BMI
    const { category, color } = bmiCategories.find(({ limit }) => bmi < limit);
    bmiCategoryElement.innerHTML = `Category: <span style="color: ${color}">${category}</span>`;
  } else {
    // Display error message if inputs are invalid
    bmiResultElement.innerText = "--";
    bmiCategoryElement.innerText = "Please enter valid values.";
    bmiCategoryElement.style.color = "red";
  }
}

/**
 * Resets the BMI form and result display.
 */
function resetBMI() {
  document.getElementById("bmiForm").reset();
  document.getElementById("bmiResult").innerText = "--";
  document.getElementById("bmiCategory").innerText = "Category:";
  document.getElementById("bmiCategory").style.color = "";
}

/**
 * Toggles between metric and US units for weight and height inputs.
 * Updates the labels and converts existing values if necessary.
 */
function toggleUnits() {
  isMetric = !isMetric;

  // Update the toggle button text
  const toggleButton = document.querySelector(".btn-primary");
  toggleButton.innerText = isMetric ? "Switch to US Units" : "Switch to Metric Units";

  // Get weight and height input elements and their labels
  const weightLabel = document.querySelector("label[for='weight']");
  const heightLabel = document.querySelector("label[for='height']");
  const weightInput = document.getElementById("weight");
  const heightInput = document.getElementById("height");

  if (isMetric) {
    // Switch to metric units
    weightLabel.innerText = "Weight (kg)";
    heightLabel.innerText = "Height (cm)";

    // Convert weight from pounds to kilograms if a value exists
    if (weightInput.value) {
      weightInput.value = (parseFloat(weightInput.value) / 2.2046226218).toFixed(2);
    }

    // Convert height from inches to centimeters if a value exists
    if (heightInput.value) {
      heightInput.value = (parseFloat(heightInput.value) / 0.3937007874).toFixed(2);
    }
  } else {
    // Switch to US units
    weightLabel.innerText = "Weight (lbs)";
    heightLabel.innerText = "Height (in)";

    // Convert weight from kilograms to pounds if a value exists
    if (weightInput.value) {
      weightInput.value = (parseFloat(weightInput.value) * 2.2046226218).toFixed(2);
    }

    // Convert height from centimeters to inches if a value exists
    if (heightInput.value) {
      heightInput.value = (parseFloat(heightInput.value) * 0.3937007874).toFixed(2);
    }
  }
}
