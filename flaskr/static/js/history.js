document.addEventListener("DOMContentLoaded", function () {
  // Fetch history data and render the chart/table
  fetch("/api/get-history")
    .then(response => response.json())
    .then(data => {
      if (data.history.length > 0) {
        let tableBody = document.querySelector("#historyTable tbody");
        let dates = [];
        let calories = [];
        let firstDate = new Date(data.history[0].date);

        // Set Month & Year Header
        let monthYear = firstDate.toLocaleString("default", { month: "long", year: "numeric" });
        document.getElementById("monthYear").innerText = monthYear;

        data.history.forEach(record => {
          let recordDate = new Date(record.date);
          let formattedDate = recordDate.toLocaleString("default", { month: "long", day: "numeric", year: "numeric" });

          dates.push(recordDate.getDate()); // Only show day in chart
          calories.push(record.total_calories);

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
          tableBody.innerHTML += row;
        });

        // Render calorie chart
        const ctx = document.getElementById("calorieChart").getContext("2d");
        new Chart(ctx, {
          type: "line",
          data: {
            labels: dates,
            datasets: [{
              label: "Calorie Intake",
              data: calories,
              borderColor: "rgba(255, 255, 255, 0.8)", // Light line color
              backgroundColor: "rgba(108, 119, 64, 0.3)",
              borderWidth: 2,
              fill: true
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true
              }
            }
          }
        });
      }
    })
    .catch(error => console.error("Error fetching history:", error));
});

function viewDetails(date) {
  // Set the modal title with the selected date
  document.getElementById("modalDate").innerText = `Details for ${new Date(date).toLocaleString("default", { month: "long", day: "numeric", year: "numeric" })}`;
  document.getElementById("modalDetails").innerHTML = "";

  // Fetch detailed calorie intake data for the selected date
  fetch(`/api/get-record?date=${date}`)
    .then(response => response.json())
    .then(data => {
      if (data.details) {
        data.details.forEach(item => {
          let row = `<tr>
              <td>${item.food_name}</td>
              <td>${item.servings}</td>
              <td>${item.base_calorie}</td>
              <td>${item.total_calories}</td>
          </tr>`;
          document.getElementById("modalDetails").innerHTML += row;
        });
      }
    })
    .catch(error => console.error("Error fetching details:", error));

  // Show the modal
  var detailsModal = new bootstrap.Modal(document.getElementById("detailsModal"));
  detailsModal.show();

  // Close modal manually when "Close" button is clicked
  document.querySelector("#detailsModal .btn-secondary").addEventListener("click", function () {
    detailsModal.hide();
  });
}
