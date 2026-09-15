/**
 * Positional Radar Chart Component with On-Ball & Off-Ball Layers
 * Filter-reactive to active team and position selection
 */
window.RadarChart = (function() {
  let chartInstance = null;
  const labels = ["PG", "SG", "SF", "PF", "C"];

  function init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.COCKPIT_DATA) return;
    render(window.COCKPIT_DATA.players || []);
  }

  function updateData(filteredPlayers) {
    render(filteredPlayers);
  }

  function render(players) {
    const canvas = document.getElementById('radarChartCanvas');
    if (!canvas) return;

    // Compute positional averages for filtered cohort
    const posMap = { PG: [], SG: [], SF: [], PF: [], C: [] };
    players.forEach(p => {
      if (posMap[p.position]) posMap[p.position].push(p);
    });

    const bavData = labels.map(pos => {
      const list = posMap[pos];
      return list.length ? (list.reduce((acc, p) => acc + p.bav_score, 0) / list.length) : 0.0;
    });

    const sciData = labels.map(pos => {
      const list = posMap[pos];
      return list.length ? (list.reduce((acc, p) => acc + p.sci_score, 0) / list.length) : 0.0;
    });

    const ctx = canvas.getContext('2d');
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'On-Ball Value (BAV)',
            data: bavData.map(v => Number(v.toFixed(3))),
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.25)',
            borderWidth: 2,
            pointBackgroundColor: '#38bdf8',
            pointBorderColor: '#ffffff',
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: 'Off-Ball Spacing (SCI)',
            data: sciData.map(v => Number(v.toFixed(3))),
            borderColor: '#c084fc',
            backgroundColor: 'rgba(192, 132, 252, 0.25)',
            borderWidth: 2,
            pointBackgroundColor: '#c084fc',
            pointBorderColor: '#ffffff',
            pointRadius: 4,
            pointHoverRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: (e, elements) => {
          if (elements && elements.length > 0) {
            const index = elements[0].index;
            const clickedPos = labels[index];
            if (window.Dashboard) {
              window.Dashboard.filterByPosition(clickedPos);
            }
          }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
            grid: { color: 'rgba(255, 255, 255, 0.08)' },
            pointLabels: {
              color: '#f8fafc',
              font: { size: 12, weight: '700' }
            },
            ticks: {
              color: '#64748b',
              backdropColor: 'transparent',
              stepSize: 0.5
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#cbd5e1',
              font: { size: 12, weight: '600' },
              boxWidth: 14,
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderColor: '#38bdf8',
            borderWidth: 1,
            titleFont: { weight: '800' },
            bodyFont: { size: 12 },
            callbacks: {
              afterBody: (context) => {
                const pos = context[0].label;
                const count = posMap[pos] ? posMap[pos].length : 0;
                return `Filtered Cohort: ${count} players`;
              }
            }
          }
        }
      }
    });
  }

  return { init, updateData };
})();
