let isMetric = true;

function calculateBMI() {
  const weightInput = document.getElementById("weight");
  const heightInput = document.getElementById("height");
  const bmiResultElement = document.getElementById("bmiResult");
  const bmiCategoryElement = document.getElementById("bmiCategory");

  let weight = parseFloat(weightInput.value);
  let height = parseFloat(heightInput.value);

  bmiCategoryElement.style.color = "";  
  bmiCategoryElement.innerHTML = "Category:";

  if (!isMetric) {
    weight *= 0.453592; 
    height *= 2.54 / 100; 
  } else {
    height /= 100;
  }

  if (weight > 0 && height > 0) {
    const bmi = (weight / (height * height)).toFixed(2);
    bmiResultElement.innerText = bmi;

    const bmiCategories = [
      { limit: 18.5, category: "Underweight", color: "blue" },
      { limit: 24.9, category: "Normal weight", color: "green" },
      { limit: 29.9, category: "Overweight", color: "orange" },
      { limit: Infinity, category: "Obese", color: "red" }
    ];

    const { category, color } = bmiCategories.find(({ limit }) => bmi < limit);
    bmiCategoryElement.innerHTML = `Category: <span style="color: ${color}">${category}</span>`;
  } else {
    bmiResultElement.innerText = "--";
    bmiCategoryElement.innerText = "Please enter valid values.";
    bmiCategoryElement.style.color = "red";
  }
}

function resetBMI() {
  document.getElementById("bmiForm").reset();
  document.getElementById("bmiResult").innerText = "--";
  document.getElementById("bmiCategory").innerText = "Category:";
  document.getElementById("bmiCategory").style.color = "";
}

function toggleUnits() {
  isMetric = !isMetric;
  
  const toggleButton = document.querySelector(".btn-primary");
  toggleButton.innerText = isMetric ? "Switch to US Units" : "Switch to Metric Units";

  const weightLabel = document.querySelector("label[for='weight']");
  const heightLabel = document.querySelector("label[for='height']");
  const weightInput = document.getElementById("weight");
  const heightInput = document.getElementById("height");

  if (isMetric) {
    weightLabel.innerText = "Weight (kg)";
    heightLabel.innerText = "Height (cm)";

    if (weightInput.value) {
      weightInput.value = (parseFloat(weightInput.value) / 0.453592).toFixed(2);
    }

    if (heightInput.value) {
      heightInput.value = (parseFloat(heightInput.value) / 2.54).toFixed(2);
    }
  } else {
    weightLabel.innerText = "Weight (lbs)";
    heightLabel.innerText = "Height (in)";

    if (weightInput.value) {
      weightInput.value = (parseFloat(weightInput.value) * 0.453592).toFixed(2); 
    }

    if (heightInput.value) {
      heightInput.value = (parseFloat(heightInput.value) * 2.54).toFixed(2);
    }
  }
}