/**
 * Innovexa Main Frontend Application Logic
 * Implements navigation router, data fetching, Chart.js rendering,
 * vis.js network force-graph, and inductive simulation builder.
 */

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

let dashboardChartTimeline = null;
let dashboardChartArchetypes = null;
let networkGraphInstance = null;

// Application State
const state = {
  currentView: 'dashboard',
  selectedBrowseNodeId: null,
  simulatedFeatures: new Set(),
  simulatedConnections: new Set(),
  browsePage: 1,
  browseFilters: { split: 'test', label: '', archetype: '', search_id: '' },
  historyPage: 1,
  historyFilters: { mode: '', prediction: '' },
  activeClusterId: null,
  featureCategories: {}
};

function initApp() {
  setupNavigation();
  setupSidebarToggle();
  loadFeatureCategories();
  navigate('dashboard');
}

// -------------------------------------------------------------
// NAVIGATION & SHELL
// -------------------------------------------------------------
function setupNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      navigate(targetView);
    });
  });
}

function setupSidebarToggle() {
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
    });
  }
}

function navigate(viewName) {
  state.currentView = viewName;

  // Update Nav pills
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Toggle View Containers
  document.querySelectorAll('.page-view').forEach(view => {
    if (view.id === `view-${viewName}`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  // Update Top Header Title
  const titles = {
    dashboard: { title: 'Security Overview Dashboard', sub: 'Real-time telemetry and synthetic injection detection benchmarks' },
    browse: { title: 'Browse Test Profiles (Option A)', sub: 'Inspect verified ground-truth nodes and audit baseline model decisions' },
    simulate: { title: 'Simulate New Profile (Option B)', sub: 'Inductive test sandbox: configure behavioral features & graph connections' },
    network: { title: 'Graph & Community Analysis', sub: 'Explore high-risk Sybil rings and interactive 2-hop local subgraphs' },
    history: { title: 'Detection Interaction Log', sub: 'Auditable transaction ledger of all browse and simulation interactions' },
    modelinfo: { title: 'Model Architecture & Benchmark Info', sub: 'Comparative metrics between baseline models and GNN readiness' }
  };

  const meta = titles[viewName] || { title: 'Innovexa Console', sub: '' };
  document.getElementById('header-title').innerText = meta.title;
  document.getElementById('header-sub').innerText = meta.sub;

  // View Specific Lifecycles
  if (viewName === 'dashboard') loadDashboardView();
  else if (viewName === 'browse') loadBrowseView();
  else if (viewName === 'simulate') loadSimulateView();
  else if (viewName === 'network') loadNetworkView();
  else if (viewName === 'history') loadHistoryView();
}

// -------------------------------------------------------------
// PHASE F1 — DASHBOARD OVERVIEW
// -------------------------------------------------------------
async function loadDashboardView() {
  try {
    const summary = await api.getDashboardSummary();

    // Populate KPI cards
    document.getElementById('kpi-total-profiles').innerText = summary.total_profiles_analyzed.toLocaleString();
    document.getElementById('kpi-fake-detected').innerText = summary.fake_detected.toLocaleString();
    document.getElementById('kpi-genuine-detected').innerText = summary.genuine_detected.toLocaleString();
    document.getElementById('kpi-high-risk').innerText = summary.high_risk_pending_review.toLocaleString();

    // Accuracy subtext
    document.getElementById('kpi-accuracy-metric').innerText = `${(summary.model_accuracy * 100).toFixed(1)}% Benchmark Accuracy`;
    document.getElementById('kpi-f1-metric').innerText = `F1-Score: ${summary.model_f1_score.toFixed(4)}`;

    // Render Timeline Bar Chart
    renderTimelineChart(summary.detections_over_time);

    // Render Archetype Donut Chart
    renderArchetypeChart(summary.archetype_distribution);

  } catch (err) {
    showToast(`Failed to load dashboard summary: ${err.message}`, 'error');
  }
}

function renderTimelineChart(timelineData) {
  const ctx = document.getElementById('chart-timeline');
  if (!ctx) return;

  if (dashboardChartTimeline) dashboardChartTimeline.destroy();

  const labels = timelineData.map(d => d.day);
  const fakes = timelineData.map(d => d.fake_detected);
  const genuines = timelineData.map(d => d.genuine_detected);

  dashboardChartTimeline = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Fake Detected',
          data: fakes,
          backgroundColor: 'rgba(244, 63, 94, 0.75)',
          borderColor: '#f43f5e',
          borderWidth: 1,
          borderRadius: 6
        },
        {
          label: 'Genuine Verified',
          data: genuines,
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          borderColor: '#10b981',
          borderWidth: 1,
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { family: 'Inter' } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b' }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b' }
        }
      }
    }
  });
}

