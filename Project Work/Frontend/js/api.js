/**
 * Innovexa API Client Module
 * Provides unified HTTP service methods with loading indicators and error handling.
 */

const API_BASE = 'http://127.0.0.1:8000/api';

const api = {
  async get(endpoint, params = {}) {
    const url = new URL(`${API_BASE}${endpoint}`);
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        url.searchParams.append(k, params[k]);
      }
    });

    try {
      const response = await fetch(url.toString());
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API GET ${endpoint} error:`, err);
      throw err;
    }
  },

  async post(endpoint, data = {}) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API POST ${endpoint} error:`, err);
      throw err;
    }
  },

  async delete(endpoint) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API DELETE ${endpoint} error:`, err);
      throw err;
    }
  },

  // Specialized Endpoints
  getDashboardSummary() {
    return this.get('/dashboard/summary');
  },

  getProfiles(params) {
    return this.get('/profiles', params);
  },

  getProfileDetails(nodeId) {
    return this.get(`/profiles/${nodeId}`);
  },

  getFeatureCategories() {
    return this.get('/profiles/categories');
  },

  predictBrowse(nodeId) {
    return this.post(`/predict/browse/${nodeId}`);
  },

  predictSimulate(payload) {
    return this.post('/predict/simulate', payload);
  },

  getClusters(params) {
    return this.get('/network/clusters', params);
  },

  getClusterSubgraph(clusterId, maxNodes = 40) {
    return this.get(`/network/cluster/${clusterId}/subgraph`, { max_nodes: maxNodes });
  },

  getNodeSubgraph(nodeId, maxNeighbors = 20) {
    return this.get(`/network/node/${nodeId}/subgraph`, { max_neighbors: maxNeighbors });
  },

  getHistory(params) {
    return this.get('/history', params);
  },

  clearHistory() {
    return this.delete('/history/clear');
  }
};

// Global Toast Notification Helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : type === 'error' ? '⚠️' : 'ℹ️'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
