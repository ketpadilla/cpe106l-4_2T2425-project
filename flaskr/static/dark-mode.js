document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.querySelector(".dark-mode-toggle");
  const icon = toggleButton.querySelector(".dark-mode-icon");
  const body = document.body;

  // Function to update the icon based on mode
  function updateIcon(isDark) {
      if (isDark) {
        icon.innerHTML = `<path d="M6 .278a.77.77 0 0 1 .08.858 7.2 7.2 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277q.792-.001 1.533-.16a.79.79 0 0 1 .81.316.73.73 0 0 1-.031.893A8.35 8.35 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.75.75 0 0 1 6 .278"/>`; // Moon icon
      } else {
        icon.innerHTML = `<path d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0m0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13m8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5M3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8m10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0m-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0m9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707M4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708"/>`; // Sun icon
      }
  }

  // Function to determine if dark mode should be applied
  function getPreferredMode() {
      const storedMode = localStorage.getItem("darkMode");
      if (storedMode) {
          return storedMode === "enabled"; // User preference
      }
      return window.matchMedia("(prefers-color-scheme: dark)").matches; // System preference
  }

  // Apply the initial mode
  if (getPreferredMode()) {
      body.classList.add("dark-mode");
  } else {
      body.classList.remove("dark-mode");
  }
  updateIcon(body.classList.contains("dark-mode"));

  // Listen for system preference changes
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
      if (!localStorage.getItem("darkMode")) {
          body.classList.toggle("dark-mode", event.matches);
          updateIcon(event.matches);
      }
  });

  // Toggle dark mode on button click
  toggleButton.addEventListener("click", function () {
      const isDark = body.classList.toggle("dark-mode");

      // Save preference in localStorage
      if (isDark) {
          localStorage.setItem("darkMode", "enabled");
      } else {
          localStorage.setItem("darkMode", "disabled");
      }

      updateIcon(isDark);
  });
});
