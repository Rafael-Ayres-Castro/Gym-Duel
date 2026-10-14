// Logged-in frame: screen content + navigation (bottom bar on mobile, sidebar on desktop).
// Built once and kept while moving between Home and Histórico; only the content area changes.
import { ApiError } from '../core/api.js';
import { loadCurrentUser, resetAppState } from '../core/app-state.js';
import { createElement, html, on, renderInto } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { go, reload } from '../core/router.js';
import { session } from '../core/session.js';
import { closeAccountMenu } from '../ui/account-menu.js';
import { avatar } from '../ui/avatar.js';
import { showToast } from '../ui/toast.js';
import { NAV_ITEMS } from './nav-items.js';

let shell = null; // { element, content }

const soonAttrs = (item) => (item.soon ? html`aria-disabled="true"` : '');

const bottomNav = () => html`
  <nav class="bottom-nav only-mobile" aria-label="Navegação principal">
    ${NAV_ITEMS.map((item) => html`
      <button class="bottom-nav__item${item.soon ? ' is-soon' : ''}" type="button" data-nav="${item.id}" ${soonAttrs(item)}>
        ${icon(item.icon, 24)}
        <span>${item.label}</span>
        ${item.soon && html`<span class="soon-badge soon-badge--tiny">EM BREVE</span>`}
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
        </button>`)}
    </nav>
    <div class="sidebar__user">
      ${avatar({ name: user.first_name, color: user.color, size: 38 })}
      <div class="sidebar__who">
        <div class="sidebar__name-row">
          <span class="sidebar__name">${user.first_name}</span>
          <button class="sidebar__logout" type="button" data-action="logout" aria-label="Sair" title="Sair">${icon('logout', 18)}</button>
        </div>
        <span class="sidebar__goal">Meta: ${user.weekly_goal} treinos/semana</span>
      </div>
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

export function logout() {
  closeAccountMenu();
  session.clear();
  resetAppState();
  shell = null;
  go('login');
}

function build(root, user) {
  const element = createElement(shellView(user));
  root.replaceChildren(element);
  on(element, 'click', '[data-nav]', (_, button) => {
    const item = NAV_ITEMS.find((entry) => entry.id === button.dataset.nav);
    if (item.soon) showToast(item.soon);
    else go(item.id);
  });
  on(element, 'click', '[data-action="logout"]', logout);
  on(element, 'click', '[data-action="retry"]', reload);
  return { element, content: element.querySelector('#screen') };
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
  if (!shell || !root.contains(shell.element)) shell = build(root, user);
  closeAccountMenu();
  setActive(screenId);
  window.scrollTo(0, 0);
  try {
    return await mountScreen(shell.content);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.code !== 'not_authenticated') renderInto(shell.content, loadErrorView(error.message));
    return undefined;
  }
}
