// Main JavaScript for FinSight

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.classList.contains('fade')) {
                alert.classList.remove('show');
            }
        }, 5000);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            } else {
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                    submitBtn.disabled = true;
                }
            }
            form.classList.add('was-validated');
        });
    });

    // Currency formatting
    const currencyInputs = document.querySelectorAll('input[name="amount"]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview if it's an image
                    if (file.type.startsWith('image/')) {
                        let preview = input.parentNode.querySelector('.file-preview');
                        if (!preview) {
                            preview = document.createElement('div');
                            preview.className = 'file-preview mt-2';
                            input.parentNode.appendChild(preview);
                        }
                        preview.innerHTML = `
                            <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 150px;">
                            <p class="small text-muted mt-1">${file.name}</p>
                        `;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Auto-refresh for dashboard (every 5 minutes)
    if (window.location.pathname.includes('/dashboard') || 
        window.location.pathname.includes('/approvals')) {
        setInterval(function() {
            // Check for new notifications or updates
            checkForUpdates();
        }, 300000); // 5 minutes
    }

    // Search functionality for tables
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(function(searchInput) {
        const targetTable = document.querySelector(searchInput.dataset.search);
        if (targetTable) {
            searchInput.addEventListener('keyup', function() {
                filterTable(targetTable, this.value);
            });
        }
    });

    // Confirmation dialogs for important actions
    const dangerButtons = document.querySelectorAll('.btn-danger, .btn-outline-danger');
    dangerButtons.forEach(function(btn) {
        if (!btn.hasAttribute('onclick')) {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to proceed with this action?')) {
                    e.preventDefault();
                }
            });
        }
    });
});

// Utility Functions
function checkForUpdates() {
    // This would make an AJAX call to check for new notifications
    // For now, just a placeholder
    console.log('Checking for updates...');
}

function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();

    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(function() {
        notification.remove();
    }, 5000);
}

// OCR Processing Functions
function processReceipt(file, callback) {
    const formData = new FormData();
    formData.append('receipt', file);

    fetch('/upload_receipt', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            callback(null, data.data);
        } else {
            callback(data.error || 'OCR processing failed');
        }
    })
    .catch(error => {
        callback('Network error occurred');
    });
}

// Export Functions
function exportToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push(col.textContent.trim());
        });
        csv.push(rowData.join(','));
    });

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Theme Toggle (Future Enhancement)
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.toggle('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Load saved theme
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
});

// PWA Service Worker Registration (Future Enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed');
            });
    });
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S to submit forms
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            form.submit();
        }
    }

    // Ctrl+N for new expense
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/submit_expense';
    }

    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});