function renderArchetypeChart(archetypeDist) {
  const ctx = document.getElementById('chart-archetypes');
  if (!ctx) return;

  if (dashboardChartArchetypes) dashboardChartArchetypes.destroy();

  const labels = ['Arch A (Sparsity)', 'Arch B (Dense)', 'Arch C (Camouflage)', 'Arch D (Sybil Ring)'];
  const values = [archetypeDist.A || 0, archetypeDist.B || 0, archetypeDist.C || 0, archetypeDist.D || 0];

  dashboardChartArchetypes = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          '#38bdf8', // Cyan
          '#818cf8', // Indigo
          '#f59e0b', // Amber (Camouflage)
          '#f43f5e'  // Rose (Sybil)
        ],
        borderColor: '#0f172a',
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#94a3b8', boxWidth: 12, font: { size: 11, family: 'Inter' } }
        }
      },
      cutout: '72%'
    }
  });
}

// -------------------------------------------------------------
// PHASE F2 — BROWSE PROFILES VIEW (OPTION A)
// -------------------------------------------------------------
async function loadBrowseView() {
  setupBrowseFilters();
  await fetchBrowseProfiles();
}

function setupBrowseFilters() {
  const searchInput = document.getElementById('browse-search-id');
  const labelSelect = document.getElementById('browse-filter-label');
  const archSelect = document.getElementById('browse-filter-arch');

  if (!searchInput.dataset.bound) {
    searchInput.dataset.bound = 'true';
    searchInput.addEventListener('input', debounce(() => {
      state.browseFilters.search_id = searchInput.value.trim();
      state.browsePage = 1;
      fetchBrowseProfiles();
    }, 300));

    labelSelect.addEventListener('change', () => {
      state.browseFilters.label = labelSelect.value;
      state.browsePage = 1;
      fetchBrowseProfiles();
    });

    archSelect.addEventListener('change', () => {
      state.browseFilters.archetype = archSelect.value;
      state.browsePage = 1;
      fetchBrowseProfiles();
    });
  }
}

async function fetchBrowseProfiles() {
  const tbody = document.getElementById('browse-table-body');
  tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 30px;">Loading profile data...</td></tr>`;

  try {
    const params = {
      split: state.browseFilters.split,
      page: state.browsePage,
      page_size: 15
    };
    if (state.browseFilters.label !== '') params.label = parseInt(state.browseFilters.label);
    if (state.browseFilters.archetype !== '') params.archetype = state.browseFilters.archetype;
    if (state.browseFilters.search_id !== '') params.search_id = parseInt(state.browseFilters.search_id);

    const res = await api.getProfiles(params);
    tbody.innerHTML = '';

    if (res.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 30px; color: var(--text-muted);">No matching profiles found</td></tr>`;
      return;
    }

    res.items.forEach(node => {
      const tr = document.createElement('tr');
      tr.style.cursor = 'pointer';
      tr.id = `row-node-${node.node_id}`;
      if (state.selectedBrowseNodeId === node.node_id) tr.classList.add('selected');

      const isFake = node.is_fake;
      const pillClass = isFake ? 'pill-fake' : 'pill-genuine';
      const labelText = isFake ? (node.archetype ? `Fake (${node.archetype})` : 'Fake') : 'Genuine';

      tr.innerHTML = `
        <td style="font-weight: 600; color: var(--text-main);">#${node.node_id}</td>
        <td><span class="pill ${pillClass}">${labelText}</span></td>
        <td>${(node.risk_score * 100).toFixed(1)}%</td>
        <td>${node.degree}</td>
        <td>Comm #${node.community_id}</td>
        <td><button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;">Inspect & Predict</button></td>
      `;

      tr.addEventListener('click', () => {
        selectBrowseNode(node.node_id);
      });

      tbody.appendChild(tr);
    });

    // Update pagination controls
    document.getElementById('browse-pagination-info').innerText = `Page ${res.page} of ${res.total_pages} (${res.total} profiles)`;
    document.getElementById('btn-browse-prev').disabled = (res.page <= 1);
    document.getElementById('btn-browse-next').disabled = (res.page >= res.total_pages);

    // Auto-select first node if none selected
    if (!state.selectedBrowseNodeId && res.items.length > 0) {
      selectBrowseNode(res.items[0].node_id);
    }

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: var(--status-fake);">Error loading profiles: ${err.message}</td></tr>`;
  }
}

