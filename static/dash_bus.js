document.addEventListener("DOMContentLoaded", function() {
    
    // --- NAVIGATION LOGIC ---
    const navLinks = document.querySelectorAll('.nav-link[data-page]');
    const pageContents = document.querySelectorAll('.page-content');

    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const pageId = this.getAttribute('data-page');
            
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            this.classList.add('active');

            pageContents.forEach(content => content.style.display = 'none');
            const activeContent = document.getElementById(pageId + '-content');
            
            if (activeContent) {
                activeContent.style.display = 'block';
            }
        });
    });

    // --- CHART CREATION LOGIC ---
    // The variables chartLabels, revenueData, etc., are defined in the HTML script tag

    // 1. Revenue Trend Chart (Bar)
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx && typeof chartLabels !== 'undefined' && chartLabels.length > 0) {
        new Chart(revenueCtx, {
            type: 'bar',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Gross Revenue (₹)',
                    data: revenueData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });
    }

    // 2. Tax Comparison Chart (Line)
    const taxCtx = document.getElementById('taxComparisonChart');
    if (taxCtx && typeof chartLabels !== 'undefined' && chartLabels.length > 0) {
        new Chart(taxCtx, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'GST Payable (₹)',
                    data: gstData,
                    borderColor: 'rgba(255, 193, 7, 1)',
                    backgroundColor: 'rgba(255, 193, 7, 0.2)',
                    fill: true,
                    tension: 0.1
                }, {
                    label: 'Income Tax Payable (₹)',
                    data: taxData,
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.2)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });
    }
});

