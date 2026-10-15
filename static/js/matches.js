/**
 * FanClub - Match Scheduling & Fixture Management
 * (static/js/matches.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initMatchTabs();
  initScheduleMatchModal();
});

// -------------------------------------------------------------
// Match Fixture Filtering Tabs
// -------------------------------------------------------------
function initMatchTabs() {
  const tabBtns = document.querySelectorAll('.match-tab-btn');
  const matchCards = document.querySelectorAll('.match-card');
  const emptyState = document.getElementById('matchesEmptyState');

  if (!tabBtns.length) return;

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');
      let visible = 0;

      matchCards.forEach(card => {
        const status = (card.getAttribute('data-status') || '').toLowerCase();

        if (filter === 'all') {
          card.style.display = '';
          visible++;
        } else if (filter === 'upcoming' && status === 'scheduled') {
          card.style.display = '';
          visible++;
        } else if (filter === 'past' && (status === 'completed' || status === 'cancelled')) {
          card.style.display = '';
          visible++;
        } else {
          card.style.display = 'none';
        }
      });

      if (emptyState) {
        emptyState.style.display = visible === 0 ? 'block' : 'none';
      }
    });
  });
}

// -------------------------------------------------------------
// Schedule Match Modal & Validation
// -------------------------------------------------------------
function initScheduleMatchModal() {
  const openBtn = document.getElementById('btnOpenScheduleMatchModal');
  const modal = document.getElementById('scheduleMatchModal');
  const form = document.getElementById('scheduleMatchForm');
  const homeSelect = document.getElementById('matchHomeTeam');
  const awaySelect = document.getElementById('matchAwayTeam');
  const dateInput = document.getElementById('matchDate');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => openModal(modal));
  }

  if (dateInput) {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    dateInput.min = `${year}-${month}-${day}`;
  }

  if (form) {
    // Prevent selecting identical teams
    const validateTeams = () => {
      if (homeSelect && awaySelect && homeSelect.value && awaySelect.value) {
        if (homeSelect.value === awaySelect.value) {
          showToast('Home team and Opponent team cannot be the same.', 'warning');
          return false;
        }
      }
      return true;
    };

    if (homeSelect) homeSelect.addEventListener('change', validateTeams);
    if (awaySelect) awaySelect.addEventListener('change', validateTeams);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!validateTeams()) return;

      const homeTeamId = homeSelect ? homeSelect.value : '';
      const awayTeamId = awaySelect ? awaySelect.value : '';
      const venueId = document.getElementById('matchVenue')?.value;
      const matchDate = dateInput ? dateInput.value : '';
      const matchTime = document.getElementById('matchTime')?.value;
      const notes = document.getElementById('matchNotes')?.value.trim();

      if (!homeTeamId || !awayTeamId || !venueId || !matchDate || !matchTime) {
        showToast('Please fill out all required match fixture fields.', 'warning');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Scheduling Fixture...`;

      const result = await apiFetch('/matches/create', {
        method: 'POST',
        body: JSON.stringify({
          home_team_id: homeTeamId,
          away_team_id: awayTeamId,
          venue_id: venueId,
          match_date: matchDate,
          match_time: matchTime,
          notes: notes
        })
      });

      if (result.ok && result.data.success) {
        showToast('Match fixture scheduled successfully!', 'success');
        setTimeout(() => {
          window.location.reload();
        }, 700);
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origText;
        showToast(result.data.message || 'Could not schedule match.', 'error');
      }
    });
  }
}
