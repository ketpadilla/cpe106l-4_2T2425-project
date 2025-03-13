/**
 * Handles the implementation of saving and managing favorite foods.
 * This script loads the user's favorite foods, displays them in the user profile,
 * and allows users to remove favorites or add them to their daily intake.
 */
$(document).ready(function() {
    // Load user favorites when the page loads
    loadFavorites();
    
    /**
     * Loads the user's favorite foods from the server.
     * On success, it calls the displayFavorites function to update the UI.
     */
    function loadFavorites() {
      $.ajax({
        url: '/api/get-favorites', // The API endpoint to fetch favorite foods
        type: 'GET', // HTTP method
        success: function(response) {
          displayFavorites(response.favorites); // Display favorites in the UI
        },
        error: function(xhr, status, error) {
          console.error('Error loading favorites:', error);
          $('.card-body:contains("Favorites")')
            .append('<p class="text-danger">Failed to load favorites</p>');
        }
      });
    }
    
    /**
     * Displays the user's favorite foods in the user profile.
     * If the user has no favorites, it shows a placeholder message.
     * 
     * @param {Array} favorites - The list of favorite food items.
     */
    function displayFavorites(favorites) {
        const favoritesContainer = $('.card-body:contains("Favorites")');
        favoritesContainer.find('p.text-muted').remove(); // Prevent duplication
        favoritesContainer.find('ul').remove(); // Remove existing list if reloading
    
        if (favorites.length > 0) {
            let html = '<ul class="list-group mt-3">';
            favorites.forEach(item => {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <span class="fw-bold">${item.name}</span><br>
                        <small class="text-muted">Calories: ${item.calories} kcal</small>
                        <small class="text-muted ms-2">Serving Size: ${item.serving_size}</small>
                        ${item.brand ? `<br><small class="text-muted">Brand: ${item.brand}</small>` : ''}
                    </div>
                    <div class="d-flex flex-column">
                        <button class="btn btn-sm btn-success add-to-daily-intake mb-2" data-fdcid="${item.fdcId}" data-name="${item.name}" data-calories="${item.calories}">
                            <i class="fas fa-plus-circle"></i> Add to Daily Intake
                        </button>
                        <button class="btn btn-sm btn-danger remove-favorite" data-fdcid="${item.fdcId}">
                            <i class="fas fa-trash-alt"></i> Remove
                        </button>
                    </div>
                </li>`;
            });
            html += '</ul>';
            favoritesContainer.append(html);
        } else {
            favoritesContainer.append('<p class="text-muted mt-3">You have no favorite foods yet.</p>');
        }
    }
    
    /**
     * Handles the removal of a favorite food item.
     * Sends an AJAX request to the server and updates the UI accordingly.
     */
    $(document).on('click', '.remove-favorite', function() {
      const fdcId = $(this).data('fdcid'); // Get the food item ID
      const listItem = $(this).closest('li'); // Select the corresponding list item
      
      $.ajax({
        url: '/api/remove-favorite', // The API endpoint for removing favorites
        type: 'POST', // HTTP method
        contentType: "application/json", // Data type
        data: JSON.stringify({ fdcId: fdcId }), // Send the food item ID
        success: function(response) {
          // Remove the item from the list with a fade-out effect
          listItem.fadeOut(300, function() { $(this).remove(); });

          // If this was the last favorite, show the empty message
          if ($('.remove-favorite').length === 1) {
            setTimeout(() => {
              $('.card-body:contains("Favorites")')
                .append('<p class="text-muted mt-3">You have no favorite foods yet.</p>');
            }, 300);
          }
        },
        error: function(xhr, status, error) {
          alert('Failed to remove favorite. Please try again.');
        }
      });
    });

    /**
     * Handles adding a favorite food item to the daily intake.
     * Sends an AJAX request to the server and updates the button text.
     */
    $(document).on('click', '.add-to-daily-intake', function() {
      let fdcId = $(this).data('fdcid'); // Get the food item ID
      let button = $(this); // Store the button element
      
      $.ajax({
        url: '/api/add-daily-intake', // The API endpoint for adding to daily intake
        type: 'POST', // HTTP method
        contentType: "application/json", // Data type
        data: JSON.stringify({ fdcId: fdcId }), // Send the food item ID
        success: function() {
          // Update the button text and disable it after successful addition
          button.text('✔ Added to Intake').prop('disabled', true);
        },
        error: function() {
          alert("Failed to add to daily intake. Try again.");
        }
      });
    });
});
