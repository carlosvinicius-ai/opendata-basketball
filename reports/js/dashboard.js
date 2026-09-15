/**
 * Global Reactive Dashboard Controller
 * Synchronizes: KPIs, Top 5, Full-Width Court Matrix, Radar, Scatter, and Table
 * 100% English
 */
window.Dashboard = (function() {
  let state = {
    selectedTeam: 'ALL',
    selectedPosition: 'ALL',
    searchQuery: '',
    currentPage: 1,
    pageSize: 15,
    sortCol: 'fspv_score',
    sortAsc: false,
  };

  function init() {
    if (!window.COCKPIT_DATA) {
      console.error("Cockpit data not found!");
      return;
    }

    // Init components
    if (window.CourtMatrix) window.CourtMatrix.init('courtMatrixContainer', 'courtTooltip');
    if (window.RadarChart) window.RadarChart.init('radarChartCanvas');
    if (window.ScatterPlot) window.ScatterPlot.init('scatterChartCanvas');
    if (window.ScoutingDrawer) window.ScoutingDrawer.init();

    populateTeamDropdown();
    bindFilters();
    bindAuditToggle();
    bindCourtModes();
    bindTableSorting();

    update();
  }

  function bindAuditToggle() {
    const btn = document.getElementById('btnToggleAudit');
    const drawer = document.getElementById('auditDrawer');
    if (btn && drawer) {
      btn.addEventListener('click', () => {
        drawer.classList.toggle('open');
        btn.textContent = drawer.classList.contains('open') ? '▲ Hide Scientific Audit' : '▼ Scientific Audit & Rigor';
      });
    }
  }

  function bindCourtModes() {
    const btnLeader = document.getElementById('modeBtnLeader');
    const btnBalance = document.getElementById('modeBtnBalance');
    if (btnLeader && btnBalance) {
      btnLeader.addEventListener('click', () => {
        btnLeader.classList.add('active');
        btnBalance.classList.remove('active');
        if (window.CourtMatrix) window.CourtMatrix.setMode('leader');
      });
      btnBalance.addEventListener('click', () => {
        btnBalance.classList.add('active');
        btnLeader.classList.remove('active');
        if (window.CourtMatrix) window.CourtMatrix.setMode('balance');
      });
    }
  }

  function populateTeamDropdown() {
    const select = document.getElementById('teamSelect');
    if (!select || !window.COCKPIT_DATA.teams) return;
    
    window.COCKPIT_DATA.teams.forEach(team => {
      const opt = document.createElement('option');
      opt.value = team;
      opt.textContent = team;
      select.appendChild(opt);
    });

    select.addEventListener('change', (e) => {
      state.selectedTeam = e.target.value;
      state.currentPage = 1;
      update();
    });
  }

  function bindFilters() {
    // Position chips
    const chips = document.querySelectorAll('.pos-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.selectedPosition = chip.getAttribute('data-pos');
        state.currentPage = 1;
        update();
      });
    });

    // Search input
    const searchInput = document.getElementById('playerSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.toLowerCase().trim();
        state.currentPage = 1;
        update();
      });
    }

    // Pagination
    const prevBtn = document.getElementById('btnPrevPage');
    const nextBtn = document.getElementById('btnNextPage');
    if (prevBtn) prevBtn.addEventListener('click', () => {
      if (state.currentPage > 1) {
        state.currentPage--;
        renderTable();
      }
    });
    if (nextBtn) nextBtn.addEventListener('click', () => {
      state.currentPage++;
      renderTable();
    });
  }

  function filterByPosition(pos) {
    const chips = document.querySelectorAll('.pos-chip');
    chips.forEach(chip => {
      if (chip.getAttribute('data-pos') === pos) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
    state.selectedPosition = pos;
    state.currentPage = 1;
    update();
  }

  function getFilteredPlayers() {
    let list = window.COCKPIT_DATA.players || [];

    if (state.selectedTeam !== 'ALL') {
      list = list.filter(p => p.team === state.selectedTeam);
    }
    if (state.selectedPosition !== 'ALL') {
      list = list.filter(p => p.position === state.selectedPosition);
    }
    if (state.searchQuery) {
      list = list.filter(p => 
        p.player_name.toLowerCase().includes(state.searchQuery) ||
        p.team.toLowerCase().includes(state.searchQuery) ||
        (p.archetype && p.archetype.toLowerCase().includes(state.searchQuery))
      );
    }

    // Sort
    list.sort((a, b) => {
      let valA = a[state.sortCol];
      let valB = b[state.sortCol];
      if (typeof valA === 'string') return state.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      return state.sortAsc ? (valA - valB) : (valB - valA);
    });

    return list;
  }

  function update() {
    const filtered = getFilteredPlayers();
    renderKPIs(filtered);
    renderTop5(filtered);
    renderTable(filtered);

    // Synchronize All Visualizations
    if (window.CourtMatrix) window.CourtMatrix.updateData(filtered);
    if (window.RadarChart) window.RadarChart.updateData(filtered);
    if (window.ScatterPlot) window.ScatterPlot.updateData(filtered);
  }

  function renderKPIs(filtered) {
    if (!filtered || filtered.length === 0) {
      document.getElementById('kpiFspvLeadName').textContent = 'No player found';
      document.getElementById('kpiBavLeadName').textContent = 'No player found';
      document.getElementById('kpiSciLeadName').textContent = 'No player found';
      document.getElementById('kpiAvgScore').textContent = '0.00';
      return;
    }

    const topFspv = filtered[0];
    const topBav = [...filtered].sort((a, b) => b.bav_score - a.bav_score)[0];
    const topSci = [...filtered].sort((a, b) => b.sci_score - a.sci_score)[0];
    const avgFspv = (filtered.reduce((acc, p) => acc + p.fspv_score, 0) / filtered.length).toFixed(2);

    // KPI 1: FSPV Leader
    document.getElementById('kpiFspvLeadName').textContent = topFspv.player_name;
    document.getElementById('kpiFspvLeadTeam').textContent = `${topFspv.team} · ${topFspv.position}`;
    document.getElementById('kpiFspvScore').textContent = `+${topFspv.fspv_score}`;
    document.getElementById('kpiFspvPct').textContent = `${topFspv.fspv_percentile}% Top`;

    // KPI 2: On-Ball Engine
    document.getElementById('kpiBavLeadName').textContent = topBav.player_name;
    document.getElementById('kpiBavLeadTeam').textContent = `${topBav.team} · ${topBav.position}`;
    document.getElementById('kpiBavScore').textContent = `+${topBav.bav_score}`;
    document.getElementById('kpiBavPct').textContent = `${topBav.bav_percentile}% BAV`;

    // KPI 3: Off-Ball Anchor
    document.getElementById('kpiSciLeadName').textContent = topSci.player_name;
    document.getElementById('kpiSciLeadTeam').textContent = `${topSci.team} · ${topSci.position}`;
    document.getElementById('kpiSciScore').textContent = `+${topSci.sci_score}`;
    document.getElementById('kpiSciPct').textContent = `${topSci.sci_percentile}% SCI`;

    // KPI 4: Rotation Average
    document.getElementById('kpiAvgScore').textContent = `${avgFspv >= 0 ? '+' : ''}${avgFspv}`;
    document.getElementById('kpiCohortCount').textContent = `${filtered.length} Evaluated Players`;
  }

  function renderTop5(filtered) {
    const container = document.getElementById('top5Container');
    if (!container) return;
    const top5 = filtered.slice(0, 5);

    if (top5.length === 0) {
      container.innerHTML = '<p style="grid-column: 1/-1; color: var(--text-muted);">No player matches the active filters.</p>';
      return;
    }

    container.innerHTML = top5.map((p, idx) => `
      <div class="top5-card" onclick="window.ScoutingDrawer.openPlayerByName('${p.player_name.replace(/'/g, "\'")}')">
        <div style="display: flex; justify-content: space-between;">
          <span class="top5-rank">#${idx + 1}</span>
          <span style="font-size: 10px; font-weight: 700; color: #4ade80;">${p.fspv_percentile}%</span>
        </div>
        <div class="top5-name">${p.player_name}</div>
        <div class="top5-meta">${p.team} · ${p.position}</div>
        <div style="margin-top: 6px; font-size: 11px; display: flex; gap: 6px;">
          <span style="color: #38bdf8;">BAV +${p.bav_score}</span>
          <span style="color: #c084fc;">SCI +${p.sci_score}</span>
        </div>
      </div>
    `).join('');
  }

  function bindTableSorting() {
    const headers = document.querySelectorAll('.data-table th[data-sort]');
    headers.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (state.sortCol === col) {
          state.sortAsc = !state.sortAsc;
        } else {
          state.sortCol = col;
          state.sortAsc = false;
        }
        update();
      });
    });
  }

  function renderTable(prefiltered) {
    const filtered = prefiltered || getFilteredPlayers();
    const tbody = document.getElementById('tableBody');
    const infoEl = document.getElementById('tablePageInfo');
    const prevBtn = document.getElementById('btnPrevPage');
    const nextBtn = document.getElementById('btnNextPage');
    if (!tbody) return;

    const total = filtered.length;
    const totalPages = Math.ceil(total / state.pageSize) || 1;
    if (state.currentPage > totalPages) state.currentPage = totalPages;

    const startIdx = (state.currentPage - 1) * state.pageSize;
    const pageItems = filtered.slice(startIdx, startIdx + state.pageSize);

    if (infoEl) infoEl.textContent = `Page ${state.currentPage} of ${totalPages} (${total} players)`;
    if (prevBtn) prevBtn.disabled = state.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = state.currentPage >= totalPages;

    tbody.innerHTML = pageItems.map((p, idx) => {
      const overallRank = startIdx + idx + 1;
      const initials = p.player_name.split(' ').map(n => n[0]).slice(0, 2).join('');
      
      let badgeClass = 'pill-fspv';
      if (p.archetype === 'Primary Ball Creator') badgeClass = 'pill-bav';
      else if (p.archetype === 'Space Creator') badgeClass = 'pill-sci';
      else if (p.archetype === 'Dual-Threat Star') badgeClass = 'pill-gold';

      return `
        <tr onclick="window.ScoutingDrawer.openPlayerByName('${p.player_name.replace(/'/g, "\'")}')">
          <td style="font-weight: 700; color: #94a3b8;">#${overallRank}</td>
          <td>
            <div class="player-cell-main">
              <div class="player-avatar">${initials}</div>
              <div>
                <div style="font-weight: 700; color: #f8fafc;">${p.player_name}</div>
                <div style="font-size: 11px; color: #64748b;">#${p.jersey}</div>
              </div>
            </div>
          </td>
          <td style="color: #cbd5e1;">${p.team}</td>
          <td><span style="font-weight: 700; color: #e2e8f0;">${p.position}</span></td>
          <td><span class="badge-pill ${badgeClass}" style="font-size: 10px; padding: 2px 6px; border-radius: 4px;">${p.archetype}</span></td>
          <td style="color: #38bdf8; font-weight: 700;">${p.bav_score >= 0 ? '+' : ''}${p.bav_score}</td>
          <td style="color: #c084fc; font-weight: 700;">${p.sci_score >= 0 ? '+' : ''}${p.sci_score}</td>
          <td style="color: #4ade80; font-weight: 800; font-size: 14px;">${p.fspv_score >= 0 ? '+' : ''}${p.fspv_score}</td>
          <td style="color: #f8fafc; font-weight: 700;">${p.fspv_percentile}%</td>
        </tr>
      `;
    }).join('');
  }

  return { init, filterByPosition };
})();

document.addEventListener('DOMContentLoaded', () => {
  window.Dashboard.init();
});
