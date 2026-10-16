// Thin fetch wrapper for the /api endpoints. Every error becomes an ApiError with a pt-BR message.
import { session } from './session.js';

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let onSessionExpired = () => {};
/** Called when the server says the token is no longer valid (main.js sends the user to login). */
export function setSessionExpiredHandler(handler) { onSessionExpired = handler; }

async function request(method, path, { body, query } = {}) {
  const url = new URL(`/api${path}`, window.location.origin);
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value != null) url.searchParams.set(key, value);
  });

  const isForm = body instanceof FormData; // uploads: the browser sets the multipart boundary itself
  const headers = {};
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json';
  if (session.token) headers.Authorization = `Bearer ${session.token}`;

  let response;
  try {
    const payload = body === undefined || isForm ? body : JSON.stringify(body);
    response = await fetch(url, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, 'network', 'Sem conexão com o servidor. Confira a internet e tente de novo.');
  }
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === 'object' ? data.detail : {};
    const error = new ApiError(response.status, detail.code || 'error', detail.message || 'Algo deu errado. Tente de novo.');
    if (error.code === 'not_authenticated') onSessionExpired();
    throw error;
  }
  return data;
}

export const api = {
  register: (data) => request('POST', '/auth/register', { body: data }),
  login: (email, password) => request('POST', '/auth/login', { body: { email, password } }),
  me: () => request('GET', '/me'),
  scoreboard: () => request('GET', '/scoreboard'),
  summary: (period) => request('GET', '/summary', { query: { period } }),
  workouts: ({ person = 'all', period = 'week', limit } = {}) => request('GET', '/workouts', { query: { person, period, limit } }),
  checkin: (workout) => request('POST', '/workouts', { body: workout }),
  deleteWorkout: (id) => request('DELETE', `/workouts/${id}`),
  updateMe: (data) => request('PATCH', '/me', { body: data }),
  uploadPhoto: (workoutId, blob) => {
    const form = new FormData();
    form.append('photo', blob, 'treino.jpg');
    return request('POST', `/workouts/${workoutId}/photo`, { body: form });
  },
  cheer: (workoutId) => request('POST', `/workouts/${workoutId}/cheer`),
  rules: () => request('GET', '/rules'),
  proposeRules: (values) => request('POST', '/rules/proposals', { body: values }),
  approveRules: (id) => request('POST', `/rules/proposals/${id}/approve`),
  rejectRules: (id) => request('POST', `/rules/proposals/${id}/reject`),
  cancelRules: (id) => request('DELETE', `/rules/proposals/${id}`),
  streaks: () => request('GET', '/streaks'),
  notifications: () => request('GET', '/notifications'),
  markNotificationsRead: () => request('POST', '/notifications/read'),
};
