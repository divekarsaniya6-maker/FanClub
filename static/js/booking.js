/**
 * FanClub - Football Ground Booking & Availability Logic
 * (static/js/booking.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initVenueSearchFilter();
  initVenueDetailSlots();
  initBookingCancellation();
});

// -------------------------------------------------------------
// Venues List: Real-time Search & Filter
// -------------------------------------------------------------
function initVenueSearchFilter() {
  const searchInput = document.getElementById('venueSearch');
  const locationFilter = document.getElementById('locationFilter');
  const priceFilter = document.getElementById('priceFilter');
  const venueCards = document.querySelectorAll('.venue-card');
  const emptyState = document.getElementById('venuesEmptyState');

  if (!searchInput && !locationFilter && !priceFilter) return;

  function filterVenues() {
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const loc = locationFilter ? locationFilter.value.toLowerCase().trim() : '';
    const maxPrice = priceFilter ? parseFloat(priceFilter.value) || 999999 : 999999;

    let visibleCount = 0;

    venueCards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const location = (card.getAttribute('data-location') || '').toLowerCase();
      const price = parseFloat(card.getAttribute('data-price')) || 0;

      const matchesQuery = !query || name.includes(query) || location.includes(query);
      const matchesLoc = !loc || location.includes(loc);
      const matchesPrice = price <= maxPrice;

      if (matchesQuery && matchesLoc && matchesPrice) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (emptyState) {
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  if (searchInput) searchInput.addEventListener('input', filterVenues);
  if (locationFilter) locationFilter.addEventListener('change', filterVenues);
  if (priceFilter) priceFilter.addEventListener('change', filterVenues);
}

// -------------------------------------------------------------
// Venue Details: Slot Picker & Dynamic Availability
// -------------------------------------------------------------
function initVenueDetailSlots() {
  const dateInput = document.getElementById('bookingDate');
  const slotsContainer = document.getElementById('slotsContainer');
  const selectedSlotInput = document.getElementById('selectedTimeSlot');
  const bookingForm = document.getElementById('groundBookingForm');
  const venueIdInput = document.getElementById('venueId');

  if (!dateInput || !slotsContainer) return;

  // Set min date to today in Indian timezone (YYYY-MM-DD)
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const todayStr = `${year}-${month}-${day}`;
  if (!dateInput.value) {
    dateInput.value = todayStr;
  }
  dateInput.min = todayStr;

  const venueId = venueIdInput ? venueIdInput.value : '';

  async function loadSlots(dateVal) {
    slotsContainer.innerHTML = `
      <div class="slots-loading">
        <i class="fa-solid fa-spinner fa-spin"></i> Checking real-time ground slot availability...
      </div>
    `;
    selectedSlotInput.value = '';
    updateSummarySlot('');

    try {
      const res = await fetch(`/api/venues/${venueId}/slots?date=${encodeURIComponent(dateVal)}`);
      const data = await res.json();

      if (!res.ok || !data.slots) {
        slotsContainer.innerHTML = `<div class="slots-error"><i class="fa-solid fa-triangle-exclamation"></i> Could not load slots for this date.</div>`;
        return;
      }

      renderSlots(data.slots);
    } catch (err) {
      console.error(err);
      slotsContainer.innerHTML = `<div class="slots-error"><i class="fa-solid fa-triangle-exclamation"></i> Network error loading slots.</div>`;
    }
  }

  function renderSlots(slots) {
    slotsContainer.innerHTML = '';

    if (slots.length === 0) {
      slotsContainer.innerHTML = `<div class="slots-empty">No time slots scheduled for this date.</div>`;
      return;
    }

    slots.forEach(slot => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `slot-pill ${slot.is_available ? 'available' : 'booked'}`;
      btn.disabled = !slot.is_available;

      btn.innerHTML = `
        <span class="slot-time"><i class="fa-regular fa-clock"></i> ${slot.time}</span>
        <span class="slot-status-tag">${slot.is_available ? 'Available' : 'Booked'}</span>
      `;

      if (slot.is_available) {
        btn.addEventListener('click', () => {
          document.querySelectorAll('.slot-pill').forEach(s => s.classList.remove('selected'));
          btn.classList.add('selected');
          selectedSlotInput.value = slot.time;
          updateSummarySlot(slot.time);
        });
      }

      slotsContainer.appendChild(btn);
    });
  }

  function updateSummarySlot(slotTime) {
    const summarySlotEl = document.getElementById('summarySelectedSlot');
    const submitBtn = document.getElementById('btnSubmitBooking');
    if (summarySlotEl) {
      summarySlotEl.textContent = slotTime || 'Please select a time slot above';
      summarySlotEl.style.color = slotTime ? 'var(--accent-green)' : 'var(--text-muted)';
    }
    if (submitBtn) {
      submitBtn.disabled = !slotTime;
    }
  }

  dateInput.addEventListener('change', () => {
    if (dateInput.value) {
      loadSlots(dateInput.value);
      const summaryDateEl = document.getElementById('summarySelectedDate');
      if (summaryDateEl) summaryDateEl.textContent = dateInput.value;
    }
  });

  // Initial load
  loadSlots(dateInput.value);

  // Form Submission
  if (bookingForm) {
    bookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const timeSlot = selectedSlotInput.value;
      if (!timeSlot) {
        showToast('Please select an available time slot before continuing.', 'warning');
        return;
      }

      const contactName = document.getElementById('contactName')?.value.trim();
      const contactPhone = document.getElementById('contactPhone')?.value.trim();

      if (!contactName || !contactPhone) {
        showToast('Please provide your full contact name and phone number.', 'warning');
        return;
      }

      const submitBtn = document.getElementById('btnSubmitBooking');
      const origText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Confirming Reservation in Database...`;

      const payload = {
        venue_id: venueId,
        date: dateInput.value,
        time_slot: timeSlot,
        contact_name: contactName,
        contact_phone: contactPhone
      };

      const result = await apiFetch('/bookings/create', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (result.ok && result.data.success) {
        showToast('Reservation confirmed! Generating digital pass...', 'success');
        setTimeout(() => {
          window.location.href = result.data.redirect || `/bookings/${result.data.booking_id}`;
        }, 500);
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origText;
        showToast(result.data.message || 'Failed to book slot. It may have already been reserved.', 'error');
        // Reload slots to reflect newest database state
        loadSlots(dateInput.value);
      }
    });
  }
}

// -------------------------------------------------------------
// My Bookings: Real Cancellation Handler
// -------------------------------------------------------------
function initBookingCancellation() {
  document.querySelectorAll('.btn-cancel-booking').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const bookingId = btn.getAttribute('data-id');
      const bookingCode = btn.getAttribute('data-code');

      if (!confirm(`Are you sure you want to cancel booking ${bookingCode}? This will permanently release your ground slot.`)) {
        return;
      }

      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Cancelling...`;

      const result = await apiFetch(`/bookings/${bookingId}/cancel`, {
        method: 'POST'
      });

      if (result.ok && result.data.success) {
        showToast('Booking cancelled successfully. Slot is now re-opened.', 'success');
        setTimeout(() => {
          window.location.reload();
        }, 700);
      } else {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-xmark"></i> Cancel Booking`;
        showToast(result.data.message || 'Could not cancel booking.', 'error');
      }
    });
  });
}