async function selectBrowseNode(nodeId) {
  state.selectedBrowseNodeId = nodeId;
  document.querySelectorAll('#browse-table-body tr').forEach(r => r.classList.remove('selected'));
  const targetRow = document.getElementById(`row-node-${nodeId}`);
  if (targetRow) targetRow.classList.add('selected');

  // Trigger Backend Prediction (Option A)
  try {
    const predResult = await api.predictBrowse(nodeId);
    renderBrowseDetail(predResult);
  } catch (err) {
    showToast(`Inference error: ${err.message}`, 'error');
  }
}

function renderBrowseDetail(res) {
  document.getElementById('detail-node-id').innerText = `#${res.node_id}`;
  
  const statusPill = document.getElementById('detail-status-pill');
  if (res.prediction === 1) {
    statusPill.className = 'pill pill-fake';
    statusPill.innerText = `Detected Fake ${res.archetype ? '(' + res.archetype + ')' : ''}`;
  } else {
    statusPill.className = 'pill pill-genuine';
    statusPill.innerText = 'Verified Genuine';
  }

  // Risk Score Meter
  const pct = (res.risk_score * 100).toFixed(1);
  document.getElementById('detail-risk-pct').innerText = `${pct}%`;
  const fill = document.getElementById('detail-meter-fill');
  fill.style.width = `${pct}%`;
  fill.style.backgroundColor = res.prediction === 1 ? 'var(--status-fake)' : 'var(--status-genuine)';

  document.getElementById('detail-degree').innerText = res.degree;
  document.getElementById('detail-clustering').innerText = res.clustering_coefficient.toFixed(3);
  document.getElementById('detail-community').innerText = `Cluster #${res.community_id}`;

  // Feature Categories Breakdown
  const attrContainer = document.getElementById('detail-attribute-tags');
  attrContainer.innerHTML = '';
  const featSummary = res.feature_summary || {};
  const sampleAttrs = featSummary.active_sample || [];

  if (sampleAttrs.length === 0) {
    attrContainer.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-muted);">No positive binary attributes registered</span>`;
  } else {
    sampleAttrs.forEach(attr => {
      const tag = document.createElement('span');
      tag.className = 'attr-tag';
      tag.innerText = `${attr.category}: ${attr.name}`;
      attrContainer.appendChild(tag);
    });
  }
}

