// DocuMatch Centralized API Client
// Supports pointing to persistent FastAPI backend via VITE_API_BASE_URL or VITE_API_URL
// Automatically attaches Reviewer Authentication headers for secure operations

export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  ''
).replace(/\/$/, '');

// Default reviewer development key used when no Supabase Auth session token is explicitly stored
export const DEFAULT_REVIEWER_KEY = 'documatch-reviewer-dev-key-2026';

export function getReviewerToken() {
  try {
    return localStorage.getItem('documatch_reviewer_token') || DEFAULT_REVIEWER_KEY;
  } catch {
    return DEFAULT_REVIEWER_KEY;
  }
}

export function setReviewerToken(token) {
  try {
    localStorage.setItem('documatch_reviewer_token', token);
  } catch (e) {
    console.warn('Unable to persist reviewer token:', e);
  }
}

export function apiUrl(path) {
  if (!path.startsWith('/')) {
    path = '/' + path;
  }
  return `${API_BASE}${path}`;
}

export async function apiFetch(path, options = {}) {
  const url = apiUrl(path);
  const token = getReviewerToken();
  const headers = {
    ...(options.headers || {}),
    'Authorization': `Bearer ${token}`,
    'X-Reviewer-Key': token,
  };
  return fetch(url, { ...options, headers });
}
