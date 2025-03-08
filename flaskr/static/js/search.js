$(document).ready(function() {
  let currentRequest = null;
  let currentPage = 1;
  const limit = 10;

  function performSearch(reset = true) {
    let query = $('#searchQuery').val().trim();
    if (query === "") {
      if (currentRequest) currentRequest.abort();
      $('#results').empty();
      $('#viewMoreContainer').remove();
      return;
    }

    if (reset) {
      $('#results').html("<p>Loading...</p>");
      currentPage = 1;
    }

    if (currentRequest) currentRequest.abort();

    currentRequest = $.ajax({
      url: '/api/search-food/',
      type: 'GET',
      data: { query: query, page: currentPage, limit: limit },
      success: function(response) {
        let resultsHTML = reset ? "<ul class='list-group'>" : $('#results').html();
        
        if (response.results.length > 0) {
          response.results.forEach(item => {
            let brandText = item.brand ? `<small class="text-muted">Brand: ${item.brand}</small>` : "";
            let addButtons = userLoggedIn === "true"
              ? `<div class='d-flex flex-column'>
                  <button class='btn btn-success btn-sm add-to-daily-intake mb-2' data-fdcid="${item.fdcId}" data-name="${item.name}" data-calories="${item.calories}">${addIconHTML} Add to Daily Intake</button>
                  <button class='btn btn-danger btn-sm add-to-favorites' data-fdcid="${item.fdcId}">${favoritesIconHTML} Add to Favorites</button>
                </div>`
              : `<button class='btn btn-secondary btn-sm lock-login'>Log in to Add</button>`;
            let learnMoreButton = item.fdcId 
              ? `<button class='btn btn-link p-0 learn-more text-muted' data-fdcid="${item.fdcId}" style="text-decoration: underline !important; font-style: italic; background: none; border: none; font-size: 0.70em;">Learn More</button>` 
              : "";

            resultsHTML += `
              <li class='list-group-item d-flex justify-content-between align-items-center'>
                <div>
                  <span>${item.name}</span><br>
                  <small>Calories: ${item.calories} kcal | Serving Size: ${item.serving_size}</small><br>
                  ${brandText}<br>
                  ${learnMoreButton}
                </div>
                <div>${addButtons}</div>
              </li>
            `;
          });
          resultsHTML += "</ul>";
        } else {
          resultsHTML = "<p>No results found</p>";
        }
        $('#results').html(resultsHTML);

        if (response.has_more) {
          if (!$('#viewMoreContainer').length) {
            $('#results').after(`
              <div id="viewMoreContainer" class="d-flex justify-content-center mt-3">
                <button id="viewMoreBtn" class="btn btn-primary">View More</button>
              </div>
            `);
          }
        } else {
          $('#viewMoreContainer').remove();
        } 
      },
      error: function(xhr, status, error) {
        if (status !== "abort") $('#results').html("<p>Failed to retrieve data</p>");
      }
    });
  }

  $('#searchQuery').on('input', function() {
    performSearch(true);
  });

  $(document).on('click', '#viewMoreBtn', function() {
    if (currentRequest) currentRequest.abort();
  
    let query = $('#searchQuery').val().trim();
    currentPage++;
  
    currentRequest = $.ajax({
      url: '/api/search-food/',
      type: 'GET',
      data: { query: query, page: currentPage, limit: limit }, // Ensure limit is passed
      success: function(response) {
        if (response.results.length > 0) {
          let resultsHTML = response.results.map(item => {
            let brandText = item.brand ? `<small class="text-muted">Brand: ${item.brand}</small>` : "";
            let addButtons = userLoggedIn === "true"
              ? `<div class='d-flex flex-column'>
                  <button class='btn btn-success btn-sm add-to-daily-intake mb-2' data-fdcid="${item.fdcId}" data-name="${item.name}" data-calories="${item.calories}">${addIconHTML} Add to Daily Intake</button>
                  <button class='btn btn-danger btn-sm add-to-favorites' data-fdcid="${item.fdcId}">${favoritesIconHTML} Add to Favorites</button>
                </div>`
              : `<button class='btn btn-secondary btn-sm lock-login'>Log in to Add</button>`;
  
            return `
              <li class='list-group-item d-flex justify-content-between align-items-center'>
                <div>
                  <span>${item.name}</span><br>
                  <small>Calories: ${item.calories} kcal | Serving Size: ${item.serving_size}</small><br>
                  ${brandText}
                </div>
                <div>${addButtons}</div>
              </li>
            `;
          }).join('');
  
          $('.list-group').append(resultsHTML);
        }
  
        if (!response.has_more) {
          $('#viewMoreContainer').remove();
        }
      },
      error: function(xhr, status) {
        if (status !== "abort") {
          $('#viewMoreBtn').text("Failed to load more").prop("disabled", true);
        }
      }
    });
  });
  
  $(document).on('click', '.lock-login', function() {
    window.location.href = '/sign-in/';
  });

  $(document).on('click', '.add-to-favorites', function() {
    let fdcId = $(this).data('fdcid');
    let button = $(this);
    
    $.ajax({
      url: '/api/add-favorite',
      type: 'POST',
      contentType: "application/json",
      data: JSON.stringify({ fdcId: fdcId }),
      success: function() {
        button.text('✔ Added to Favorites').prop('disabled', true);
      },
      error: function() {
        alert("Failed to add to favorites. Try again.");
      }
    });
  });

  $(document).on('click', '.add-to-daily-intake', function() {
    let fdcId = $(this).data('fdcid');
    let button = $(this);
    
    $.ajax({
      url: '/api/add-daily-intake',
      type: 'POST',
      contentType: "application/json",
      data: JSON.stringify({ fdcId: fdcId }),
      success: function() {
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