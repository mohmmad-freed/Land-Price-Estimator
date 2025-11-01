// Dropdown Menu Handler
document.addEventListener('DOMContentLoaded', function() {
  const dropdowns = document.querySelectorAll('.group');
  
  // Handle dropdown open/close
  dropdowns.forEach(dropdown => {
    const trigger = dropdown.querySelector('button');
    const menu = dropdown.querySelector('[class*="bg-card"][class*="shadow-lg"]');
    
    if (trigger && menu) {
      trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // Close all other dropdowns
        dropdowns.forEach(otherDropdown => {
          const otherMenu = otherDropdown.querySelector('[class*="bg-card"][class*="shadow-lg"]');
          if (otherMenu && otherDropdown !== dropdown) {
            otherMenu.classList.add('opacity-0', 'invisible');
            otherMenu.classList.remove('opacity-100', 'visible');
          }
        });
        
        // Toggle current dropdown
        menu.classList.toggle('opacity-0');
        menu.classList.toggle('opacity-100');
        menu.classList.toggle('invisible');
        menu.classList.toggle('visible');
      });
    }
  });
  
  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    dropdowns.forEach(dropdown => {
      const menu = dropdown.querySelector('[class*="bg-card"][class*="shadow-lg"]');
      const trigger = dropdown.querySelector('button');
      
      if (menu && trigger && !dropdown.contains(e.target)) {
        menu.classList.add('opacity-0', 'invisible');
        menu.classList.remove('opacity-100', 'visible');
      }
    });
  });
});

// Form Validation Helper
function validateForm(formSelector) {
  const form = document.querySelector(formSelector);
  if (!form) return false;
  
  const requiredFields = form.querySelectorAll('[required]');
  let isValid = true;
  
  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      showFieldError(field, 'This field is required');
    } else {
      clearFieldError(field);
    }
  });
  
  return isValid;
}

// Show field error
function showFieldError(field, message) {
  field.classList.add('border-destructive');
  
  let errorElement = field.parentElement.querySelector('.error-message');
  if (!errorElement) {
    errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    field.parentElement.appendChild(errorElement);
  }
  errorElement.textContent = message;
}

// Clear field error
function clearFieldError(field) {
  field.classList.remove('border-destructive');
  const errorElement = field.parentElement.querySelector('.error-message');
  if (errorElement) {
    errorElement.remove();
  }
}

// Show notification
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `p-4 rounded-lg mb-4 ${
    type === 'success' ? 'bg-primary text-primary-foreground' : 'bg-destructive text-destructive-foreground'
  }`;
  notification.textContent = message;
  
  const container = document.querySelector('main') || document.body;
  container.insertBefore(notification, container.firstChild);
  
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Debounce helper for search/filter inputs
function debounce(func, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

// Format currency
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

// Format date
function formatDate(dateString) {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString('en-US', options);
}