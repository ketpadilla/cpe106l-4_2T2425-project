$(document).ready(function() {
  let currentRequest = null; // Stores the current AJAX request to prevent duplicate calls
  let currentPage = 1; // Tracks the current page number for pagination
  const limit = 10; // Number of results per page

  /**
   * Performs a food search based on the user's input.
   * Handles pagination and dynamically updates the search results.
   * @param {boolean} reset - Determines whether to reset the results or load more items.
   */
  function performSearch(reset = true) {
    let query = $('#searchQuery').val().trim();

    // If the query is empty, abort any existing request and clear results
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

    // Abort any ongoing request before making a new one
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

        // Handle "View More" button for pagination
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
      error: function(xhr, status) {
        if (status !== "abort") $('#results').html("<p>Failed to retrieve data</p>");
      }
    });
  }

  // Trigger search when the user types in the search field
  $('#searchQuery').on('input', function() {
    performSearch(true);
  });

  // Handle "View More" button click for pagination
  $(document).on('click', '#viewMoreBtn', function() {
    if (currentRequest) currentRequest.abort();
  
    let query = $('#searchQuery').val().trim();
    currentPage++;
  
    currentRequest = $.ajax({
      url: '/api/search-food/',
      type: 'GET',
      data: { query: query, page: currentPage, limit: limit },
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

  // Redirect users to the login page when they attempt to add items without being logged in
  $(document).on('click', '.lock-login', function() {
    window.location.href = '/sign-in/';
  });

  // Handles adding a food item to the user's favorites
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

  // Handles adding a food item to the user's daily intake
  $(document).on("click", ".add-to-daily-intake", function () {
    let fdcId = $(this).data("fdcid");
    let button = $(this);

    $.ajax({
      url: "/api/add-daily-intake",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ fdcId: fdcId }),
      success: function (response) {
        if (response.error) {
          alert("Error: " + response.error);
          return;
        }
        
        button.text("✔ Added to Intake").prop("disabled", true);
        alert("Food added! Calories: "
