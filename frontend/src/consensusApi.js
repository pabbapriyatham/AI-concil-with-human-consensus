const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

async function request(path, body) {
  const response = await fetch(`${BASE}/api/consensus${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = Array.isArray(error.detail) ? error.detail.map(e => e.msg).join('; ') : error.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export const consensusApi = {
  config: () => request('/config'),
  execute: body => request('/executions', body),
  review: (id, body) => request(`/knowledge/${encodeURIComponent(id)}/review`, body),
  history: id => request(`/knowledge/${encodeURIComponent(id)}/history`),
};
