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

    // 1. Data for Monthly GST Payable (Line Graph)
    const monthlyGstLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthlyGstData = [12000, 15000, 11000, 18000, 16000, 21000, 19000, 22000, 25000, 23000, 28000, 31000];

    // 2. Data for Annual Revenue (Bar Graph)
    const annualRevenueLabels = ['2022', '2023', '2024', '2025'];
    const annualRevenueData = [950000, 1100000, 1050000, 1250000];

    // 3. Data for Tax Payable
    const taxPayableYears = ['2022', '2023', '2024', '2025'];
    const taxPayableData = [105000, 120000, 115000, 140000];


    // --- CHART INITIALIZATION ---

    // 1. Monthly GST Payable (Line Chart)
    const gstCtx = document.getElementById('monthlyGstChart').getContext('2d');
    new Chart(gstCtx, {
        type: 'line',
        data: {
            labels: monthlyGstLabels,
            datasets: [{
                label: 'GST Payable (₹)',
                data: monthlyGstData,
                fill: true,
                backgroundColor: 'rgba(0, 123, 255, 0.2)',
                borderColor: 'rgba(0, 123, 255, 1)',
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // 2. Annual Revenue (Bar Chart)
    const revenueCtx = document.getElementById('annualRevenueChart').getContext('2d');
    new Chart(revenueCtx, {
        type: 'bar',
        data: {
            labels: annualRevenueLabels,
            datasets: [{
                label: 'Revenue (₹)',
                data: annualRevenueData,
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: 'rgba(40, 167, 69, 1)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // 3. Tax Payable (Dotted Line Graph) - AXES SWAPPED
    const taxCtx = document.getElementById('taxPayableChart').getContext('2d');
    new Chart(taxCtx, {
        type: 'line',
        data: {
            labels: taxPayableYears, // Labels for the x-axis
            datasets: [{
                label: 'Tax Payable (₹)',
                data: taxPayableData, // Data for the y-axis
                borderColor: 'rgba(220, 53, 69, 1)',
                pointBackgroundColor: 'rgba(220, 53, 69, 1)',
                pointRadius: 6,
                pointHoverRadius: 8,
                borderDash: [5, 5],
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: { // X-axis is now the Year
                    type: 'category',
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: { // Y-axis is now the Amount
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Amount Payable (₹)'
                    }
                }
            }
        }
    });
});