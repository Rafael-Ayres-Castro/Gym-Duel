// Data shared by several screens. The scoreboard carries the server's "today" and week bounds,
// which every date label depends on, so it is kept here after each load.
import { api } from './api.js';
import { session } from './session.js';

let scoreboard = null;

export async function loadScoreboard() {
  scoreboard = await api.scoreboard();
  return scoreboard;
}

export const cachedScoreboard = () => scoreboard;
export function setScoreboard(value) { scoreboard = value; }

export async function loadCurrentUser() {
  if (!session.user) session.setUser(await api.me());
  return session.user;
}

export function resetAppState() { scoreboard = null; }
