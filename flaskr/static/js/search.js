$(document).ready(function() {
  let currentRequest = null; 

  $('#searchQuery').on('input', function() {
    let query = $(this).val().trim();

    if (query === "") {
      if (currentRequest) {
        currentRequest.abort(); 
      }
      $('#results').empty();
      return;
    }

    $('#results').html("<p>Loading...</p>");

    if (currentRequest) {
      currentRequest.abort();
    }

    currentRequest = $.ajax({
      url: '/api/search-food/',
      type: 'GET',
      data: { query: query },
      success: function(response) {
        let resultsHTML = "";
        if (response.length > 0) {
          resultsHTML = "<ul class='list-group'>";
          response.forEach(item => {
            let brandText = item.brand ? `<small class="text-muted" style="font-size: 12px;">Brand: ${item.brand}</small>` : "";
            let addButtons = userLoggedIn == "true"
            ? `<div class='d-flex flex-column'>
                <button class='btn btn-success btn-sm add-to-daily-intake mb-2' data-fdcid="${item.fdcId}" data-name="${item.name}" data-calories="${item.calories}">
                  ${addIconHTML} Add to Daily Intake
                </button>
                <button class='btn btn-danger btn-sm add-to-favorites' data-fdcid="${item.fdcId}">
                  ${favoritesIconHTML} Add to Favorites
                </button>
              </div>`
            : `<button class='btn btn-secondary btn-sm d-flex align-items-center justify-content-center align-middle lock-login' 
                style="width: 150px; height: 36px; font-size: 14px;">
                <span class="d-flex align-items-center">${lockIconHTML} <span class="ml-12 px-2">Log in to Add</span></span>
              </button>`;
        

            let learnMoreButton = item.fdcId 
            ? `<button class='btn btn-link p-0 learn-more text-muted' data-fdcid="${item.fdcId}" style="text-decoration: underline !important; font-style: italic; background: none; border: none; font-size: 0.70em;">Learn More</button>` 
            : "";

            resultsHTML += `
              <li class='list-group-item d-flex justify-content-between align-items-center'>
                <div>
                  <span style="font-family: 'Libre Franklin', sans-serif; font-size: 16px;">${item.name}</span><br>
                  <small style="font-family: 'Sofia Sans', sans-serif; font-size: 14px;">
                    Calories: <span style="color: #e67e22;">${item.calories}</span> kcal | 
                    Serving Size: <span style="color: #2ecc71;">${item.serving_size}</span>
                  </small><br>
                  ${brandText}<br>
                  ${learnMoreButton}
                </div>
                <div class="d-flex flex-column align-items-center justify-content-center gap-2">
                  <div>${addButtons}</div>
                </div>
              </li>
            `;
          });
          resultsHTML += "</ul>";
        } else {
          resultsHTML = "<p>No results found</p>";
        }
        $('#results').html(resultsHTML);
      },
      error: function(xhr, status, error) {
        if (status !== "abort") { 
          console.log("Error:", error);
          $('#results').html("<p>Failed to retrieve data</p>");
        }
      }
    });
  });

  // Redirect to login when lock icon button is clicked
  $(document).on('click', '.lock-login', function() {
    window.location.href = '/sign-in/';
  });

  // Add to Favorites
  $(document).on('click', '.add-to-favorites', function() {
    let fdcId = $(this).data('fdcid');
    let button = $(this);

    $.ajax({
      url: '/api/add-favorite',
      type: 'POST',
      data: { fdcId: fdcId },
      success: function(response) {
        button.text('✔ Added to Favorites').prop('disabled', true);
      },
      error: function() {
        alert("Failed to add to favorites. Try again.");
      }
    });
  });

  // Add to Daily Intake
  $(document).on('click', '.add-to-daily-intake', function() {
    let fdcId = $(this).data('fdcid');
    let name = $(this).data('name');
    let calories = $(this).data('calories');
    let button = $(this);

    $.ajax({
      url: '/api/add-daily-intake',
      type: 'POST',
      data: { fdcId: fdcId, name: name, calories: calories },
      success: function(response) {
        button.text('✔ Added to Intake').prop('disabled', true);
      },
      error: function() {
        alert("Failed to add to daily intake. Try again.");
      }
    });
  });


  $(document).on('click', '.learn-more', function() {
    let fdcId = $(this).data('fdcid');
    $('#foodModalBody').html("<p>Loading details...</p>");

    $.ajax({
      url: `/api/food-details/${fdcId}`,
      type: 'GET',
      success: function(response) {
        $('#foodModalBody').html(`
          <h5>${response.name}</h5>
          <p><strong>Calories:</strong> ${response.calories} kcal</p>
          <p><strong>Serving Size:</strong> ${response.serving_size}</p>
          <p><strong>Macronutrients:</strong></p>
          <ul>
            <li>Protein: ${response.protein}g</li>
            <li>Carbs: ${response.carbs}g</li>
            <li>Fats: ${response.fats}g</li>
          </ul>
        `);
      },
      error: function() {
        $('#foodModalBody').html("<p>Failed to load food details.</p>");
      }
    });

    $('#foodModal').modal('show');
  });
});
