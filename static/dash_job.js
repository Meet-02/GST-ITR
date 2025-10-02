// This script handles the single-page navigation logic
document.addEventListener("DOMContentLoaded", function() {
    const navLinks = document.querySelectorAll('.nav-link[data-page]');
    const pageContents = document.querySelectorAll('.page-content');

    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the link from navigating away

            const pageId = this.getAttribute('data-page');

            // Remove 'active' class from all links
            navLinks.forEach(navLink => {
                navLink.classList.remove('active');
            });

            // Add 'active' class to the clicked link
            this.classList.add('active');

            // Hide all page content sections
            pageContents.forEach(content => {
                content.style.display = 'none';
            });

            // Show the content section that matches the clicked link
            const activeContent = document.getElementById(pageId + '-content');
            if (activeContent) {
                activeContent.style.display = 'block';
            }
        });
    });
});