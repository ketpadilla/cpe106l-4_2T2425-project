document.addEventListener('DOMContentLoaded', function() {
    const dobElem = document.getElementById('dobText');
    let age = 30; 
    if (dobElem) {
        const dobStr = dobElem.innerText;
        const dobDate = new Date(dobStr);
        if (!isNaN(dobDate)) {
            const diffMs = Date.now() - dobDate.getTime();
            const diffDate = new Date(diffMs); 
            age = Math.abs(diffDate.getUTCFullYear() - 1970);
        }
    }

    // Display the age
    document.getElementById('ageDisplay').innerHTML = `<strong>Age: </strong> ${age}`;
});