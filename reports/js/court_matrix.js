/**
 * Court Matrix 14x10 Tactical Grid Renderer
 * Reactive to active filters (Team, Position, Search)
 */
window.CourtMatrix = (function() {
  let mode = 'leader'; // 'leader' or 'balance'
  let containerEl = null;
  let tooltipEl = null;
  let currentFilteredPlayers = null;

  function init(containerId, tooltipId) {
    containerEl = document.getElementById(containerId);
    tooltipEl = document.getElementById(tooltipId);
    render();
  }

  function setMode(newMode) {
    mode = newMode;
    render();
  }

  function updateData(filteredPlayers) {
    currentFilteredPlayers = filteredPlayers;
    render();
  }

  function render() {
    if (!containerEl || !window.COCKPIT_DATA) return;
    const data = window.COCKPIT_DATA;
    const matrix = data.court_matrix_14x10 || [];
    const filteredSet = currentFilteredPlayers ? new Set(currentFilteredPlayers.map(p => p.player_id)) : null;

    // ViewBox: 0 0 940 500 representing 94ft x 50ft (FIBA court proportions)
    // 14 cols: width = 940 / 14 = 67.14
    // 10 rows: height = 500 / 10 = 50.0
    const colW = 940 / 14;
    const rowH = 500 / 10;

    let svgHtml = `
      <svg class="court-svg" viewBox="0 0 940 500" xmlns="http://www.w3.org/2000/svg">
        <!-- Court Floor -->
        <rect x="0" y="0" width="940" height="500" fill="#080c14" rx="8" />
        
        <!-- Court Boundary and Markings -->
        <rect x="10" y="10" width="920" height="480" fill="none" stroke="#1e293b" stroke-width="2" />
        <line x1="470" y1="10" x2="470" y2="490" stroke="#1e293b" stroke-width="2" />
        <circle cx="470" cy="250" r="60" fill="none" stroke="#1e293b" stroke-width="2" />
        
        <!-- Left Basket (Negative X) -->
        <circle cx="70" cy="250" r="12" fill="none" stroke="#f59e0b" stroke-width="2" />
        <rect x="10" y="160" width="180" height="180" fill="none" stroke="#1e293b" stroke-width="2" />
        <path d="M 10 50 L 140 50 A 237.5 237.5 0 0 1 140 450 L 10 450" fill="none" stroke="#334155" stroke-width="2" stroke-dasharray="4,4" />

        <!-- Right Basket (Positive X) -->
        <circle cx="870" cy="250" r="12" fill="none" stroke="#f59e0b" stroke-width="2" />
        <rect x="750" y="160" width="180" height="180" fill="none" stroke="#1e293b" stroke-width="2" />
        <path d="M 930 50 L 800 50 A 237.5 237.5 0 0 0 800 450 L 930 450" fill="none" stroke="#334155" stroke-width="2" stroke-dasharray="4,4" />
        
        <!-- 14x10 Tactical Blocks -->
        <g id="court-grid-cells">
    `;

    matrix.forEach((cell, idx) => {
      const x = cell.col * colW;
      const y = cell.row * rowH;

      // Filter matching check
      let matchingLeader = null;
      let hasFilterMatch = true;

      if (filteredSet) {
        // Find if top players in this cell match the active filter
        const matchedPlayer = (cell.top_players || []).find(tp => {
          const fullP = currentFilteredPlayers.find(p => p.player_name === tp.name);
          return fullP != null;
        });

        if (matchedPlayer) {
          matchingLeader = matchedPlayer;
        } else {
          hasFilterMatch = false;
        }
      }

      let fillColor = "rgba(255, 255, 255, 0.02)";
      let strokeColor = "rgba(255, 255, 255, 0.05)";
      let textColor = "#94a3b8";
      let labelText = cell.leader_initials || "";
      let cellOpacity = hasFilterMatch ? "1.0" : "0.2";

      if (mode === 'leader') {
        const displayVal = matchingLeader ? matchingLeader.score : cell.leader_value;
        const valAlpha = Math.min(0.55, Math.max(0.10, displayVal * 0.18));
        
        if (hasFilterMatch) {
          fillColor = `rgba(56, 189, 248, ${valAlpha.toFixed(2)})`;
          strokeColor = "rgba(56, 189, 248, 0.25)";
          textColor = "#f8fafc";
          if (matchingLeader) {
            const parts = matchingLeader.name.split(' ');
            labelText = parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : matchingLeader.name.substring(0, 2).toUpperCase();
          }
        } else {
          fillColor = "rgba(255, 255, 255, 0.02)";
          labelText = "—";
        }
      } else {
        // Balance BAV vs SCI
        const ratio = cell.balance_ratio;
        if (!hasFilterMatch) {
          fillColor = "rgba(255, 255, 255, 0.02)";
          labelText = "—";
        } else if (ratio > 0.05) {
          const a = Math.min(0.60, 0.15 + ratio * 0.45);
          fillColor = `rgba(56, 189, 248, ${a.toFixed(2)})`;
          strokeColor = "rgba(56, 189, 248, 0.35)";
          textColor = "#38bdf8";
          labelText = `+${Math.round(ratio * 100)}% BAV`;
        } else if (ratio < -0.05) {
          const a = Math.min(0.60, 0.15 + Math.abs(ratio) * 0.45);
          fillColor = `rgba(192, 132, 252, ${a.toFixed(2)})`;
          strokeColor = "rgba(192, 132, 252, 0.35)";
          textColor = "#c084fc";
          labelText = `+${Math.round(Math.abs(ratio) * 100)}% SCI`;
        } else {
          fillColor = "rgba(255, 255, 255, 0.06)";
          labelText = "BAL";
        }
      }

      svgHtml += `
        <g class="court-block" data-idx="${idx}" opacity="${cellOpacity}">
          <rect x="${x + 1.5}" y="${y + 1.5}" width="${colW - 3}" height="${rowH - 3}" rx="4"
                fill="${fillColor}" stroke="${strokeColor}" stroke-width="1" />
          <text x="${x + colW / 2}" y="${y + rowH / 2 + 4}" 
                text-anchor="middle" font-size="${mode === 'leader' ? '12' : '9'}" font-weight="700" fill="${textColor}">
            ${labelText}
          </text>
        </g>
      `;
    });

    svgHtml += `
        </g>
      </svg>
    `;

    containerEl.innerHTML = svgHtml;
    bindEvents(matrix);
  }

  function bindEvents(matrix) {
    const blocks = containerEl.querySelectorAll('.court-block');
    blocks.forEach(block => {
      const idx = parseInt(block.getAttribute('data-idx'), 10);
      const cell = matrix[idx];

      block.addEventListener('mousemove', (e) => {
        if (!tooltipEl || !cell) return;
        tooltipEl.style.display = 'block';
        tooltipEl.style.left = (e.pageX + 15) + 'px';
        tooltipEl.style.top = (e.pageY - 20) + 'px';

        const top3Html = (cell.top_players || []).map(p => 
          `<li style="margin-top: 3px; display: flex; justify-content: space-between;">
             <span>${p.name} <small style="color: #64748b">(${p.team})</small></span>
             <strong style="color: #4ade80">+${p.score}</strong>
           </li>`
        ).join('');

        tooltipEl.innerHTML = `
          <div style="font-weight: 800; font-size: 13px; color: #38bdf8; margin-bottom: 4px;">
            ${cell.zone_type}
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-bottom: 6px;">
            Column ${cell.col + 1}/14 · Row ${cell.row + 1}/10 · <strong>${cell.actions_count} Actions</strong>
          </div>
          <div style="display: flex; gap: 8px; margin-bottom: 8px; font-size: 11px;">
            <span style="color: #38bdf8;">BAV: ${cell.bav_sum.toFixed(2)}</span>
            <span style="color: #c084fc;">SCI: ${cell.sci_sum.toFixed(2)}</span>
          </div>
          <div style="font-size: 11px; font-weight: 700; color: #f8fafc; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px; margin-bottom: 4px;">
            Top Zone Contributors:
          </div>
          <ul style="list-style: none; padding: 0; margin: 0; font-size: 11px;">
            ${top3Html}
          </ul>
        `;
      });

      block.addEventListener('mouseleave', () => {
        if (tooltipEl) tooltipEl.style.display = 'none';
      });

      block.addEventListener('click', () => {
        if (cell && cell.leader_name && window.ScoutingDrawer) {
          window.ScoutingDrawer.openPlayerByName(cell.leader_name);
        }
      });
    });
  }

  return { init, setMode, updateData, render };
})();