// -------------------------------------------------------------
// PHASE F3 — SIMULATE PROFILE VIEW (OPTION B)
// -------------------------------------------------------------
async function loadFeatureCategories() {
  try {
    state.featureCategories = await api.getFeatureCategories();
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
}

async function loadSimulateView() {
  renderSimulateAccordion();
  setupSimulationEvents();
}

function renderSimulateAccordion() {
  const container = document.getElementById('simulate-accordion');
  if (!container || Object.keys(state.featureCategories).length === 0) return;

  container.innerHTML = '';
  const categories = Object.keys(state.featureCategories);

  categories.forEach(catName => {
    const feats = state.featureCategories[catName] || [];
    const group = document.createElement('div');
    group.className = 'category-group';

    group.innerHTML = `
      <div class="category-header">
        <span>${catName} (${feats.length})</span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">Expand ▾</span>
      </div>
      <div class="feature-pill-list" style="display: none;"></div>
    `;

    const header = group.querySelector('.category-header');
    const pillList = group.querySelector('.feature-pill-list');

    // Fill pills (limit preview to first 25 for DOM speed)
    feats.slice(0, 25).forEach(f => {
      const toggle = document.createElement('div');
      toggle.className = 'feature-toggle';
      toggle.innerText = f.feature_name;
      if (state.simulatedFeatures.has(f.feature_index)) toggle.classList.add('active');

      toggle.addEventListener('click', () => {
        if (state.simulatedFeatures.has(f.feature_index)) {
          state.simulatedFeatures.delete(f.feature_index);
          toggle.classList.remove('active');
        } else {
          state.simulatedFeatures.add(f.feature_index);
          toggle.classList.add('active');
        }
        updateSimulateCounters();
      });

      pillList.appendChild(toggle);
    });

    header.addEventListener('click', () => {
      const isHidden = pillList.style.display === 'none';
      pillList.style.display = isHidden ? 'flex' : 'none';
      header.querySelector('span:last-child').innerText = isHidden ? 'Collapse ▴' : 'Expand ▾';
    });

    container.appendChild(group);
  });
}

function setupSimulationEvents() {
  const addConnBtn = document.getElementById('btn-add-connection');
  const connInput = document.getElementById('simulate-conn-input');
  const runBtn = document.getElementById('btn-run-simulation');

  if (addConnBtn && !addConnBtn.dataset.bound) {
    addConnBtn.dataset.bound = 'true';
    addConnBtn.addEventListener('click', () => {
      const val = parseInt(connInput.value);
      if (!isNaN(val) && val >= 0 && val < 4489) {
        if (state.simulatedConnections.size >= 10) {
          showToast('Maximum 10 connection neighbors allowed in sandbox demo', 'warning');
          return;
        }
        state.simulatedConnections.add(val);
        connInput.value = '';
        renderConnectionChips();
      } else {
        showToast('Please enter a valid existing node ID (0 - 4488)', 'error');
      }
    });

    runBtn.addEventListener('click', executeSimulation);
  }
}

function renderConnectionChips() {
  const container = document.getElementById('simulate-connection-chips');
  container.innerHTML = '';
  state.simulatedConnections.forEach(nid => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.innerHTML = `Node #${nid} <span class="chip-remove">&times;</span>`;
    chip.querySelector('.chip-remove').addEventListener('click', () => {
      state.simulatedConnections.delete(nid);
      renderConnectionChips();
    });
    container.appendChild(chip);
  });
  updateSimulateCounters();
}

function updateSimulateCounters() {
  document.getElementById('sim-active-feat-count').innerText = state.simulatedFeatures.size;
  document.getElementById('sim-active-conn-count').innerText = state.simulatedConnections.size;
}

