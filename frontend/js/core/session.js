// Login session: the JWT lives in localStorage (valid for 30 days), the user object in memory.
import { readItem, writeItem } from './storage.js';

const TOKEN_KEY = 'gymduel.token';
const LAST_EMAIL_KEY = 'gymduel.lastEmail';

let currentUser = null;

export const session = {
  get token() { return readItem(TOKEN_KEY); },
  get user() { return currentUser; },
  get isLoggedIn() { return Boolean(this.token); },

  start({ access_token: token, user }) {
    writeItem(TOKEN_KEY, token);
    writeItem(LAST_EMAIL_KEY, user.email);
    currentUser = user;
  },
  setUser(user) { currentUser = user; },
  clear() {
    writeItem(TOKEN_KEY, null);
    currentUser = null;
  },

  /** Pre-fills the login form with the last e-mail used on this device. */
  get lastEmail() { return readItem(LAST_EMAIL_KEY) || ''; },
};
