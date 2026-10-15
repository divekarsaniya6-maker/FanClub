/**
 * FanClub - Team Management Logic
 * (static/js/teams.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initTeamSearch();
  initCreateTeamModal();
  initJoinTeamByCode();
  initTeamActions();
  initCopyCodeButtons();
});

// -------------------------------------------------------------
// Team Directory Search
// -------------------------------------------------------------
function initTeamSearch() {
  const searchInput = document.getElementById('teamSearchInput');
  const teamCards = document.querySelectorAll('.team-card');
  const emptyState = document.getElementById('teamsEmptyState');

  if (!searchInput) return;

  searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase().trim();
    let visible = 0;

    teamCards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const city = (card.getAttribute('data-city') || '').toLowerCase();
      const captain = (card.getAttribute('data-captain') || '').toLowerCase();

      if (!query || name.includes(query) || city.includes(query) || captain.includes(query)) {
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
}

// -------------------------------------------------------------
// Create Team Modal & Handler
// -------------------------------------------------------------
function initCreateTeamModal() {
  const openBtn = document.getElementById('btnOpenCreateTeamModal');
  const modal = document.getElementById('createTeamModal');
  const form = document.getElementById('createTeamForm');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => openModal(modal));
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('teamName')?.value.trim();
      const city = document.getElementById('teamCity')?.value.trim();
      const description = document.getElementById('teamDescription')?.value.trim();

      if (!name || !city) {
        showToast('Please enter both team name and home city.', 'warning');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Creating...`;

      const result = await apiFetch('/teams/create', {
        method: 'POST',
        body: JSON.stringify({ name, city, description })
      });

      if (result.ok && result.data.success) {
        showToast('Football team registered successfully!', 'success');
        setTimeout(() => {
          window.location.href = result.data.redirect || `/teams/${result.data.team_id}`;
        }, 700);
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origText;
        showToast(result.data.message || 'Could not register team.', 'error');
      }
    });
  }
}

// -------------------------------------------------------------
// Join Team By Unique Code
// -------------------------------------------------------------
function initJoinTeamByCode() {
  const openBtn = document.getElementById('btnOpenJoinByCodeModal');
  const modal = document.getElementById('joinByCodeModal');
  const form = document.getElementById('joinByCodeForm');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => openModal(modal));
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const code = document.getElementById('teamCodeInput')?.value.trim().toUpperCase();

      if (!code) {
        showToast('Please enter a team code.', 'warning');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Joining...`;

      const result = await apiFetch('/teams/join-code', {
        method: 'POST',
        body: JSON.stringify({ team_code: code })
      });

      if (result.ok && result.data.success) {
        showToast(result.data.message || 'Successfully joined the team!', 'success');
        setTimeout(() => {
          window.location.href = result.data.redirect || `/teams/${result.data.team_id}`;
        }, 700);
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origText;
        showToast(result.data.message || 'Invalid team code or membership error.', 'error');
      }
    });
  }
}

// -------------------------------------------------------------
// Team Actions: Join / Leave from Team Details
// -------------------------------------------------------------
function initTeamActions() {
  // Direct Join
  const joinBtn = document.getElementById('btnJoinTeamDirect');
  if (joinBtn) {
    joinBtn.addEventListener('click', async () => {
      const teamId = joinBtn.getAttribute('data-team-id');
      joinBtn.disabled = true;
      joinBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Joining Team...`;

      const result = await apiFetch(`/teams/${teamId}/join`, {
        method: 'POST'
      });

      if (result.ok && result.data.success) {
        showToast('You have joined the squad!', 'success');
        setTimeout(() => window.location.reload(), 600);
      } else {
        joinBtn.disabled = false;
        joinBtn.innerHTML = `<i class="fa-solid fa-user-plus"></i> Join Squad`;
        showToast(result.data.message || 'Could not join team.', 'error');
      }
    });
  }

  // Leave Team
  const leaveBtn = document.getElementById('btnLeaveTeam');
  if (leaveBtn) {
    leaveBtn.addEventListener('click', async () => {
      const teamId = leaveBtn.getAttribute('data-team-id');
      if (!confirm('Are you sure you want to leave this team?')) return;

      leaveBtn.disabled = true;
      leaveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Leaving...`;

      const result = await apiFetch(`/teams/${teamId}/leave`, {
        method: 'POST'
      });

      if (result.ok && result.data.success) {
        showToast('You have left the team.', 'info');
        setTimeout(() => window.location.reload(), 600);
      } else {
        leaveBtn.disabled = false;
        leaveBtn.innerHTML = `<i class="fa-solid fa-arrow-right-from-bracket"></i> Leave Team`;
        showToast(result.data.message || 'Could not leave team.', 'error');
      }
    });
  }
}

// -------------------------------------------------------------
// Copy Team Code to Clipboard
// -------------------------------------------------------------
function initCopyCodeButtons() {
  document.querySelectorAll('.btn-copy-code').forEach(btn => {
    btn.addEventListener('click', async () => {
      const code = btn.getAttribute('data-code');
      if (!code) return;

      try {
        await navigator.clipboard.writeText(code);
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
        btn.classList.add('btn-copied');
        showToast(`Team code ${code} copied to clipboard!`, 'success');
        setTimeout(() => {
          btn.innerHTML = originalHtml;
          btn.classList.remove('btn-copied');
        }, 2000);
      } catch (err) {
        showToast(`Code: ${code}`, 'info');
      }
    });
  });
}