async function executeSimulation() {
  const resultCard = document.getElementById('simulate-result-card');
  resultCard.style.display = 'block';
  resultCard.innerHTML = `<div style="text-align:center; padding: 30px;"><div class="skeleton" style="height: 120px;"></div><p style="margin-top: 10px; color: var(--text-muted);">Synthesizing inductive graph metrics and evaluating Random Forest...</p></div>`;

  try {
    const payload = {
      active_feature_indices: Array.from(state.simulatedFeatures),
      connection_node_ids: Array.from(state.simulatedConnections)
    };

    const res = await api.predictSimulate(payload);

    const isFake = (res.prediction === 1);
    const pillClass = isFake ? 'pill-fake' : 'pill-genuine';
    const fillBg = isFake ? 'var(--status-fake)' : 'var(--status-genuine)';
    const pct = (res.risk_score * 100).toFixed(1);

    resultCard.innerHTML = `
      <div class="card-header">
        <div>
          <h3 class="card-title">Inference Result</h3>
          <span class="card-desc">Evaluated by ${res.model_version}</span>
        </div>
        <span class="pill ${pillClass}">${res.prediction_label}</span>
      </div>

      <div class="risk-meter">
        <div style="display:flex; justify-content:space-between; font-size: 0.85rem;">
          <span style="color: var(--text-secondary);">Calculated Risk Score</span>
          <span style="font-weight:700; color:${fillBg};">${pct}%</span>
        </div>
        <div class="meter-track">
          <div class="meter-fill" style="width: ${pct}%; background-color: ${fillBg};"></div>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-muted); margin-top: 4px;">Tier: <strong style="color:var(--text-main);">${res.risk_tier}</strong></p>
      </div>

      <div class="metric-strip">
        <div class="metric-box">
          <div class="metric-box-val">${res.structural_features.degree}</div>
          <div class="metric-box-lbl">Derived Degree</div>
        </div>
        <div class="metric-box">
          <div class="metric-box-val">${res.structural_features.clustering_coefficient}</div>
          <div class="metric-box-lbl">Local Triangles</div>
        </div>
        <div class="metric-box">
          <div class="metric-box-val">#${res.structural_features.inferred_community_id}</div>
          <div class="metric-box-lbl">Assigned Cluster</div>
        </div>
      </div>
      <p style="font-size: 0.78rem; color: var(--status-genuine); text-align: center; margin-top: 10px;">
        ✓ Recorded automatically to detection history log
      </p>
    `;

    showToast(`Simulation complete: ${res.prediction_label} (${pct}% risk)`, isFake ? 'warning' : 'success');

  } catch (err) {
    resultCard.innerHTML = `<p style="color: var(--status-fake); padding: 20px;">Simulation error: ${err.message}</p>`;
  }
}

