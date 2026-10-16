// Entry point: wires routes, session expiry and starts the app.
import { initCheckin } from './checkin/checkin-modal.js';
import { setSessionExpiredHandler } from './core/api.js';
import { defineRoutes, startRouter } from './core/router.js';
import { session } from './core/session.js';
import { initShortcuts } from './core/shortcuts.js';
import { logout, showInShell } from './layout/app-shell.js';
import { initPhotoViewer } from './ui/photo-viewer.js';
import * as history from './screens/history/history.js';
import * as home from './screens/home/home.js';
import * as goals from './screens/goals/goals.js';
import * as rewards from './screens/rewards/rewards.js';
import * as login from './screens/auth/login.js';
import * as signup from './screens/auth/signup.js';

const root = document.getElementById('app');

const requireLogin = () => (session.isLoggedIn ? null : 'login');
const guestsOnly = () => (session.isLoggedIn ? 'home' : null);

defineRoutes(
  {
    login: { guard: guestsOnly, mount: () => login.mount(root) },
    signup: { guard: guestsOnly, mount: () => signup.mount(root) },
    home: { guard: requireLogin, mount: () => showInShell(root, 'home', home.mount) },
    history: { guard: requireLogin, mount: () => showInShell(root, 'history', history.mount) },
    rewards: { guard: requireLogin, mount: () => showInShell(root, 'rewards', rewards.mount) },
    goals: { guard: requireLogin, mount: () => showInShell(root, 'goals', goals.mount) },
  },
  () => (session.isLoggedIn ? 'home' : 'login'),
);

setSessionExpiredHandler(logout);
initCheckin();
initShortcuts();
initPhotoViewer();

startRouter();
