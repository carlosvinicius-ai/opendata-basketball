/**
 * Tactical Archetype Scatter Plot (BAV vs SCI Percentiles)
 * Filter-reactive and 100% English
 */
window.ScatterPlot = (function() {
  let chartInstance = null;

  function init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.COCKPIT_DATA) return;
    render(window.COCKPIT_DATA.players || []);
  }

  function updateData(filteredPlayers) {
    render(filteredPlayers);
  }

  function render(players) {
    const canvas = document.getElementById('scatterChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const groups = {
      'Dual-Threat Star': [],
      'Primary Ball Creator': [],
      'Space Creator': [],
      'System / Rotation Contributor': [],
    };

    players.forEach(p => {
      const arch = p.archetype || 'System / Rotation Contributor';
      if (!groups[arch]) groups[arch] = [];
      groups[arch].push({
        x: p.bav_percentile,
        y: p.sci_percentile,
        player: p
      });
    });

    const datasets = [
      {
        label: 'Dual-Threat Stars',
        data: groups['Dual-Threat Star'],
        backgroundColor: '#4ade80',
        borderColor: '#166534',
        pointRadius: 6,
        pointHoverRadius: 9,
      },
      {
        label: 'Primary Ball Creators',
        data: groups['Primary Ball Creator'],
        backgroundColor: '#38bdf8',
        borderColor: '#0369a1',
        pointRadius: 5,
        pointHoverRadius: 8,
      },
      {
        label: 'Space Creators',
        data: groups['Space Creator'],
        backgroundColor: '#c084fc',
        borderColor: '#6b21a8',
        pointRadius: 5,
        pointHoverRadius: 8,
      },
      {
        label: 'System / Rotation',
        data: groups['System / Rotation Contributor'],
        backgroundColor: '#64748b',
        borderColor: '#334155',
        pointRadius: 4,
        pointHoverRadius: 7,
      }
    ];

    chartInstance = new Chart(ctx, {
      type: 'scatter',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: (e, elements) => {
          if (elements && elements.length > 0) {
            const el = elements[0];
            const pData = datasets[el.datasetIndex].data[el.index];
            if (pData && pData.player && window.ScoutingDrawer) {
              window.ScoutingDrawer.openPlayer(pData.player);
            }
          }
        },
        scales: {
          x: {
            min: 0,
            max: 100,
            title: {
              display: true,
              text: 'On-Ball Percentile (BAV %)',
              color: '#38bdf8',
              font: { size: 12, weight: '700' }
            },
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            ticks: { color: '#94a3b8' }
          },
          y: {
            min: 0,
            max: 100,
            title: {
              display: true,
              text: 'Off-Ball Spacing Percentile (SCI %)',
              color: '#c084fc',
              font: { size: 12, weight: '700' }
            },
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            ticks: { color: '#94a3b8' }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#cbd5e1',
              font: { size: 11, weight: '600' },
              boxWidth: 12,
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                const p = context.raw.player;
                return [
                  `${p.player_name} (${p.team}) · ${p.position}`,
                  `FSPV: +${p.fspv_score} (${p.fspv_percentile}%)`,
                  `BAV: +${p.bav_score} | SCI: +${p.sci_score}`
                ];
              }
            }
          }
        }
      }
    });
  }

  return { init, updateData };
})();
