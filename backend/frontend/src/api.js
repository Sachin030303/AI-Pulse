const API_ROOT = '/api/v1';
const TOKEN_KEY = 'ai-pulse-session';

export function getSavedToken() {
  try { return sessionStorage.getItem(TOKEN_KEY) || ''; }
  catch { return ''; }
}

export function saveToken(value) {
  try {
    if (value) sessionStorage.setItem(TOKEN_KEY, value);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch { /* Browsers can block sessionStorage. */ }
}

export class ApiError extends Error {
  constructor(message, status) { super(message); this.name = 'ApiError'; this.status = status; }
}

export async function apiRequest(path, { token = '', method = 'GET', body, params, signal } = {}) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
  });
  const url = `${API_ROOT}${path}${query.size ? `?${query}` : ''}`;
  let response;
  try {
    response = await fetch(url, {
      method,
      signal,
      credentials: 'omit',
      cache: 'no-store',
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach AI-Pulse API. Check FastAPI on port 8000.', 0);
  }
  const json = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = json?.detail;
    const message = typeof detail === 'string' ? detail :
      Array.isArray(detail) ? detail.map((item) => item.msg).filter(Boolean).join('; ') :
      `Request failed (HTTP ${response.status})`;
    throw new ApiError(message, response.status);
  }
  return json;
}
