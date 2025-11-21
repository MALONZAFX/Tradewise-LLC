// TradeWise Admin Custom JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add custom behavior to admin
    
    // Enhance action buttons
    const actionButtons = document.querySelectorAll('.action-buttons .button');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Auto-refresh dashboard data every 30 seconds
    if (window.location.pathname === '/admin/') {
        setInterval(() => {
            fetch('/admin/api/stats/')
                .then(response => response.json())
                .then(data => {
                    // Update stats on dashboard
                    console.log('Refreshed admin stats:', data);
                });
        }, 30000);
    }
    
    // Add confirmation for critical actions
    const deleteButtons = document.querySelectorAll('a[class*="deletelink"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});