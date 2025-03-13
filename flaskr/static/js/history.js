/**
 * Fetches history data from the server and renders the calorie chart and table.
 * This script retrieves past calorie intake records, displays them in a table,
 * and plots the data on a line chart for visualization.
 */
document.addEventListener("DOMContentLoaded", function () {
  // Fetch history data and render the chart/table
  fetch("/api/get-history")
    .then(response => response.json())
    .then(data => {
      if (data.history.length > 0) {
        let tableBody = document.querySelector("#historyTable tbody"); // Select table body
        let dates = []; // Array to store date labels for the chart
        let calories = []; // Array to store calorie values for the chart
        let firstDate = new Date(data.history[0].date);

        // Set Month & Year Header in the UI
        let monthYear = firstDate.toLocaleString("default", { month: "long", year: "numeric" });
        document.getElementById("monthYear").innerText = monthYear;

        // Loop through history data and populate the table and chart
        data.history.forEach(record => {
          let recordDate = new Date(record.date);
          let formattedDate = recordDate.toLocaleString("default", { month: "long", day: "numeric", year: "numeric" });

          dates.push(recordDate.getDate()); // Extract only the day for chart labels
          calories.push(record.total_calories); // Store calorie data

          // Create a new row for the history table
          let row = `<tr>
              <td>${formattedDate}</td>
              <td>${record.total_calories}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-primary"  
                        onclick="viewDetails('${record.date}')">
                  View Details
                </button>
              </td>
          </tr>`;
          tableBody.innerHTML += row; // Append row to the table
        });

        // Render the calorie intake chart using Chart.js
        const ctx = document.getElementById("calorieChart").getContext("2d");
        new Chart(ctx, {
          type: "line", // Chart type
          data: {
            labels: dates, // X-axis labels (days)
            datasets: [{
              label: "Calorie Intake", // Chart label
              data: calories, // Y-axis data
              borderColor: "rgba(255, 255, 255, 0.8)", // Light-colored line
              backgroundColor: "rgba(108, 119, 64, 0.3)", // Light fill under the line
              borderWidth: 2,
              fill: true // Enable area fill
            }]
          },
          options: {
            responsive: true, // Ensure chart adapts to screen size
            maintainAspectRatio: false, // Allow dynamic resizing
            scales: {
              y: {
                beginAtZero: true // Ensure y-axis starts at zero
              }
            }
          }
        });
      }
    })
    .catch(error => console.error("Error fetching history:", error)); // Handle errors
});

/**
 * Displays detailed calorie intake information for a selected date.
 * Fetches detailed records from the server and updates the modal content.
 *
 * @param {string} date - The selected date in string format (YYYY-MM-DD).
 */
function viewDetails(date) {
  // Set the modal title with the selected date
  document.getElementById("modalDate").innerText = `Details for ${new Date(date).toLocaleString("default", { month: "long", day: "numeric", year: "numeric" })}`;
  document.getElementById("modalDetails").innerHTML = ""; // Clear previous details

  // Fetch detailed calorie intake data for the selected date
  fetch(`/api/get-record?date=${date}`)
    .then(response => response.json())
    .then(data => {
      if (data.details) {
        // Loop through detailed records and create table rows
        data.details.forEach(item => {
          let row = `<tr>
              <td>${item.food_name}</td>
              <td>${item.servings}</td>
              <td>${item.base_calorie}</td>
              <td>${item.total_calories}</td>
          </tr>`;
          document.getElementById("modalDetails").innerHTML += row; // Append row to modal table
        });
      }
    })
    .catch(error => console.error("Error fetching details:", error)); // Handle errors

  // Show the modal with the retrieved details
  var detailsModal = new bootstrap.Modal(document.getElementById("detailsModal"));
  detailsModal.show();

  // Close modal manually when the "Close" button is clicked
  document.querySelector("#detailsModal .btn-secondary").addEventListener("click", function () {
    detailsModal.hide();
  });
}