// -------------------------------------------------------------
// PHASE F4 — NETWORK ANALYSIS VIEW
// -------------------------------------------------------------
async function loadNetworkView() {
  const clusterListContainer = document.getElementById('network-cluster-list');
  clusterListContainer.innerHTML = '<p style="padding: 20px; color: var(--text-muted);">Loading community clusters...</p>';

  try {
    const res = await api.getClusters();
    clusterListContainer.innerHTML = '';

    res.clusters.forEach(c => {
      const item = document.createElement('div');
      item.className = 'cluster-item';
      if (state.activeClusterId === c.cluster_id) item.classList.add('active');

      const pillClass = c.risk_level === 'High' ? 'pill-fake' : c.risk_level === 'Medium' ? 'pill-warning' : 'pill-genuine';

      item.innerHTML = `
        <div class="cluster-item-title">
          <span>Cluster #${c.cluster_id}</span>
          <span class="pill ${pillClass}">${c.risk_level} Risk</span>
        </div>
        <div class="cluster-meta-row">
          <span>Nodes: ${c.size}</span>
          <span>Fake Ratio: ${(c.fake_ratio * 100).toFixed(1)}%</span>
        </div>
        <div class="cluster-meta-row">
          <span>Mean Risk: ${(c.mean_risk_score * 100).toFixed(1)}%</span>
          <span>Fakes: ${c.fake_count}</span>
        </div>
      `;

      item.addEventListener('click', () => {
        document.querySelectorAll('.cluster-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        state.activeClusterId = c.cluster_id;
        loadClusterGraph(c.cluster_id);
      });

      clusterListContainer.appendChild(item);
    });

    // Auto-select first cluster if none selected
    if (res.clusters.length > 0 && !state.activeClusterId) {
      state.activeClusterId = res.clusters[0].cluster_id;
      clusterListContainer.children[0].classList.add('active');
      loadClusterGraph(state.activeClusterId);
    }

  } catch (err) {
    clusterListContainer.innerHTML = `<p style="color: var(--status-fake); padding: 16px;">Failed to load clusters: ${err.message}</p>`;
  }
}

async function loadClusterGraph(clusterId) {
  const container = document.getElementById('network-graph-container');
  container.innerHTML = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: var(--text-muted);">Rendering interactive force graph...</div>';

  try {
    const subgraph = await api.getClusterSubgraph(clusterId, 45);
    container.innerHTML = '';

    // vis.js dataset format
    const nodes = new vis.DataSet(subgraph.nodes.map(n => {
      const isFake = n.is_fake;
      return {
        id: n.id,
        label: `${n.id}`,
        title: `Node #${n.id}<br>Type: ${isFake ? 'Fake' : 'Genuine'}<br>Risk: ${(n.risk_score * 100).toFixed(1)}%<br>Degree: ${n.degree}`,
        color: {
          background: isFake ? '#f43f5e' : '#10b981',
          border: isFake ? '#be123c' : '#047857',
          highlight: { background: '#38bdf8', border: '#0284c7' }
        },
        size: Math.max(12, Math.min(26, 10 + n.degree / 4)),
        font: { color: '#f8fafc', size: 10 }
      };
    }));

    const edges = new vis.DataSet(subgraph.edges.map(e => ({
      from: e.source,
      to: e.target,
      color: { color: 'rgba(255, 255, 255, 0.15)', highlight: '#38bdf8' },
      width: 1
    })));

    const data = { nodes, edges };
    const options = {
      physics: {
        stabilization: false,
        barnesHut: { gravitationalConstant: -2000, springLength: 80 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true
      }
    };

    networkGraphInstance = new vis.Network(container, data, options);

  } catch (err) {
    container.innerHTML = `<div style="padding: 30px; color: var(--status-fake); text-align: center;">Graph render error: ${err.message}</div>`;
  }
}

// -------------------------------------------------------------
// PHASE F5 — DETECTION HISTORY VIEW
// -------------------------------------------------------------
async function loadHistoryView() {
  setupHistoryFilters();
  await fetchHistoryRecords();
}

function setupHistoryFilters() {
  const modeSelect = document.getElementById('history-filter-mode');
  const predSelect = document.getElementById('history-filter-pred');
  const clearBtn = document.getElementById('btn-clear-history');

  if (!modeSelect.dataset.bound) {
    modeSelect.dataset.bound = 'true';
    modeSelect.addEventListener('change', () => {
      state.historyFilters.mode = modeSelect.value;
      state.historyPage = 1;
      fetchHistoryRecords();
    });

    predSelect.addEventListener('change', () => {
      state.historyFilters.prediction = predSelect.value;
      state.historyPage = 1;
      fetchHistoryRecords();
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        if (confirm('Clear all recorded interactions from detection history?')) {
          await api.clearHistory();
          showToast('History cleared', 'info');
          fetchHistoryRecords();
        }
      });
    }
  }
}

async function fetchHistoryRecords() {
  const tbody = document.getElementById('history-table-body');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 30px;">Loading interaction history...</td></tr>';

  try {
    const params = {
      page: state.historyPage,
      page_size: 15
    };
    if (state.historyFilters.mode) params.mode = state.historyFilters.mode;
    if (state.historyFilters.prediction !== '') params.prediction = parseInt(state.historyFilters.prediction);

    const res = await api.getHistory(params);
    tbody.innerHTML = '';

    if (res.items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 30px; color: var(--text-muted);">No history records logged yet</td></tr>';
      return;
    }

    res.items.forEach(item => {
      const tr = document.createElement('tr');
      const isFake = (item.prediction === 1);
      const pillClass = isFake ? 'pill-fake' : 'pill-genuine';

      tr.innerHTML = `
        <td style="font-weight: 600; color: var(--text-main);">#${item.id}</td>
        <td>${item.node_id !== null ? `#${item.node_id}` : '<em style="color:var(--text-muted);">Simulated</em>'}</td>
        <td><span class="pill ${item.mode === 'simulate' ? 'pill-info' : 'pill-warning'}">${item.mode.toUpperCase()}</span></td>
        <td><span class="pill ${pillClass}">${item.prediction_label}</span></td>
        <td>${(item.risk_score * 100).toFixed(1)}%</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${item.timestamp}</td>
        <td style="font-size: 0.78rem; color: var(--text-secondary); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.details || '-'}</td>
      `;

      tbody.appendChild(tr);
    });

    // Pagination
    document.getElementById('history-pagination-info').innerText = `Page ${res.page} of ${res.total_pages} (${res.total} records)`;
    document.getElementById('btn-history-prev').disabled = (res.page <= 1);
    document.getElementById('btn-history-next').disabled = (res.page >= res.total_pages);

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px; color: var(--status-fake);">Error loading history: ${err.message}</td></tr>`;
  }
}

// Utility: Debounce input
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
