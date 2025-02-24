$(document).ready(function() {
  let currentRequest = null; // Store the current AJAX request

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
            resultsHTML += `<li class='list-group-item'>${item.name}</li>`;
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
});