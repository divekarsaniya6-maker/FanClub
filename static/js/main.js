/**
 * FanClub - Professional Football Ground Booking & Community Platform
 * Main JavaScript (static/js/main.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initUserDropdown();
  initFlashMessages();
  initModals();
});

// -------------------------------------------------------------
// Mobile Navigation Drawer
// -------------------------------------------------------------
function initMobileNav() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const navMenu = document.querySelector('.nav-menu');

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      navMenu.classList.toggle('active');
      const icon = toggleBtn.querySelector('i');
      if (icon) {
        if (navMenu.classList.contains('active')) {
          icon.classList.remove('fa-bars');
          icon.classList.add('fa-xmark');
        } else {
          icon.classList.remove('fa-xmark');
          icon.classList.add('fa-bars');
        }
      }
    });

    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && !toggleBtn.contains(e.target) && navMenu.classList.contains('active')) {
        navMenu.classList.remove('active');
        const icon = toggleBtn.querySelector('i');
        if (icon) {
          icon.classList.remove('fa-xmark');
          icon.classList.add('fa-bars');
        }
      }
    });
  }
}

// -------------------------------------------------------------
// User Profile Dropdown
// -------------------------------------------------------------
function initUserDropdown() {
  const userTrigger = document.querySelector('.user-menu-trigger');
  const userDropdown = document.querySelector('.user-dropdown');

  if (userTrigger && userDropdown) {
    userTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdown.contains(e.target) && !userTrigger.contains(e.target)) {
        userDropdown.classList.remove('show');
      }
    });
  }
}

// -------------------------------------------------------------
// Auto-dismiss Flash Alerts
// -------------------------------------------------------------
function initFlashMessages() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
      });
    }

    // Auto dismiss after 6 seconds for success/info
    if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
      setTimeout(() => {
        if (document.body.contains(alert)) {
          alert.style.opacity = '0';
          alert.style.transform = 'translateY(-10px)';
          setTimeout(() => alert.remove(), 300);
        }
      }, 6000);
    }
  });
}

// -------------------------------------------------------------
// Toast Notifications
// -------------------------------------------------------------
function showToast(message, type = 'info', duration = 4500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };

  const icon = iconMap[type] || 'fa-bell';

  toast.innerHTML = `
    <i class="fa-solid ${icon}"></i>
    <div class="toast-content">${message}</div>
    <button class="toast-close" type="button" aria-label="Close notification">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-show');
  });

  const closeToast = () => {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 350);
  };

  toast.querySelector('.toast-close').addEventListener('click', closeToast);
  setTimeout(closeToast, duration);
}

// -------------------------------------------------------------
// Modal Helpers
// -------------------------------------------------------------
function initModals() {
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal);
      }
    });
  });
}

function openModal(modalEl) {
  if (typeof modalEl === 'string') {
    modalEl = document.getElementById(modalEl);
  }
  if (!modalEl) return;
  modalEl.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(modalEl) {
  if (typeof modalEl === 'string') {
    modalEl = document.getElementById(modalEl);
  }
  if (!modalEl) return;
  modalEl.classList.remove('active');
  document.body.style.overflow = '';
}

// -------------------------------------------------------------
// Global CSRF helper for Fetch
// -------------------------------------------------------------
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  const token = getCsrfToken();
  if (token) {
    headers['X-CSRF-Token'] = token;
  }
  if (!headers['Content-Type'] && options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  options.headers = headers;
  options.credentials = 'same-origin';

  try {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data };
  } catch (err) {
    console.error('API Fetch error:', err);
    return { ok: false, status: 0, data: { message: 'Network connection error' } };
  }
}
