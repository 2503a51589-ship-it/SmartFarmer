/**
 * SIH26032: Chart.js Analytics for Admin Dashboard & Reports
 */

function initAdminCharts(analyticsData) {
    if (!window.Chart || !analyticsData) return;

    // 1. Daily Bookings Chart
    const dailyCtx = document.getElementById('dailyBookingsChart');
    if (dailyCtx) {
        new Chart(dailyCtx, {
            type: 'bar',
            data: {
                labels: analyticsData.daily_labels || ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Today'],
                datasets: [{
                    label: 'Farmers Booked',
                    data: analyticsData.daily_counts || [12, 19, 15, 25, 22, 30, 28],
                    backgroundColor: 'rgba(46, 125, 50, 0.8)',
                    borderColor: '#1b5e20',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } } }
            }
        });
    }

    // 2. Crop-wise Procurement Distribution (Doughnut)
    const cropCtx = document.getElementById('cropProcurementChart');
    if (cropCtx) {
        new Chart(cropCtx, {
            type: 'doughnut',
            data: {
                labels: analyticsData.crop_labels || ['Wheat', 'Paddy', 'Groundnut', 'Gram', 'Mustard'],
                datasets: [{
                    data: analyticsData.crop_quantities || [450, 320, 210, 180, 95],
                    backgroundColor: ['#2e7d32', '#f59e0b', '#0284c7', '#8b5cf6', '#ec4899']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // 3. Center Queue Congestion Chart (Horizontal Bar)
    const centerCtx = document.getElementById('centerQueueChart');
    if (centerCtx) {
        new Chart(centerCtx, {
            type: 'bar',
            indexAxis: 'y',
            data: {
                labels: analyticsData.center_names || ['Anand Mandi', 'Navsari Samiti', 'Patan Mandi', 'Vadodara PACS', 'Rajkot Mandi'],
                datasets: [{
                    label: 'Active Waiting Queue',
                    data: analyticsData.center_queues || [4, 2, 7, 3, 6],
                    backgroundColor: ['#10b981', '#10b981', '#f59e0b', '#10b981', '#ef4444'],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });
    }

    // 4. Payment DBT Status Chart (Pie)
    const paymentCtx = document.getElementById('paymentStatusChart');
    if (paymentCtx) {
        new Chart(paymentCtx, {
            type: 'pie',
            data: {
                labels: ['Credited', 'Processing', 'Pending'],
                datasets: [{
                    data: analyticsData.payment_stats || [75, 18, 7],
                    backgroundColor: ['#10b981', '#f59e0b', '#64748b']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}
