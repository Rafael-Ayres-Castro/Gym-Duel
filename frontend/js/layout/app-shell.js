// Logged-in frame: screen content + navigation (bottom bar on mobile).
// Built once and kept while moving between Home and Histórico; only the content area changes.
import { resetAppState, loadCurrentUser } from '../core/app-state.js';
import { createElement, html, on } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { go } from '../core/router.js';
import { session } from '../core/session.js';
import { closeAccountMenu } from '../ui/account-menu.js';
import { showToast } from '../ui/toast.js';
import { NAV_ITEMS } from './nav-items.js';

let shell = null; // { element, content }

const bottomNav = () => html`
  <nav class="bottom-nav" aria-label="Navegação principal">
    ${NAV_ITEMS.map((item) => html`
      <button class="bottom-nav__item${item.soon ? ' is-soon' : ''}" type="button" data-nav="${item.id}"
        ${item.soon ? html`aria-disabled="true"` : ''}>
        ${icon(item.icon, 24)}
        <span>${item.label}</span>
        ${item.soon && html`<span class="soon-badge soon-badge--tiny">EM BREVE</span>`}
      </button>`)}
  </nav>`;

const shellView = () => html`
  <div class="app">
    <div class="app__body"><div class="app__content" id="screen"></div></div>
    ${bottomNav()}
  </div>`;

export function logout() {
  closeAccountMenu();
  session.clear();
  resetAppState();
  shell = null;
  go('login');
}

function build(root) {
  const element = createElement(shellView());
  root.replaceChildren(element);
  on(element, 'click', '[data-nav]', (_, button) => {
    const item = NAV_ITEMS.find((entry) => entry.id === button.dataset.nav);
    if (item.soon) showToast(item.soon);
    else go(item.id);
  });
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
  await loadCurrentUser();
  if (!shell || !root.contains(shell.element)) shell = build(root);
  closeAccountMenu();
  setActive(screenId);
  window.scrollTo(0, 0);
  return mountScreen(shell.content);
}
