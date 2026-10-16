// Login session: the JWT lives in localStorage (valid for 30 days), the user object in memory.
//
// Every account that logs in on this device is also kept in a small list (token + name, e-mail
// and color), so "Trocar de conta" switches without typing the password again. "Sair" removes
// the account from the list; "Entrar com outra conta" keeps it there.
import { readItem, writeItem } from './storage.js';

const TOKEN_KEY = 'gymduel.token';
const LAST_EMAIL_KEY = 'gymduel.lastEmail';
const ACCOUNTS_KEY = 'gymduel.accounts';

let currentUser = null;

function readAccounts() {
  try {
    const list = JSON.parse(readItem(ACCOUNTS_KEY) || '[]');
    return Array.isArray(list) ? list : [];
  } catch {
    return []; // corrupted value: start over rather than break the login
  }
}

const writeAccounts = (list) => writeItem(ACCOUNTS_KEY, list.length ? JSON.stringify(list) : null);

/** Add or refresh the saved entry of `user` (keeps name and e-mail up to date after edits). */
function remember(user, token) {
  const entry = { id: user.id, firstName: user.first_name, email: user.email, color: user.color, token };
  writeAccounts([entry, ...readAccounts().filter((account) => account.id !== user.id)]);
}

export const session = {
  get token() { return readItem(TOKEN_KEY); },
  get user() { return currentUser; },
  get isLoggedIn() { return Boolean(this.token); },

  start({ access_token: token, user }) {
    writeItem(TOKEN_KEY, token);
    writeItem(LAST_EMAIL_KEY, user.email);
    currentUser = user;
    remember(user, token);
  },
  setUser(user) {
    currentUser = user;
    if (!this.token) return;
    remember(user, this.token);
    writeItem(LAST_EMAIL_KEY, user.email); // follows an e-mail change made in "Minha conta"
  },

  /** "Sair": forget the account in use on this device. */
  clear() {
    const token = this.token;
    writeAccounts(readAccounts().filter((account) => account.token !== token));
    writeItem(TOKEN_KEY, null);
    currentUser = null;
  },

  /** "Entrar com outra conta": leave the current account saved and go to an empty login. */
  park() {
    writeItem(TOKEN_KEY, null);
    currentUser = null;
  },

  /** Saved accounts other than the one in use (all of them when nobody is logged in). */
  get otherAccounts() {
    const token = this.token;
    return readAccounts().filter((account) => account.token !== token);
  },

  /** Make a saved account the current one. The user object is reloaded by the next screen. */
  switchTo(accountId) {
    const account = readAccounts().find((entry) => entry.id === accountId);
    if (!account) return false;
    writeItem(TOKEN_KEY, account.token);
    writeItem(LAST_EMAIL_KEY, account.email); // if its token expired, the login comes pre-filled
    currentUser = null;
    return true;
  },

  /** Pre-fills the login form with the last e-mail used on this device. */
  get lastEmail() { return readItem(LAST_EMAIL_KEY) || ''; },
};
