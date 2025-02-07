// Open the side menu
function openMenu() {
    document.getElementById("side-menu").style.width = "250px";
  }
  
  // Close the side menu
  function closeMenu() {
    document.getElementById("side-menu").style.width = "0";
  }
  
  
  // Function to display current date and time
  function updateDateTime() {
      const dateTimeElement = document.getElementById("datetime");
      const now = new Date();
  
      const options = {
          weekday: 'short',
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
      };
  
      dateTimeElement.textContent = now.toLocaleString('en-US', options);
  }
  
  // Update datetime every second
  setInterval(updateDateTime, 1000);
  window.onload = updateDateTime; // Run immediately on load