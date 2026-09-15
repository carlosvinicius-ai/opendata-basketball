/**
 * Slide-Over Player Scouting Drawer
 * 100% English
 */
window.ScoutingDrawer = (function() {
  let drawerEl = null;
  let backdropEl = null;

  function init() {
    drawerEl = document.getElementById('scoutingDrawer');
    backdropEl = document.getElementById('drawerBackdrop');

    const closeBtn = document.getElementById('drawerCloseBtn');
    if (closeBtn) closeBtn.addEventListener('click', close);
    if (backdropEl) backdropEl.addEventListener('click', close);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });
  }

  function openPlayerByName(name) {
    if (!window.COCKPIT_DATA) return;
    const player = (window.COCKPIT_DATA.players || []).find(p => p.player_name === name);
    if (player) openPlayer(player);
  }

  function openPlayer(player) {
    if (!drawerEl || !backdropEl) return;
    populateContent(player);
    drawerEl.classList.add('open');
    backdropEl.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    if (!drawerEl || !backdropEl) return;
    drawerEl.classList.remove('open');
    backdropEl.classList.remove('active');
    document.body.style.overflow = '';
  }

  function populateContent(p) {
    document.getElementById('drawerPlayerName').textContent = p.player_name;
    document.getElementById('drawerPlayerTeam').textContent = `${p.team} · #${p.jersey} · ${p.position}`;
    document.getElementById('drawerArchetypeBadge').textContent = p.archetype;
    
    // Percentiles
    document.getElementById('meterFspvVal').textContent = `${p.fspv_percentile}%`;
    document.getElementById('meterFspvFill').style.width = `${p.fspv_percentile}%`;
    document.getElementById('meterFspvFill').style.background = 'linear-gradient(90deg, #10b981, #4ade80)';

    document.getElementById('meterBavVal').textContent = `${p.bav_percentile}% (Score: +${p.bav_score})`;
    document.getElementById('meterBavFill').style.width = `${p.bav_percentile}%`;
    document.getElementById('meterBavFill').style.background = 'linear-gradient(90deg, #0284c7, #38bdf8)';

    document.getElementById('meterSciVal').textContent = `${p.sci_percentile}% (Score: +${p.sci_score})`;
    document.getElementById('meterSciFill').style.width = `${p.sci_percentile}%`;
    document.getElementById('meterSciFill').style.background = 'linear-gradient(90deg, #7e22ce, #c084fc)';

    // PnR Defense Breakdown
    const pnr = p.pnr_efficiency || { drop: 0.65, switch: 0.60, blitz: 0.50, ice: 0.55 };
    document.getElementById('pnrDropBar').style.width = `${pnr.drop * 100}%`;
    document.getElementById('pnrDropVal').textContent = `${Math.round(pnr.drop * 100)}% PPP`;

    document.getElementById('pnrSwitchBar').style.width = `${pnr.switch * 100}%`;
    document.getElementById('pnrSwitchVal').textContent = `${Math.round(pnr.switch * 100)}% PPP`;

    document.getElementById('pnrBlitzBar').style.width = `${pnr.blitz * 100}%`;
    document.getElementById('pnrBlitzVal').textContent = `${Math.round(pnr.blitz * 100)}% PPP`;

    document.getElementById('pnrIceBar').style.width = `${pnr.ice * 100}%`;
    document.getElementById('pnrIceVal').textContent = `${Math.round(pnr.ice * 100)}% PPP`;

    // Favorite Zones
    const favZonesList = document.getElementById('drawerFavZones');
    if (favZonesList) {
      favZonesList.innerHTML = (p.favorite_zones || []).map(z => 
        `<span style="display:inline-block; padding: 4px 10px; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.3); border-radius: 4px; font-size: 11px; color: #38bdf8; margin: 2px;">
           ${z}
         </span>`
      ).join('');
    }

    // Scouting Directives in English
    const notes = p.scouting_notes || {};
    document.getElementById('drawerStrengths').textContent = notes.strengths || "Versatile contributor across offensive sets and court spacing.";
    document.getElementById('drawerConcessions').textContent = notes.concessions || "Force contested mid-range shots under direct pressure.";
    document.getElementById('drawerScheme').textContent = notes.defense_scheme || "Structured defensive scheme with aggressive closeouts.";
  }

  return { init, openPlayer, openPlayerByName, close };
})();
