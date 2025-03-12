/**
 * Event listener for when the DOM content is fully loaded.
 * This script calculates the user's age based on their date of birth (DOB)
 * and displays it on the page.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the element containing the date of birth (DOB)
    const dobElem = document.getElementById('dobText');
    let age = 30; // Default age if DOB is not found or invalid

    // Check if the DOB element exists
    if (dobElem) {
        // Extract the DOB string from the element
        const dobStr = dobElem.innerText;
        // Convert the DOB string to a Date object
        const dobDate = new Date(dobStr);

        // Check if the DOB is a valid date
        if (!isNaN(dobDate)) {
            // Calculate the difference between the current date and the DOB
            const diffMs = Date.now() - dobDate.getTime();
            // Convert the difference to a Date object
            const diffDate = new Date(diffMs);
            // Calculate the age in years
            age = Math.abs(diffDate.getUTCFullYear() - 1970);
        }
    }

    // Display the calculated age in the designated element
    document.getElementById('ageDisplay').innerHTML = `<strong>Age: </strong> ${age}`;
});
