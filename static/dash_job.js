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

document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("jobChart").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Gross Income", "Deductions", "Net Income", "Tax"],
            datasets: [{
                label: "Income Overview",
                data: [gross_income, deductions, net_income, tax],
                backgroundColor: ["#36A2EB", "#FF6384", "#4BC0C0", "#FFCE56"],
            }]
        }
    });
});
