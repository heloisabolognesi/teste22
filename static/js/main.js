/**
 * L.A.A.R.I - Main JavaScript File
 * Archaeological Management System
 */

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the main application
 */
function initializeApp() {
    initializeTooltips();
    initializeModals();
    initializeFormValidation();
    initializeFileUpload();
    initializeSearch();
    initializeAnimations();
    initializeThemeControls();
    
    console.log('L.A.A.R.I System Initialized');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap modals
 */
function initializeModals() {
    // Auto-focus on modal inputs when opened
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Custom form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
                
                showNotification('Por favor, corrija os erros no formulário.', 'warning');
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation for required fields
    document.querySelectorAll('input[required], select[required], textarea[required]').forEach(function(field) {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const isValid = field.checkValidity();
    field.classList.toggle('is-valid', isValid);
    field.classList.toggle('is-invalid', !isValid);
    
    return isValid;
}

/**
 * Initialize file upload enhancements
 */
function initializeFileUpload() {
    // File upload preview and validation
    document.querySelectorAll('input[type="file"]').forEach(function(input) {
        input.addEventListener('change', function(e) {
            handleFileUpload(e.target);
        });
    });
}

/**
 * Handle file upload with preview and validation
 */
function handleFileUpload(input) {
    const files = input.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    // Validate file size
    if (file.size > maxSize) {
        showNotification('Arquivo muito grande. Limite máximo: 16MB', 'error');
        input.value = '';
        return;
    }
    
    // Create or update file info display
    let fileInfo = input.parentNode.querySelector('.file-info');
    if (!fileInfo) {
        fileInfo = document.createElement('div');
        fileInfo.className = 'file-info mt-2';
        input.parentNode.appendChild(fileInfo);
    }
    
    const fileSize = formatFileSize(file.size);
    fileInfo.innerHTML = `
        <div class="d-flex align-items-center text-success">
            <i class="fas fa-file-alt me-2"></i>
            <span class="me-2">${file.name}</span>
            <small class="text-muted">(${fileSize})</small>
        </div>
    `;
    
    // Show image preview for image files
    if (file.type.startsWith('image/')) {
        showImagePreview(file, fileInfo);
    }
}

/**
 * Show image preview
 */
function showImagePreview(file, container) {
    const reader = new FileReader();
    reader.onload = function(e) {
        let preview = container.querySelector('.image-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            container.appendChild(preview);
        }
        
        preview.innerHTML = `
            <img src="${e.target.result}" alt="Preview" 
                 style="max-width: 200px; max-height: 200px; object-fit: cover;" 
                 class="img-thumbnail">
        `;
    };
    reader.readAsDataURL(file);
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Generic table search
    const searchInputs = document.querySelectorAll('[data-search-table]');
    searchInputs.forEach(function(input) {
        const tableSelector = input.dataset.searchTable;
        const table = document.querySelector(tableSelector);
        
        if (table) {
            input.addEventListener('input', function() {
                filterTable(table, this.value);
            });
        }
    });
    
    // Live search for cards
    const cardSearchInputs = document.querySelectorAll('[data-search-cards]');
    cardSearchInputs.forEach(function(input) {
        const cardsSelector = input.dataset.searchCards;
        
        input.addEventListener('input', function() {
            filterCards(cardsSelector, this.value);
        });
    });
}

/**
 * Filter table rows based on search term
 */
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        const shouldShow = text.includes(term);
        row.style.display = shouldShow ? '' : 'none';
    });
}

/**
 * Filter cards based on search term
 */
function filterCards(cardsSelector, searchTerm) {
    const cards = document.querySelectorAll(cardsSelector);
    const term = searchTerm.toLowerCase();
    
    cards.forEach(function(card) {
        const text = card.textContent.toLowerCase();
        const shouldShow = text.includes(term);
        card.style.display = shouldShow ? '' : 'none';
    });
}

/**
 * Initialize animations and transitions
 */
function initializeAnimations() {
    // Animate cards on scroll
    if (window.IntersectionObserver) {
        const cardObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, { threshold: 0.1 });
        
        document.querySelectorAll('.card').forEach(function(card) {
            cardObserver.observe(card);
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize theme controls
 */
function initializeThemeControls() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    if (!themeToggle) return;
    
    const savedTheme = Storage.get('theme', 'light');
    applyTheme(savedTheme);
    
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
        Storage.set('theme', newTheme);
    });
    
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    prefersDark.addEventListener('change', function(e) {
        if (!Storage.get('theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
}

/**
 * Apply theme to the page
 */
function applyTheme(theme) {
    const themeIcon = document.getElementById('themeIcon');
    
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeIcon) themeIcon.textContent = '☀️';
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeIcon) themeIcon.textContent = '🌙';
    }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info', duration = 5000) {
    const container = getNotificationContainer();
    
    const alertClass = type === 'error' ? 'danger' : type;
    const iconClass = getNotificationIcon(type);
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        <i class="fas ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(function() {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, duration);
    
    return notification;
}

/**
 * Get or create notification container
 */
function getNotificationContainer() {
    let container = document.getElementById('notification-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
    }
    
    return container;
}

/**
 * Get appropriate icon for notification type
 */
function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    return icons[type] || icons.info;
}

/**
 * Confirm dialog wrapper
 */
function confirmDialog(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

/**
 * Format date for display
 */
function formatDate(date, format = 'dd/MM/yyyy') {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return format
        .replace('dd', day)
        .replace('MM', month)
        .replace('yyyy', year)
        .replace('HH', hours)
        .replace('mm', minutes);
}

/**
 * Debounce function for performance optimization
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('Texto copiado para a área de transferência!', 'success');
        }).catch(function() {
            fallbackCopyText(text);
        });
    } else {
        fallbackCopyText(text);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopyText(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Texto copiado para a área de transferência!', 'success');
    } catch (err) {
        showNotification('Não foi possível copiar o texto.', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Generate QR Code (placeholder for future implementation)
 */
function generateQRCode(text, element) {
    // This would integrate with a QR code library like qrcode.js
    console.log('Generate QR Code for:', text);
    showNotification('Funcionalidade de QR Code será implementada em breve.', 'info');
}

/**
 * Export table data to CSV
 */
function exportTableToCSV(table, filename = 'export.csv') {
    const csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let text = cols[j].textContent.replace(/"/g, '""');
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * Download CSV file
 */
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/**
 * Utility functions for localStorage
 */
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Could not save to localStorage', e);
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Could not read from localStorage', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Could not remove from localStorage', e);
        }
    }
};

/**
 * Global error handler
 */
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // Could send error reports to a logging service
});

/**
 * Handle unhandled promise rejections
 */
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// Export functions for use in other scripts
window.LAARI = {
    showNotification,
    confirmDialog,
    formatDate,
    debounce,
    copyToClipboard,
    generateQRCode,
    exportTableToCSV,
    Storage
};

console.log('L.A.A.R.I JavaScript utilities loaded');
