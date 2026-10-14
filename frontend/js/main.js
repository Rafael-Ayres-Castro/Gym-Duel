// Entry point: wires routes, session expiry and starts the app.
import { setSessionExpiredHandler } from './core/api.js';
import { defineRoutes, go, startRouter } from './core/router.js';
import { session } from './core/session.js';
import * as home from './screens/home.js';
import * as login from './screens/auth/login.js';
import * as signup from './screens/auth/signup.js';

const root = document.getElementById('app');

const requireLogin = () => (session.isLoggedIn ? null : 'login');
const guestsOnly = () => (session.isLoggedIn ? 'home' : null);

defineRoutes(
  {
    login: { guard: guestsOnly, mount: () => login.mount(root) },
    signup: { guard: guestsOnly, mount: () => signup.mount(root) },
    home: { guard: requireLogin, mount: () => home.mount(root) },
  },
  () => (session.isLoggedIn ? 'home' : 'login'),
);

setSessionExpiredHandler(() => {
  session.clear();
  go('login');
});

startRouter();
