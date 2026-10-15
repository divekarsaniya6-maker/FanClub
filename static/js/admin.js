/**
 * FanClub - Administrator Console Logic
 * (static/js/admin.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initAdminVenues();
  initAdminUsers();
  initAdminBookings();
});

// -------------------------------------------------------------
// Admin Venues Management
// -------------------------------------------------------------
function initAdminVenues() {
  const addModal = document.getElementById('addVenueModal');
  const addBtn = document.getElementById('btnOpenAddVenueModal');
  const addForm = document.getElementById('addVenueForm');

  if (addBtn && addModal) {
    addBtn.addEventListener('click', () => openModal(addModal));
  }

  if (addForm) {
    addForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('venueName')?.value.trim();
      const location = document.getElementById('venueLocation')?.value.trim();
      const price = parseFloat(document.getElementById('venuePrice')?.value) || 200.0;
      const facilities = document.getElementById('venueFacilities')?.value.trim();
      const description = document.getElementById('venueDescription')?.value.trim();
      const imageUrl = document.getElementById('venueImageUrl')?.value.trim();

      if (!name || !location) {
        showToast('Venue name and location are required.', 'warning');
        return;
      }

      const submitBtn = addForm.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;

      const result = await apiFetch('/admin/venues/create', {
        method: 'POST',
        body: JSON.stringify({
          name, location, price_per_slot: price, facilities, description, image_url: imageUrl
        })
      });

      if (result.ok && result.data.success) {
        showToast('New football ground added successfully!', 'success');
        setTimeout(() => window.location.reload(), 700);
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origText;
        showToast(result.data.message || 'Error creating venue.', 'error');
      }
    });
  }

  // Toggle Venue Active / Inactive
  document.querySelectorAll('.btn-toggle-venue-status').forEach(btn => {
    btn.addEventListener('click', async () => {
      const venueId = btn.getAttribute('data-id');
      const currentActive = btn.getAttribute('data-active') === '1';
      const actionText = currentActive ? 'deactivate' : 'activate';

      if (!confirm(`Are you sure you want to ${actionText} this venue?`)) return;

      btn.disabled = true;
      const result = await apiFetch(`/admin/venues/${venueId}/toggle-status`, {
        method: 'POST'
      });

      if (result.ok && result.data.success) {
        showToast(`Venue ${actionText}d successfully.`, 'success');
        setTimeout(() => window.location.reload(), 600);
      } else {
        btn.disabled = false;
        showToast(result.data.message || 'Status toggle failed.', 'error');
      }
    });
  });

  // Edit Venue
  const editModal = document.getElementById('editVenueModal');
  const editForm = document.getElementById('editVenueForm');

  document.querySelectorAll('.btn-edit-venue').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!editModal) return;
      document.getElementById('editVenueId').value = btn.getAttribute('data-id');
      document.getElementById('editVenueName').value = btn.getAttribute('data-name');
      document.getElementById('editVenueLocation').value = btn.getAttribute('data-location');
      document.getElementById('editVenuePrice').value = btn.getAttribute('data-price');
      document.getElementById('editVenueFacilities').value = btn.getAttribute('data-facilities') || '';
      document.getElementById('editVenueDescription').value = btn.getAttribute('data-desc') || '';
      document.getElementById('editVenueImageUrl').value = btn.getAttribute('data-image') || '';
      openModal(editModal);
    });
  });

  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('editVenueId').value;
      const name = document.getElementById('editVenueName').value.trim();
      const location = document.getElementById('editVenueLocation').value.trim();
      const price = parseFloat(document.getElementById('editVenuePrice').value) || 200.0;
      const facilities = document.getElementById('editVenueFacilities').value.trim();
      const description = document.getElementById('editVenueDescription').value.trim();
      const imageUrl = document.getElementById('editVenueImageUrl').value.trim();

      const result = await apiFetch(`/admin/venues/${id}/edit`, {
        method: 'POST',
        body: JSON.stringify({ name, location, price_per_slot: price, facilities, description, image_url: imageUrl })
      });

      if (result.ok && result.data.success) {
        showToast('Venue updated successfully!', 'success');
        setTimeout(() => window.location.reload(), 600);
      } else {
        showToast(result.data.message || 'Error updating venue.', 'error');
      }
    });
  }
}

// -------------------------------------------------------------
// Admin Users Management
// -------------------------------------------------------------
function initAdminUsers() {
  const searchInput = document.getElementById('adminUserSearch');
  const userRows = document.querySelectorAll('.admin-user-row');

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase().trim();
      userRows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = (!q || text.includes(q)) ? '' : 'none';
      });
    });
  }

  // Toggle user role
  document.querySelectorAll('.btn-toggle-role').forEach(btn => {
    btn.addEventListener('click', async () => {
      const userId = btn.getAttribute('data-id');
      const currentRole = btn.getAttribute('data-role');
      const newRole = currentRole === 'admin' ? 'user' : 'admin';

      if (!confirm(`Are you sure you want to change this user's role to ${newRole.toUpperCase()}?`)) return;

      btn.disabled = true;
      const result = await apiFetch(`/admin/users/${userId}/toggle-role`, {
        method: 'POST',
        body: JSON.stringify({ role: newRole })
      });

      if (result.ok && result.data.success) {
        showToast(`Role updated to ${newRole.toUpperCase()}.`, 'success');
        setTimeout(() => window.location.reload(), 600);
      } else {
        btn.disabled = false;
        showToast(result.data.message || 'Could not update role.', 'error');
      }
    });
  });
}

// -------------------------------------------------------------
// Admin Bookings Management
// -------------------------------------------------------------
function initAdminBookings() {
  const searchInput = document.getElementById('adminBookingSearch');
  const statusFilter = document.getElementById('adminBookingStatusFilter');
  const bookingRows = document.querySelectorAll('.admin-booking-row');

  function filterBookings() {
    const q = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const st = statusFilter ? statusFilter.value.toLowerCase().trim() : '';

    bookingRows.forEach(row => {
      const text = row.innerText.toLowerCase();
      const rowStatus = (row.getAttribute('data-status') || '').toLowerCase();

      const matchQ = !q || text.includes(q);
      const matchSt = !st || rowStatus === st;

      row.style.display = (matchQ && matchSt) ? '' : 'none';
    });
  }

  if (searchInput) searchInput.addEventListener('input', filterBookings);
  if (statusFilter) statusFilter.addEventListener('change', filterBookings);

  // Update Booking Status dropdown or buttons
  document.querySelectorAll('.admin-booking-status-select').forEach(select => {
    select.addEventListener('change', async () => {
      const bookingId = select.getAttribute('data-id');
      const newStatus = select.value;

      select.disabled = true;
      const result = await apiFetch(`/admin/bookings/${bookingId}/update-status`, {
        method: 'POST',
        body: JSON.stringify({ status: newStatus })
      });

      select.disabled = false;
      if (result.ok && result.data.success) {
        showToast(`Booking status updated to ${newStatus}.`, 'success');
        const row = select.closest('tr');
        if (row) row.setAttribute('data-status', newStatus);
      } else {
        showToast(result.data.message || 'Could not update booking status.', 'error');
      }
    });
  });
}
