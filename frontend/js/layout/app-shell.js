// Logged-in frame: screen content + navigation (bottom bar on mobile, sidebar on desktop).
// Built once and kept while moving between Home and Histórico; only the content area changes.
import { api, ApiError } from '../core/api.js';
import { loadCurrentUser, resetAppState } from '../core/app-state.js';
import { createElement, html, on, renderInto } from '../core/dom.js';
import { EVENTS, listen } from '../core/events.js';
import { icon } from '../core/icons.js';
import { go, reload } from '../core/router.js';
import { session } from '../core/session.js';
import { avatar } from '../ui/avatar.js';
import { queueToasts, showToast } from '../ui/toast.js';
import { NAV_ITEMS } from './nav-items.js';

let shell = null; // { element, content, cleanup }

const soonAttrs = (item) => (item.soon ? html`aria-disabled="true"` : '');

const bottomNav = () => html`
  <nav class="bottom-nav only-mobile" aria-label="Navegação principal">
    ${NAV_ITEMS.map((item) => html`
      <button class="bottom-nav__item${item.soon ? ' is-soon' : ''}" type="button" data-nav="${item.id}" ${soonAttrs(item)}>
        ${icon(item.icon, 24)}
        <span>${item.short || item.label}</span>
        ${item.soon && html`<span class="soon-badge soon-badge--tiny">EM BREVE</span>`}
        ${item.badge && html`<span class="count-badge count-badge--tiny" data-count="${item.badge}" hidden></span>`}
      </button>`)}
  </nav>`;

const sidebar = (user) => html`
  <aside class="sidebar only-desktop">
    <div class="brand sidebar__brand">
      <div class="brand__logo" style="--size:40px">${icon('bolt', 22)}</div>
      <span class="brand__name">GYM <em>DUEL</em></span>
    </div>
    <nav class="sidebar__nav" aria-label="Navegação principal">
      ${NAV_ITEMS.map((item) => html`
        <button class="sidebar__item${item.soon ? ' is-soon' : ''}" type="button" data-nav="${item.id}" ${soonAttrs(item)}>
          ${icon(item.icon, 22)}${item.label}${item.soon && html`<span class="soon-badge">EM BREVE</span>`}
          ${item.badge && html`<span class="count-badge sidebar__count" data-count="${item.badge}" hidden></span>`}
        </button>`)}
    </nav>
    <div class="sidebar__user">
      <button class="sidebar__profile" type="button" data-nav="account" aria-label="Minha conta" title="Minha conta">
        <span data-bind="avatar">${avatar({ name: user.first_name, color: user.color, size: 38 })}</span>
        <span class="sidebar__who">
          <span class="sidebar__name" data-bind="name">${user.first_name}</span>
          <span class="sidebar__goal" data-bind="balance">Saldo: ${user.balance} pts</span>
        </span>
      </button>
      <button class="sidebar__logout" type="button" data-action="logout" aria-label="Sair" title="Sair">${icon('logout', 18)}</button>
    </div>
  </aside>`;

const shellView = (user) => html`
  <div class="app">
    ${sidebar(user)}
    <div class="app__body"><div class="app__content" id="screen"></div></div>
    ${bottomNav()}
  </div>`;

const loadErrorView = (message) => html`
  <div class="load-error">
    <p>${message}</p>
    <button class="btn btn--secondary" type="button" data-action="retry">Tentar de novo</button>
  </div>`;

/** Drop the shell and cached data, so the next screen is built for whoever is logged in. */
function leaveShell() {
  resetAppState();
  shell?.cleanup();
  shell = null;
}

export function logout() {
  session.clear();
  leaveShell();
  go('login');
}

/** Switch to another account saved on this device (no password needed). */
export function switchAccount(accountId) {
  if (!session.switchTo(accountId)) return;
  leaveShell();
  go('home');
}

/** Keep the current account saved and open the login to enter another one. */
export function addAccount() {
  session.park();
  leaveShell();
  go('login');
}

/** Reload the user (name, balance, goals) after something changed them. */
async function refreshUser() {
  const user = await api.me();
  session.setUser(user);
  const bind = (name) => shell?.element.querySelector(`[data-bind="${name}"]`);
  if (bind('balance')) bind('balance').textContent = `Saldo: ${user.balance} pts`;
  if (bind('name')) bind('name').textContent = user.first_name;
  if (bind('avatar')) renderInto(bind('avatar'), avatar({ name: user.first_name, color: user.color, size: 38 }));
}

/** Pink counters on the navigation (challenges waiting for an answer, rewards to fulfil). */
async function refreshBadges() {
  const counts = await api.badges();
  shell?.element.querySelectorAll('[data-count]').forEach((badge) => {
    const count = counts[badge.dataset.count] || 0;
    badge.hidden = count === 0;
    badge.textContent = count;
  });
}

/** Unread notifications become toasts, once. */
async function showNotifications() {
  const unread = await api.notifications();
  if (!unread.length) return;
  queueToasts(unread.map((notification) => notification.message));
  await api.markNotificationsRead();
}

function build(root, user) {
  const element = createElement(shellView(user));
  root.replaceChildren(element);
  on(element, 'click', '[data-nav]', (_, button) => {
    const item = NAV_ITEMS.find((entry) => entry.id === button.dataset.nav);
    if (item?.soon) showToast(item.soon);
    else go(button.dataset.nav); // nav items and the sidebar profile card ("account")
  });
  on(element, 'click', '[data-action="logout"]', logout);
  on(element, 'click', '[data-action="retry"]', reload);
  const refresh = () => {
    refreshUser().catch(() => {});
    refreshBadges().catch(() => {});
  };
  const cleanup = [EVENTS.workoutSaved, EVENTS.accountChanged].map((name) => listen(name, refresh));
  showNotifications().catch(() => {}); // a failure here must not block the app
  return { element, content: element.querySelector('#screen'), cleanup: () => cleanup.forEach((off) => off()) };
}

function setActive(id) {
  shell.element.querySelectorAll('[data-nav]').forEach((button) => {
    const active = button.dataset.nav === id;
    button.classList.toggle('is-active', active);
    if (active) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
}

/** Mount a logged-in screen inside the shell. Returns the screen's cleanup function. */
export async function showInShell(root, screenId, mountScreen) {
  let user;
  try {
    user = await loadCurrentUser();
  } catch (error) {
    if (!(error instanceof ApiError) || error.code === 'not_authenticated') return undefined;
    // No shell yet, so the retry button gets its own handler.
    shell = null;
    renderInto(root, loadErrorView(error.message));
    root.querySelector('[data-action="retry"]').addEventListener('click', reload);
    return undefined;
  }
  if (!shell || !root.contains(shell.element)) {
    shell?.cleanup();
    shell = build(root, user);
  }
  setActive(screenId);
  refreshBadges().catch(() => {});
  window.scrollTo(0, 0);
  try {
    return await mountScreen(shell.content);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.code !== 'not_authenticated') renderInto(shell.content, loadErrorView(error.message));
    return undefined;
  }
}
