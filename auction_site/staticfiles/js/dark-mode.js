document.addEventListener('DOMContentLoaded', function() {
    // Get the theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    
    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('theme') || 
                      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    // Apply the saved theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update toggle button icon
    updateToggleIcon(savedTheme);
    
    // Add event listener to toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // Get the current theme
            const currentTheme = document.documentElement.getAttribute('data-theme');
            
            // Toggle the theme
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Save the new theme preference
            localStorage.setItem('theme', newTheme);
            
            // Apply the new theme
            document.documentElement.setAttribute('data-theme', newTheme);
            
            // Update toggle button icon
            updateToggleIcon(newTheme);
        });
    }
    
    // Function to update toggle button icon
    function updateToggleIcon(theme) {
        if (!themeToggle) return;
        
        if (theme === 'dark') {
            themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
            themeToggle.title = 'Switch to light mode';
        } else {
            themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
            themeToggle.title = 'Switch to dark mode';
        }
    }
});

// Countdown timer for auctions
document.addEventListener('DOMContentLoaded', function() {
    const timerElements = document.querySelectorAll('.timer');
    
    timerElements.forEach(function(element) {
        const endDate = new Date(element.dataset.endDate);
        
        // Update the timer every second
        const timerId = setInterval(function() {
            const now = new Date();
            const distance = endDate - now;
            
            // If the auction has ended
            if (distance < 0) {
                clearInterval(timerId);
                element.innerHTML = 'Ended';
                element.classList.add('text-danger');
                return;
            }
            
            // Calculate time units
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            // Display the timer
            if (days > 0) {
                element.innerHTML = `${days}d ${hours}h ${minutes}m`;
            } else if (hours > 0) {
                element.innerHTML = `${hours}h ${minutes}m ${seconds}s`;
            } else {
                element.innerHTML = `${minutes}m ${seconds}s`;
                element.classList.add('text-danger');
            }
        }, 1000);
    });
});
