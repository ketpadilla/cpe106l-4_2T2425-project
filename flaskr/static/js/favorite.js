// for implementation of saving of favorite foods

$(document).ready(function() {
    // Load user favorites when the page loads
    loadFavorites();
    
    // Function to load favorites from the server
    function loadFavorites() {
      $.ajax({
        url: '/api/get-favorites',
        type: 'GET',
        success: function(response) {
          displayFavorites(response.favorites);
        },
        error: function(xhr, status, error) {
          console.error('Error loading favorites:', error);
          $('.card-body:contains("Favorites")').append('<p class="text-danger">Failed to load favorites</p>');
        }
      });
    }
    
    // Function to display favorites in the user profile
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
    
    // Event handler for removing favorites
    $(document).on('click', '.remove-favorite', function() {
      const fdcId = $(this).data('fdcid');
      const listItem = $(this).closest('li');
      
      $.ajax({
        url: '/api/remove-favorite',
        type: 'POST',
        contentType: "application/json",
        data: JSON.stringify({ fdcId: fdcId }),
        success: function(response) {
          listItem.fadeOut(300, function() { $(this).remove(); });
          
          // If this was the last favorite, show the empty message
          if ($('.remove-favorite').length === 1) {
            setTimeout(() => {
              $('.card-body:contains("Favorites")').append('<p class="text-muted mt-3">You have no favorite foods yet.</p>');
            }, 300);
          }
        },
        error: function(xhr, status, error) {
          alert('Failed to remove favorite. Please try again.');
        }
      });
    });

    // Event handler for adding to daily intake
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
});


